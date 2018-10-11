# -*- coding: utf-8 -*-

import re
import logging
import utils.image_downloader as downloader
from os.path import join
from collections import Counter
from prettytable import PrettyTable
from utils.utils import save_json, load_json, save_file, map_lemmadb, create_uri
from attributetype_indentificator import classification, clustering

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

def create_dataset(visualgenome_raw_path, visualgenome_parsed_path):
    ''' Create a dataset of objects and their attributes using VisualGenome dataset '''
    visualgenome_data = load_json(join(visualgenome_raw_path, 'attributes.json'))
    attribute_synsets = load_json(join(visualgenome_raw_path, 'attribute_synsets.json'))
    frequency_data = {}

    for image in visualgenome_data:
        objects = set()
        for attribute_data in image['attributes']:
            if 'attributes' in attribute_data and len(set(attribute_data['synsets'])) == 1:
                object_name = attribute_data['synsets'][0]
                assigned = assign_attribute(object_name, attribute_data['attributes'], attribute_synsets, frequency_data)
                if assigned and object_name not in objects:
                    objects.add(object_name)
                    frequency_data[object_name]['images'] += 1

    logging.info('Size: %s objects selected' % len(frequency_data))
    save_json(frequency_data, join(visualgenome_parsed_path,'attribute_frequencies.json'))
    
def assign_attribute(object_name, attributes, attribute_synsets, frequency_data):
    ''' Assign attributes to synsets counting its frequency '''
    assigned = False
    if object_name not in frequency_data:
        frequency_data[object_name] = {'attributes':{}, 'images':0}
    for attribute in attributes:
        attribute = attribute.strip().lower()
        if attribute in attribute_synsets:
            att_synset = attribute_synsets[attribute]
            frequency_data[object_name]['attributes'][att_synset] = frequency_data[object_name]['attributes'].get(att_synset, 0) + 1
            assigned = True

    if len(frequency_data[object_name]['attributes']) == 0:
        del frequency_data[object_name]

    return assigned

def select_relations(visualgenome_path, house_objects_path, model_path):
    ''' Select relations about how often attributes belong to objects of house domain '''
    attribute_frequency = load_json(join(visualgenome_path, 'attribute_frequencies.json'))
    groups = classification(attribute_frequency.values(), model_path)
    save_json(groups, join(visualgenome_path, 'attribute_classes.json'))
    if 'others' in groups: del groups['others']
    attribute_knowledge, relations = extract_knowledge(attribute_frequency, groups)
    house_objects = {v.replace(' ', '_'):k['dbpedia_uri'] for v,k in load_json(house_objects_path).items()}
    save_json(attribute_knowledge, join(visualgenome_path,'attribute_knowledge.json'))
    create_triples(relations, house_objects, visualgenome_path)

def extract_knowledge(attribute_frequency, groups):
    ''' Extract knowledge about how often attributes belong to objects '''
    attribute_knowledge= {}
    relations = []

    for obj in attribute_frequency.keys():
        if attribute_frequency[obj]['images'] > 1:
            categories = {'usually':{}, 'sometimes':{}, 'rarely':{}}
            has_elements =  False
            for class_name in groups.keys():
                attributes_inclass = get_attributes_inclass(attribute_frequency[obj]['attributes'], groups[class_name])
                total = float(sum(attributes_inclass.values()))
                for attribute in attributes_inclass.keys():
                    ratio = round(attributes_inclass[attribute]/total, 2)
                    
                    if ratio >= 0.70:
                        if class_name not in categories['usually']: categories['usually'][class_name] = []
                        categories['usually'][class_name].append(attribute)
                        relations.append((obj, 'usuallyOf%s'%class_name.title(), attribute))
                        has_elements =  True
                    elif ratio >= 0.20:
                        if class_name not in categories['sometimes']: categories['sometimes'][class_name] = []
                        categories['sometimes'][class_name].append(attribute)
                        relations.append((obj, 'sometimesOf%s'%class_name.title(), attribute))
                        has_elements =  True
                    elif ratio >= 0.05:
                        if class_name not in categories['rarely']: categories['rarely'][class_name] = []
                        categories['rarely'][class_name].append(attribute)
                        relations.append((obj, 'rarelyOf%s'%class_name.title(), attribute))
                        has_elements =  True
                
            if has_elements:
                attribute_knowledge[obj] = categories

    return attribute_knowledge, relations

def get_attributes_inclass(all_attributes, classified_attributes):
    ''' Get the attributes that belongs to a specific class '''
    attributes = {}

    for attribute in all_attributes.keys():
        if attribute in classified_attributes:
            attributes[attribute] = all_attributes[attribute]

    return attributes

def create_triples(relations, house_objects, visualgenome_path):
    ''' Create RDF triples of the relations in two formats: labels and URIs '''
    house_object_uris = set(house_objects.values())
    house_object_names = set(house_objects.keys())
    lemmadb = map_lemmadb(lowercase=True)
    relations_with_uris = []
    triple_labels = []
    triple_uris = []

    for object_name, category, attribute in relations:
        if object_name in lemmadb and attribute in lemmadb: # objects and attributes must to have URIs
            object_uri = create_uri(lemmadb[object_name])
            object_name = object_name.split('.')[0]
            if object_uri in house_object_uris or object_name in house_object_names:            
                relations_with_uris.append((object_name, category, attribute))
                triple_labels.append('<%s> <%s> <%s>' % (object_name, category, attribute.split('.')[0]))
                category_uri = 'http://ns.inria.fr/deko/ontology/deko.owl#' + category
                triple_uris.append('<%s> <%s> <%s>' % (object_uri, category_uri, create_uri(lemmadb[attribute])))

    calculate_statistics(relations_with_uris, visualgenome_path)
    save_file(join(visualgenome_path, 'selected_triples.nt'), triple_uris)
    save_file(join(visualgenome_path, 'selected_triples_label.nt'), triple_labels)
    logging.info('Total valid relations with URIs: %s' % len(relations_with_uris))    

def calculate_statistics(object_relations, visualgenome_path):
    ''' Calculate statistics of the dataset '''
    category_counter = {}
    object_counter = set()
    attribute_counter = []

    for object, category, attributte in object_relations:
        if category not in category_counter:
            category_counter[category] = 0
        category_counter[category] += 1
        object_counter.add(object)
        attribute_counter.append(attributte)

    table = PrettyTable()
    table.field_names = ['Item', 'Amount']
    table.align['Item'] = 'l'
    table.align['Amount'] = 'r'
    total_objects = len(object_counter)
    table.add_row(['Objects', total_objects])
    table.add_row(['Attributes', len(set(attribute_counter))])
    table.add_row(['Relations (object-attribute)', len(object_relations)])
    total_objects = float(total_objects)

    for category in sorted(category_counter.keys()):
        table.add_row(['Relations "%s"' % category, category_counter[category]])

    table.add_row(['Avg. attributes by object', round(len(attribute_counter)/total_objects, 2)])

    for category in sorted(category_counter.keys()):
        table.add_row(['Avg. relations "%s" by object' % category, round(category_counter[category]/total_objects, 2)])

    print(table)
    save_file(join(visualgenome_path,'statistics_dataset.txt'), [table.get_string()])

    table.clear_rows()
    table.field_names = ['Attribute', 'Frequency']
    for attribute, frequency in sorted(Counter(attribute_counter).items(), key=lambda x:x[1], reverse=True):
        table.add_row([attribute, frequency])

    save_file(join(visualgenome_path,'statistics_attributes.txt'), [table.get_string()])

def download_images(triples_path, images_path):
    ''' Download images for the 'object' component in RDF triples '''
    urls = set()

    with open(join(triples_path, 'selected_triples.nt'), 'r') as fin:
        for line in fin:
            result = re.match('<(.+)> <.+> <(.+)>', line.rstrip())
            urls.add(result.group(2))

    downloader.download_images(urls, images_path)