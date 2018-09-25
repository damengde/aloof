# -*- coding: utf-8 -*

import os
import re
import logging
import xml.etree.ElementTree as ET
import utils.image_downloader as downloader
from os.path import join, dirname
from prettytable import PrettyTable
from collections import Counter
from gensim.models.keyedvectors import KeyedVectors
from utils.utils import load_json, save_json, load_file, save_file, map_wn31wn30, map_wn30lemma, map_wn31db, create_uri, map_netlemma
from verbalize import verbalize_frame
from ntriples_reader import read_folder_frames
from prototypical_frame import find_prototypical_instances

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

class Validator_By_Core:
    '''
    Class that implements a frame validator according to the priority of its frame elements
    '''

    def __init__(self, annotations_path, threshold=0.75):
        self.__annotations = self.get_frametype_annotations(annotations_path)
        self.__threshold = threshold

    def get_frametype_annotations(self, frame_types_path):
        ''' Load the annotations of frame types '''
        ft_annotations = {}

        for file_name in os.listdir(frame_types_path):
            file_path = os.path.join(frame_types_path, file_name)
            xml = ET.parse(file_path)
            frame_type =  file_name[:-4].lower()
            ft_annotations[frame_type] = []
            for element in xml.findall('.//{http://framenet.icsi.berkeley.edu}FE'):
                if element.get('coreType') == 'Core' or element.get('coreType') == 'Core-Unexpressed':
                    ft_annotations[frame_type].append(element.get('name').lower())

        return ft_annotations

    def is_valid(self, frame_type, frame_elements):
        ''' Verify if a frame instance has the majority of core frame elements '''
        frame_element_cores = self.__annotations[frame_type]
        total = float(len(frame_element_cores))
        cont = sum([1 for x in frame_elements.keys() if x in frame_element_cores])

        if total == 0:#just 5 cases without core elements
            return False
        elif cont / total >= self.__threshold:
            return True
        else:
            return False


class Validator_By_Synset:
    '''
    Class that implements a frame validator according to the synsets of its frame elements
    '''

    def __init__(self, annotations_path):
        self.__annotations = self.get_frameelement_annotations(annotations_path)
        self.__wn31wn30 = map_wn31wn30()

    def get_frameelement_annotations(self, frame_elements_path):
        ''' Load the annotations of frame elements '''
        fe_annotations = {}

        for file_name in os.listdir(frame_elements_path):
            file_path = os.path.join(frame_elements_path, file_name)
            frame_type, frame_element = file_name[:-4].lower().split('---')
            if frame_type not in fe_annotations: fe_annotations[frame_type] = {}
            fe_annotations[frame_type][frame_element] = []

            with open(file_path, 'r') as file_input:
                data_lines = file_input.readlines()
            for data in data_lines:
                synset, frequency, weight = data.strip().split(',')
                result = re.match('(.+)_(\d+)', synset)
                fe_annotations[frame_type][frame_element].append({'lemma':result.group(1), 'synset_id':result.group(2)[1:], 'frequency':frequency, 'weight':weight})

        return fe_annotations

    def is_valid(self, frame_type, frame_elements):
        ''' Verify if a frame instance has at least one annotated synset in its frame elements '''
        frame_elements = {x:self.__wn31wn30[frame_elements[x]][:-2] for x in frame_elements}
        frame_element_synsets = {}

        if frame_type in self.__annotations:
            for fe in self.__annotations[frame_type]:
                frame_element_synsets[fe] = {x['synset_id'] for x in self.__annotations[frame_type][fe]} 

        cont = 0
        for fe in frame_elements:
            if fe in frame_element_synsets and frame_elements[fe] in frame_element_synsets[fe]:
                cont += 1

        if cont > 0:
            return True
        else:
            return False

class Validator_By_Embeddings:
    '''
    Class that implements a frame validator according to the similarity between frame elements and its values (words)
    '''

    def __init__(self, model_path):
        self.__model = KeyedVectors.load_word2vec_format(model_path, binary=True)
        self.__wn31wn30 = map_wn31wn30()
        self.__wn30lemma = map_wn30lemma()

    def is_valid(self, frame_type, frame_elements):
        ''' Verify if a frame instance has strong similarity in its frame elements '''
        frame_elements = {x:self.__wn30lemma[self.__wn31wn30[frame_elements[x]]] for x in frame_elements}
        total = float(len(frame_elements))
        similarity = 0

        for role, filler in frame_elements.items():
            if role in self.__model.vocab and filler in self.__model.vocab:
                similarity += self.__model.similarity(role, filler)
            else:
                total -= 1

        if total == 0: # all roles and fillers are not present in the embeddings
            return True

        if similarity / total > 0.7:
            return True

        return False


def create_dataset(option, frame_raw_path, frame_parsed_path):
    ''' Create a dataset of frame triples according to a Validator (by core, by synset or by embeddings) '''
    obj_validator = None
    if option == 'core':
        frame_types_path = join(dirname(__file__), '../../resource/frames/annotations_frame_types/')
        obj_validator = Validator_By_Core(frame_types_path)
    elif option == 'synset':
        frame_elements_path = join(dirname(__file__), '../../resource/frames/annotations_frame_elements/')
        obj_validator = Validator_By_Synset(frame_elements_path)
    elif option == 'embeddings':
        embeddings_path = join(dirname(__file__), '../../resource/embeddings/googlenews_negative300')
        obj_validator = Validator_By_Embeddings(embeddings_path)
    else:
        logging.error('Unknown "%s" option of frame validator' % option)

    if obj_validator:
        frame_instances = read_folder_frames(frame_raw_path, delete_repetition=False)
        filtered_frames = filter_instances(frame_instances, obj_validator)
        prototypical_frames = find_prototypical_instances(filtered_frames)

        save_json(prototypical_frames, join(frame_parsed_path, 'frame_instances.json'))
        logging.info('Selected %s prototypical frames' % len(prototypical_frames))

def filter_instances(frame_instances, obj_validator):
    ''' Filter out frame instances according to a Validator '''
    filtered_frames = {}
   
    for frame_id in frame_instances.keys():
        frame = frame_instances[frame_id]
        frame_type = frame.frame_type
        frame_elements = {x.role.lower():x.entity.split('/')[-1][:-1] for x in frame.frame_elements}
        if obj_validator.is_valid(frame_type.lower(), frame_elements):
            if frame_type not in filtered_frames:
                filtered_frames[frame_type] = {}
            filtered_frames[frame_type][frame_id] = frame

    return filtered_frames

def select_relations(frame_parsed_path, house_objects_path):
    ''' Select unique relations of frames about house's object '''
    house_objects = {v.replace(' ', '_'):k['dbpedia_uri'] for v,k in load_json(house_objects_path).items()}
    house_object_uris = set(house_objects.values())
    house_object_names = set(house_objects.keys())
    frame_instances = load_json(join(frame_parsed_path, 'frame_instances.json'))
    netlemma = map_netlemma()
    wn31db = map_wn31db()
    triple_uris = []
    triple_labels = []   

    for frame_id in frame_instances.keys():
        valid_frame = False
        frame = frame_instances[frame_id]
        frame_uris, frame_labels = create_triples(frame['type'], frame['elements'], wn31db, netlemma)
        for i in range(len(frame_uris)):
            object_uri = re.match('<(.+)> <(.+)> <(.+)>', frame_uris[i]).group(1)
            if object_uri in house_object_uris and frame_uris[i] not in triple_uris:
                triple_uris.append(frame_uris[i])
                triple_labels.append(frame_labels[i])
                valid_frame = True
            else:
                object_name = re.match('<(.+)> <(.+)> <(.+)>', frame_labels[i]).group(1)
                if object_name in house_object_names and frame_uris[i] not in triple_uris:
                    triple_uris.append(frame_uris[i])
                    triple_labels.append(frame_labels[i])
                    valid_frame = True
        
        if not valid_frame:
            del frame_instances[frame_id]

    calculate_statistics(triple_uris, frame_parsed_path)
    save_file(join(frame_parsed_path, 'selected_triples.nt'), triple_uris)
    save_file(join(frame_parsed_path, 'selected_triples_label.nt'), triple_labels)
    save_file(join(frame_parsed_path, 'selected_verbalized.txt'), [verbalize_frame(f['type'], f['elements'].items(), netlemma) for f in frame_instances.values()])
    logging.info('Total valid relations with URIs: %s' % len(triple_uris))

def create_triples(frame_type, frame_elements, wn31db, netlemma):
    ''' Create RDF triples from frame instance '''
    triple_uris = []
    triple_labels = []
    
    for role, filler in frame_elements.items():
        if filler in wn31db: # only frame elements with mappings
            triple_labels.append('<%s> <%s> <%s>' % (netlemma[filler], role+'Of', frame_type.lower()))
            triple_uris.append('<%s> <%s> <%s>' % (create_uri(wn31db[filler]), 'http://framebase.org/fe/%s' % role.title() +'Of', 'http://framebase.org/frame/%s' % frame_type))

    return triple_uris, triple_labels

def calculate_statistics(object_relations, output_path):
    ''' Calculate statistics of the dataset '''
    ftype_counter = set()
    felement_counter = set()
    ffiller_counter = set()

    for triple in object_relations:
        ffiller, felement, ftype = re.match('<(.+)> <(.+)> <(.+)>', triple).groups()
        ftype_counter.add(ftype)
        felement_counter.add(felement)
        ffiller_counter.add(ffiller)

    table = PrettyTable()
    table.field_names = ['Item', 'Amount']
    table.align['Item'] = 'l'
    table.align['Amount'] = 'r'
    table.add_row(['Frame types', len(ftype_counter)])
    table.add_row(['Frame elements', len(felement_counter)])
    table.add_row(['Frame elements fillers', len(ffiller_counter)])
    table.add_row(['Relations', len(object_relations)])

    print(table)
    save_file(join(output_path,'statistics_dataset.txt'), [table.get_string()])

def download_images(triples_path, images_path):
    ''' Download images for the 'object' component in RDF triples '''
    urls = set()

    with open(join(triples_path, 'selected_triples.nt'), 'r') as fin:
        for line in fin:
            result = re.match('<(.+)> <.+> <(.+)>', line.rstrip())
            urls.add(result.group(1))

    downloader.download_images(urls, images_path)