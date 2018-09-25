# -*- coding: utf-8 -*-

import re
from gensim.models.keyedvectors import KeyedVectors
from sklearn.cluster import KMeans
from sklearn.neighbors import KNeighborsClassifier
from scipy.cluster.hierarchy import linkage, fcluster


def classification(attribute_frequency, model_path):
    ''' Classify attributes into 8 classes: color, shape, size, material, position, origin, age and  opinion '''
    model = KeyedVectors.load_word2vec_format(model_path, binary=True)
    attribute_categories = process_attributes(attribute_frequency, model)
    classes = ['color', 'shape', 'size', 'material', 'position', 'origin', 'age', 'opinion']
    #seeds = find_seeds(classes, attribute_categories, model)
    groups = classification_maxsimilarity(attribute_categories, model, classes)

    return groups['a']#TODO include verbs, adverbs and nouns?

def classification_maxsimilarity(attribute_categories, model, classes, threshold=0.25):
    ''' Classify attributes using Max Similarity '''
    groups = {}

    for pos_tag in attribute_categories.keys():
        groups[pos_tag] = {}
        for attribute in attribute_categories[pos_tag].keys():
            similarities = [model.similarity(attribute.split('.')[0], x) for x in classes]
            max_similarity = max(similarities)
            if max_similarity > threshold:
                index = similarities.index(max_similarity)
                label = classes[index]
            else:
                label = 'others'

            if label not in groups[pos_tag]:
                groups[pos_tag][label] = []
            groups[pos_tag][label].append(attribute)

    return groups

def classification_knn(visualgenome_path, model_path):
    ''' Classify attributes using K-Nearest Neighbors '''
    training = model[classes]
    labels = range(len(classes))
    neigh = KNeighborsClassifier(n_neighbors=1)
    neigh.fit(training, labels)
    groups = {}

    for pos_tag in attribute_categories.keys():
        groups[pos_tag] = {}
        for attribute in attribute_categories[pos_tag].keys():
            index = neigh.predict(model[attribute].reshape(1, -1))[0]
            label = classes[index]
            if label not in groups[pos_tag]:
                groups[pos_tag][label] = []
            groups[pos_tag][label].append(attribute)

    return groups

def find_seeds(classes, attribute_categories, model, top=10):
    ''' Find seed attributes using max similarity for each class '''
    similarities = {x:{} for x in classes}
    seeds = {}

    for pos_tag in attribute_categories.keys():
        for attribute in attribute_categories[pos_tag].keys():
            for class_name in classes:
                similarities[class_name][attribute] = model.similarity(attribute.split('.')[0], class_name)

    for class_name in similarities.keys():
        seeds[class_name] = sorted(similarities[class_name].items(), key=lambda x:x[1], reverse=True)[:top]
    
    return seeds

def clustering(attribute_frequency, model_path):
    ''' Clustering of attributes '''
    model = KeyedVectors.load_word2vec_format(model_path, binary=True)
    attribute_categories = process_attributes(attribute_frequency, model)
    clusters = {}

    for pos_tag in attribute_categories.keys():
        attributes = attribute_categories[pos_tag].keys()
        clusters[pos_tag] = get_clusters(attributes, model, 'partitional')

    return clusters['a']#TODO include verbs, adverbs and nouns?

def get_clusters(attributes, model, method='partitional', threshold=0.6, k=8):
    ''' Calculate the clusters using partitional(K-Means) and hierarchical approaches '''
    clusters = {}
    data = model[[x.split('.')[0] for x in attributes]]

    if method == 'partitional':
        if len(attributes) <= k: k = k / 2
        kmeans = KMeans(n_clusters=k, random_state=0).fit(data)
        labels = kmeans.labels_
    elif method == 'hierarchical':
        labels = fcluster(linkage(data, method='single'), threshold)

    for i in range(len(labels)):
        id_cluster = str(labels[i])
        element_cluster = attributes[i]
        if id_cluster not in clusters: clusters[id_cluster] = []
        clusters[id_cluster].append(element_cluster)

    return clusters

def process_attributes(attribute_frequency, model, min_frequency=3):
    ''' Pre-process attributes grouping them by their Part-of-Speech '''
    attribute_categories = {'a':{}, 'n':{}, 'v':{}, 'r':{}}

    for attribute_data in attribute_frequency:
        for attribute, frequency in attribute_data['attributes'].items():
            pos_tag = re.match('(.+)\.(.)\.(\d+)', attribute).group(2)
            if pos_tag == 's':
                pos_tag = 'a' # adjectives satellite are considered just like adjectives 
            if attribute not in attribute_categories[pos_tag]:
                attribute_categories[pos_tag][attribute] = 0
            attribute_categories[pos_tag][attribute] += frequency
   
    for pos_tag in attribute_categories.keys():
        for attribute in attribute_categories[pos_tag].keys():
            if not (attribute_categories[pos_tag][attribute] > min_frequency and attribute.split('.')[0] in model.vocab):
                del attribute_categories[pos_tag][attribute]

    return attribute_categories