# -*- coding: utf-8 -*-

import logging
import image_downloader
from textblob import Word
from SPARQLWrapper import SPARQLWrapper, JSON
from utils import load_json, load_file, save_json

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

def select_objects(all_objects_path, house_rooms_path, house_objects_path):
    ''' Select objects present in the category 'home or hotel' of SUN database '''
    all_objects = load_json(all_objects_path)
    house_rooms = load_file(house_rooms_path)
    house_objects = {}

    for room in house_rooms:
        for image_data in all_objects[room]['annotations']:
            for obj_name in image_data['rawObjects']:
                words = obj_name.split(' ')
                singular_name = Word(words[-1]).singularize() if words[-1] != 'glass' else words[-1]# many errors with word 'glass'
                if len(words) > 1:
                    singular_name = ' '.join(words[:-1] + [singular_name])

                if singular_name not in house_objects:
                    house_objects[singular_name] = 0
                house_objects[singular_name] += 1

    link_dbpedia(house_objects, house_objects_path)

def link_dbpedia(house_objects, house_objects_path):
    ''' Link objects to DBpedia URIs '''
    sparql = SPARQLWrapper('http://dbpedia.org/sparql')
    new_house_objects = {}

    for obj_name in house_objects.keys():
        dbpedia_name = Word(obj_name).capitalize()
        uri = execute_sparql_query(sparql, dbpedia_name)
        if uri == '' and ' ' in dbpedia_name: # is multiword
            approximation = True
            simplified_word = simplify_word(dbpedia_name)
            uri = execute_sparql_query(sparql, simplified_word)
        else:
            approximation = False

        if uri != '':
            new_house_objects[obj_name] = {'frequency':house_objects[obj_name], 'dbpedia_uri':uri, 'approximation':approximation}

    save_json(new_house_objects, house_objects_path) 
    logging.info('Total objects with URIs: %s' % len(new_house_objects))

def execute_sparql_query(sparql, word):
    ''' Execute a sparql query to retrieve the URI of an object using the label field '''
    uri = ''
    sparql.setQuery('''
        SELECT ?dbpresource
        WHERE {
              ?dbpresource rdfs:label "%s"@en
              FILTER(strStarts(str(?dbpresource), "http://dbpedia.org/resource"))
              FILTER (!strstarts(str(?dbpresource), "http://dbpedia.org/resource/Category:"))
        }''' % word)

    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()['results']['bindings']
    if len(results) > 0:
        uri = results[0]['dbpresource']['value']

    return uri

def simplify_word(multiword):
    ''' Simplify a multiword choosing one of its word as representative '''
    words = multiword.split(' ')
    if 'of' in words:#e.g. basket of banana
        first_word = words[0]
        return Word(first_word).singularize()
    else:#e.g. bathroom tile
        last_word = words[-1]
        return Word(last_word).capitalize()

def is_house_domain(phrase, model, house_domain_path, threshold=0.20):
    ''' Verify if the phrase belongs to the house domain '''
    domain_words = [line.rstrip() for line in open(house_domain_path)]
    similarity = 0

    if phrase in model.vocab:
        similarity = get_max_similarity(phrase, domain_words, model)
    else:
        words = phrase.split('_')
        for word in words:
            #similarity += get_max_similarity(word, domain_words, model)
            similarity = get_max_similarity(word, domain_words, model)
            if similarity >= threshold:
                return True

        #similarity /= len(words)

    if similarity >= threshold:
        return True

    return False

def get_average_similarity(word, domain_words, model):
    ''' Return the average similarity between a word and house-domain terms '''
    similarity = 0

    if word in model.vocab:
        for domain_word in domain_words:
            similarity += model.similarity(word, domain_word)

    return similarity / len(domain_words)

def get_max_similarity(word, domain_words, model):
    ''' Return the max similarity between a word and house-domain terms '''
    similarity = 0

    if word in model.vocab:
        for domain_word in domain_words:
            tmp_similarity = model.similarity(word, domain_word)
            if tmp_similarity > similarity:
                similarity = tmp_similarity

    return similarity

def download_images(house_objects_path, images_path):
    ''' Download images of the objects '''
    objects = load_json(house_objects_path)
    urls = set()

    for object_data in objects.values():
        url = object_data['dbpedia_uri']
        if url not in urls:
            urls.add(url)
    
    image_downloader.download_images(urls, images_path)