# -*- coding: utf-8 -*-

import os
import re
import logging
import utils.image_downloader as downloader
from os.path import join
from prettytable import PrettyTable
from api import collect_relations, get_uri
from utils.utils import load_json, save_file, map_wn31db, create_uri

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

def create_dataset(conceptnet_raw_path, house_objects_path, relations_path):
    ''' Create a dataset of objects and their relations from Conceptnet '''
    objects = load_json(house_objects_path).keys()
    objects = [x.replace(' ', '_') for x in objects]
    relations = [line.rstrip() for line in open(relations_path)]
    collect_relations(objects, relations, conceptnet_raw_path, 7)

def select_relations(conceptnet_raw_path, concepnet_parsed_path, house_objects_path):#
    ''' Select some relations from Conceptnet JSON files '''
    validated_relations = validate_relations(conceptnet_raw_path)
    wn31db = map_wn31db()
    relations_with_uris = []
    objects_with_uris = {v.replace(' ', '_'):k['dbpedia_uri'] for v,k in load_json(house_objects_path).items()}
    triple_labels = []
    triple_uris = []

    for object1, relation, object2 in validated_relations:
        if object2 not in objects_with_uris:
            objects_with_uris[object2] = to_dbpedia(get_uri('/c/en/'+object2, 10), wn31db)

    for object1, relation, object2 in validated_relations:
        if objects_with_uris[object2]:# object2 must to have an URI (by default object1 has an URI)
            relation_uri = 'http://ns.inria.fr/deko/ontology/deko.owl#' + relation
            relations_with_uris.append((objects_with_uris[object1], relation, objects_with_uris[object2]))
            triple_uris.append('<%s> <%s> <%s>' % (objects_with_uris[object1], relation_uri, objects_with_uris[object2]))
            triple_labels.append('<%s> <%s> <%s>' % (object1, relation, object2))

    calculate_statistics(relations_with_uris, concepnet_parsed_path)
    save_file(join(concepnet_parsed_path, 'selected_triples.nt'), triple_uris)
    save_file(join(concepnet_parsed_path, 'selected_triples_label.nt'), triple_labels)
    logging.info('Total valid relations with URIs: %s' % len(relations_with_uris))

def validate_relations(concepnet_path):
    ''' Validate if the searched objects are the subjects in the relation '''
    validated_relations = []

    for file_name in os.listdir(concepnet_path):
        data = load_json(join(concepnet_path, file_name))
        result = re.match('.+node=(.+)&.+', data['@id'])
        if result:
            object_id = result.group(1)
        else:
            object_id = None

        for element in data['edges']:
            if object_id == element['start']['@id']:
                object1 = element['start']['@id'].split('/')[-1]
                object2 = element['end']['@id'].split('/')[-1]
                relation = element['rel']['@id'].split('/')[-1]
                validated_relations.append((object1, relation, object2))

    return validated_relations

def to_dbpedia(uri, wn31db):
    ''' Create a URI to DBpedia or BabelNet '''
    if uri: # Not None
        if uri.startswith('http://wordnet-rdf'):
            id_wn = uri.split('/')[-1][1:]
            if id_wn in wn31db:
                return create_uri(wn31db[id_wn])
            else:
                return None

    return uri

def calculate_statistics(object_relations, concepnet_parsed_path):
    ''' Calculate statistics of the dataset '''
    relation_counter = {}
    object_counter = set()

    for object1, relation, object2 in object_relations:
        if relation not in relation_counter:
            relation_counter[relation] = 0
        relation_counter[relation] += 1
        object_counter.add(object1)
        object_counter.add(object2)

    table = PrettyTable()
    table.field_names = ['Item', 'Amount']
    table.align['Item'] = 'l'
    table.align['Amount'] = 'r'
    table.add_row(['Objects', len(object_counter)])
    table.add_row(['Relations (object-object)', sum(relation_counter.values())])

    for relation in relation_counter.keys():
        table.add_row(['Relation "%s"' % relation, relation_counter[relation]])

    print(table)
    save_file(join(concepnet_parsed_path,'statistics_dataset.txt'), [table.get_string()])

def download_images(triples_path, images_path):
    ''' Download images for the 'object' component in RDF triples '''
    urls = set()

    with open(join(triples_path, 'selected_triples.nt'), 'r') as fin:
        for line in fin:
            result = re.match('<(.+)> <.+> <(.+)>', line.rstrip())
            urls.add(result.group(2))

    downloader.download_images(urls, images_path)