# -*- coding: utf-8 -*-

import time
import logging
import requests
from os.path import join
from utils.utils import save_json

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

def collect_relations(objects, relations, conceptnet_path, delay=3):
    ''' Collect relations for a list of objects '''
    for obj in objects:
        for relation in relations:
            logging.debug('Extracting relation: %s %s' % (obj, relation))
            get_relations(obj, relation, conceptnet_path)
            time.sleep(delay)

def get_relations(object_name, relation, conceptnet_path, limit=100):
    ''' Get relations of an object throught Conceptnet RESTful API '''
    base_query = 'http://api.conceptnet.io/query?node=/c/en/%s&rel=/r/%s&offset=%d&limit=%d'
    data = {}
    flag = True
    index = 0

    while flag:
        try:
            data = requests.get(base_query % (object_name, relation, index, limit)).json()
            save_json(data, join(conceptnet_path, '%s_%s_%d.json' % (object_name, relation, index)))
        except:
            query = base_query % (object_name, relation, index, limit)
            logging.error('Corrupted JSON file in "%s"' % query)
 
        if 'view' in data and 'nextPage'in data['view']:
            index += limit
        else:
            flag = False

def get_uri(object_id, delay=3):
    ''' Get the URI of an object throught Conceptnet RESTful API '''
    base_query = 'http://api.conceptnet.io/query?node=%s&rel=/r/ExternalURL&limit=30'
    try:
        data = requests.get(base_query % object_id).json()
        time.sleep(delay)
    except:
        time.sleep(60)
        query = base_query % object_id
        logging.error('Corrupted JSON file in "%s"' % query)
        return None

    for source in ['dbpedia.org', 'wordnet-rdf.princeton.edu']:# preference for these resources
        for element in data['edges']:
            if element['end']['site'] == source:
                return element['end']['@id']

    #if len(data['edges']) > 0:# TODO: Include other resources?
    #    return data['edges'][0]['end']['@id']

    return None