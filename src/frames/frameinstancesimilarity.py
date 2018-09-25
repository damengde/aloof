# -*- coding: utf-8 -*
# Original code in: https://github.com/valeriobasile/deko/blob/master/src/clustering/frameinstancesimilarity.py
import os
import math
import logging 
import requests
from nltk.corpus import framenet as fn
from nltk.corpus import wordnet
from scipy.spatial.distance import cosine

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

class Frame_Similarity:

    def __init__(self):
        self.__cache_frames = {}
        self.__cache_synsets = {}
        self.load_resources()

    def load_resources(self):
        # read the lexical units dictionary
        logging.info("reading FrameNet lexical units")
        self.lexical_units = dict()
        with open(os.path.join(os.path.dirname(__file__), "../../resource/fsimilarity/frame_lexical_units.tsv")) as f:
            for line in f:
                frame, lu = line.rstrip().split('\t')
                if not frame in self.lexical_units:
                    self.lexical_units[frame] = []
                self.lexical_units[frame].append(lu)

        # read Semcor lemmas:
        logging.info("reading Semcor 3.0 lemmas")
        self.semcor_lemmas = dict()
        self.semcor_sentences = dict()
        with open(os.path.join(os.path.dirname(__file__), "../../resource/fsimilarity/semcor3.0_lemmas.tsv")) as f:
            for line in f:
                sentence_id, lemma, sense = line.rstrip().split('\t')

                if not sentence_id in self.semcor_lemmas:
                    self.semcor_lemmas[sentence_id] = []
                self.semcor_lemmas[sentence_id].append(lemma)

                if not lemma in self.semcor_sentences:
                    self.semcor_sentences[lemma] = []
                self.semcor_sentences[lemma].append(sentence_id)

        # Mapping different WN versions
        logging.info("reading WordNet 3.0-3.1 mapping")
        self.wn31wn30 = dict()
        with open(os.path.join(os.path.dirname(__file__), '../../resource/mapping/wn30-31.map')) as f:
            for line in f:
                wn30, wn31 = line.rstrip().split(' ')
                self.wn31wn30[wn31] = wn30

        # creating dictionary of Wordnet synset id (offsets)
        logging.info("reading WordNet 3.0 offset-id mapping")
        self.offset2name = dict()
        with open(os.path.join(os.path.dirname(__file__), "../../resource/fsimilarity/wordnet_offsets.tsv")) as f:
            for line in f:
                offset, name = line.rstrip().split('\t')
                self.offset2name[offset] = name

        logging.info("loading frame vectors")
        frame_vectors = self.read_vector_file(os.path.join(os.path.dirname(__file__), '../../resource/fsimilarity/frame_vectors_glove6b.txt'))

    def read_vector_file(self, vector_file):
        f = open(vector_file,'r')
        model = {}
        for line in f:
            splitLine = line.split()
            word = splitLine[0]
            embedding = [float(val) for val in splitLine[1:]]
            model[word] = embedding
        return model

    def nasari_similarity(self, e1, e2):# for babelnet
        e1 = "bn:{0}".format(e1[1:])
        e2 = "bn:{0}".format(e2[1:])
        if e1 == e2:
            return 1.0

        result = requests.get('http://localhost:5000/nasari/cosine?key1=%s&key2=%s' % (e1, e2)).json()

        if 'similarity' in result:
            return result['similarity']

        return 0

    def frame_relatedness(self, frame1, frame2, ftsim='occ'):
        """Compute the relatedness between two frame types, using one of the
        methods proposed by Pennacchiotti and Wirth (ACL 2009)."""

        value_from_cache = self.get_from_cache(frame1, frame2, self.__cache_frames)
        if value_from_cache is not None:
            return value_from_cache

        if ftsim == 'occ':
            return self.cr_occ(frame1, frame2)
        elif ftsim == 'dist':
            return self.ftsim_dist(frame1, frame2)

    def ftsim_dist(self, frame1, frame2):
        v1 = frame_vectors[frame1]
        v2 = frame_vectors[frame2]
        return 1.0 - cosine(v1, v2)

    def cr_occ(self, frame1, frame2):
        """This is an implementation of the first co-occurrence measure of
        Pennacchiotti and Wirth (ACL2009), described in Sec. 4.2.1 of the paper.
        Input: two frame type names, e.g., Commerce_buy/Commerce_sell.
        Output: a real number (Pointwise-mutual information)."""
        
        lus1 = self.lexical_units[frame1]
        lus2 = self.lexical_units[frame2]

        '''Set of the contexts (sentences in Semcor 3.0) where the lexical units
        of frame1 occur'''
        cf1 = set()
        for lu in lus1:
            if lu in self.semcor_sentences:
                cf1 = cf1.union(set(self.semcor_sentences[lu]))

        '''Set the contexts (sentences in Semcor 3.0) where the lexical units
        of frame2 occur'''
        cf2 = set()
        for lu in lus2:
            if lu in self.semcor_sentences:
                cf2 = cf2.union(set(self.semcor_sentences[lu]))

        '''Set of the contexts where lexical units from both frames co-occur'''
        cf12 = cf1.intersection(cf2)

        '''Compute the Normalized Point-wise Mutual Information'''
        l1 = float(len(cf1))/float(len(self.semcor_lemmas))
        l2 = float(len(cf2))/float(len(self.semcor_lemmas))
        l12 = float(len(cf12))/float(len(self.semcor_lemmas))
        if l12 == 0.0 or l1 == 0.0 or l2 == 0.0:
            return 0.0
        else:
            #return (math.log(l12/(l1*l2), 2.0))/(-math.log(l12, 2.0))
            x = (math.log(l12/(l1*l2), 2.0))/(-math.log(l12, 2.0))
            normalized = (x+1)/2.0 # Normalized between [0,1] = (x-min(x))/(max(x)-min(x))
            return normalized

    def wup_similarity(self, s1, s2):
        synset1 = wordnet.synset(self.offset2name[s1])
        synset2 = wordnet.synset(self.offset2name[s2])
        result = synset1.wup_similarity(synset2)

        return result if result is not None else 0.0

    def synset_similarity(self, e1, e2, fesim='wup'):# for wordnet
        """Input: two concept URI, e.g, '<http://babelnet.org/rdf/s00046516n>?'
        Output: a real number between 0.0 and 1.0"""
        value_from_cache = self.get_from_cache(e1, e2, self.__cache_synsets) 
        if value_from_cache is not None:
            return value_from_cache

        synsetid1 = e1[1:-1].split('/')[-1]
        synsetid2 = e2[1:-1].split('/')[-1]

        if fesim == 'wup':
            return self.wup_similarity(self.wn31wn30[synsetid1], self.wn31wn30[synsetid2])
        elif fesim == 'dist':
            return self.nasari_similarity(synsetid1, synsetid2)

    def frame_element_relatedness(self, fe1, fe2, roles=False, fesim='dist'):
        """Computes an aggregate measure of relatedness between the entities
        involved in the frame elements.
        Input: two frame elements
        Output: a real number between 0.0 and 1.0"""
        sims1 = []
        for s1 in fe1:
            max_sim = 0.0
            for s2 in fe2:
                if roles == True and s1.role != s2.role:
                    sim = 0.0
                else:
                    sim = self.synset_similarity(s1.entity, s2.entity, fesim=fesim)
                if sim > max_sim:
                    max_sim = sim
            sims1.append(max_sim)

        if len(sims1) > 0:
            sim1 = sum(sims1)/float(len(sims1))
        else:
            sim1 = 0.0

        sims2 = []
        for s2 in fe2:
            max_sim = 0.0
            for s1 in fe1:
                if roles == True and s1.role != s2.role:
                    sim = 0.0
                else:
                    sim = self.synset_similarity(s1.entity, s2.entity, fesim=fesim)
                if sim > max_sim:
                    max_sim = sim
            sims2.append(max_sim)

        if len(sims2) > 0:
            sim2 = sum(sims2)/float(len(sims2))
        else:
            sim2 = 0.0      

        return (sim1+sim2)/2.0

    def frame_instance_similarity(self, fi1, fi2, alpha=0.40, roles=False, ftsim='occ', fesim='wup'):
        # the alpha prameter will be read from a config file
        frame_sim = self.frame_relatedness(fi1.frame_type, fi2.frame_type, ftsim=ftsim)
        fe_sim = self.frame_element_relatedness(fi1.frame_elements, fi2.frame_elements, roles=roles, fesim=fesim)
        sim = alpha * frame_sim + (1.0-alpha) * fe_sim

        return sim

    def get_from_cache(self, item1, item2, cache):
        if item1 == item2:
            return 1.0
        elif item1 in cache and item2 in cache[item1]:
            return cache[item1][item2]
        elif item2 in cache and item1 in cache[item2]:
            return cache[item2][item1]
        else:
            return None

    def set_caches(self, cache_frames, cache_synsets):
        self.__cache_frames = cache_frames
        self.__cache_synsets = cache_synsets
