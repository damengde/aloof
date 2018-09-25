# -*- coding: utf-8 -*-
import os
import re
import json
import codecs
from os.path import dirname, join

def save_json(data, json_path, sort_keys=True):
    ''' Save a dictionary into a JSON file '''
    with open(json_path, 'w') as fout:
        json.dump(data, fout, indent=4, sort_keys=sort_keys)

def load_json(json_path):
    ''' Load a JSON file into a dictionary '''
    with open(json_path) as fin:
        data = json.load(fin)

    return data

def save_file(file_path, lines):
    ''' Save a list of lines into a file '''
    with codecs.open(file_path, 'w', 'utf-8') as fout:
        fout.write('\n'.join(lines))

def load_file(file_path):
    ''' Load a file into a list of lines '''
    lines = []
    with codecs.open(file_path, 'r', 'utf-8') as fin:
        for line in fin:
            lines.append(line.rstrip())

    return lines

def map_wn31wn30():
    ''' Load mappings between WordNet 3.1 and WordNet 3.0 '''
    wn31wn30 = {}
    with codecs.open(join(os.path.dirname(__file__), '../../resource/mapping/wn30-31.map'), 'r', 'utf-8') as f:
        for line in f:
            wn30, wn31 = line.rstrip().split(' ')
            wn31wn30[wn31] = wn30

    return wn31wn30

def map_wn31bn35():
    ''' Load mappings between WordNet 3.1 and BabelNet 3.5 '''
    wn31bn35 = {}
    with codecs.open(join(dirname(__file__),'../../resource/mapping/bn35-wn31.map'), 'r', 'utf-8') as f:
        for line in f:
            bnid, wnlemma, wnoffset = line.rstrip().split(' ')
            wn31bn35[wnoffset[1:]] = bnid

    return wn31bn35

def map_wn31db():
    ''' Load mappings between WordNet 3.1 and DBpedia (or BabelNet if DBpedia does'nt exists) '''
    wn31bn35 = map_wn31bn35()
    bn35db = map_bn35db()
    wn31db = {}

    for wnid, bnid in wn31bn35.items():
        if bnid in bn35db and bn35db[bnid] != '-NA-':
            wn31db[wnid] = bn35db[bnid]
        else:
            wn31db[wnid] = bnid

    return wn31db

def map_wn30lemma():
    ''' Load mappings between WordNet 3.0 IDs and its lemmas '''
    wn30lemma = {}
    with codecs.open(join(os.path.dirname(__file__), '../../resource/mapping/wn30-lemma.map'), 'r', 'utf-8') as f:
        for line in f:
            wnid, wnlemma = line.rstrip().split('\t')
            wn30lemma[wnid] = wnlemma.split('.')[0]

    return wn30lemma

def map_lemmadb(lowercase=False):
    ''' Load mappings between lemmas and DBpedia (or BabelNet if DBpedia does'nt exists)'''
    bn35db = map_bn35db()
    lemmadb = {}

    with codecs.open(join(dirname(__file__),'../../resource/mapping/bn35-wn31.map'), 'r', 'utf-8') as f:
        for line in f:
            bnid, wnlemma, wnoffset = line.rstrip().split(' ')
            result = re.match('(.+)-(.)#(\d+)-.', wnlemma)
            digit = '0' + result.group(3) if len(result.group(3)) == 1 else result.group(3)
            wnlemma = '%s.%s.%s' % (result.group(1).replace('+', '_'), result.group(2), digit)
            if lowercase: wnlemma = wnlemma.lower()
            if bnid in bn35db and bn35db[bnid] != '-NA-':
                lemmadb[wnlemma] = bn35db[bnid]
            else:
                lemmadb[wnlemma] = bnid

    return lemmadb

def map_bn35db():
    ''' Load mappings between BabelNet 3.5 and DBpedia '''
    bn35db = {}
    with codecs.open(join(dirname(__file__),'../../resource/mapping/bn35-db.map'), 'r', 'utf-8') as f:
        for line in f:
            bnid, dbid = line.rstrip().split(' ')
            bn35db[bnid] = dbid

    return bn35db

def map_netlemma():
    ''' Load mappings between Wordnet 3.1/BabelNet 3.5 and lemmas '''
    netlemma = {}
    with codecs.open(join(dirname(__file__),'../../resource/mapping/bn35-wn31.map'), 'r', 'utf-8') as f:
        for line in f:
            bnid, wnlemma, wnoffset = line.rstrip().split(' ')
            lemma = wnlemma.split('-')[0].replace('+', '_')
            netlemma[wnoffset[1:]] = lemma # wordnet id to lemma
            netlemma[bnid] = lemma # babelnet id to lemma

    return netlemma

def create_uri(id_net):
    ''' Create a URI for BabelNet or DBpedia entry ID'''
    uri_net = None

    if id_net.startswith('s00'):
        uri_net = 'http://babelnet.org/rdf/%s' % id_net
    else:
        uri_net = 'http://dbpedia.org/resource/%s' % id_net

    return uri_net