# -*- coding: utf-8 -*

import logging
import kmedoids
import numpy as np
from multiprocessing import Pool
from frameinstancesimilarity import Frame_Similarity
from ntriples_reader import create_index
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
sim_evaluator = Frame_Similarity()

def find_prototypical_instances(frame_instances, min_elements=10):
    ''' Find prototypical frame instances for each frame type '''
    prototypical_instances = {}
    for frame_type in frame_instances.keys():
        if len(frame_instances[frame_type]) >= min_elements:
            logging.info('Analysing prototypical frames for %s' % frame_type)
            instance = frequency_approach(frame_instances[frame_type])
            prototypical_instances.update(instance)

    return prototypical_instances

def partitional_approach(frame_instances, percentage=10):
    ''' Find prototypical frame instances using partitional clustering approach '''
    condensed_matrix, instance_indexes = create_distance_matrix(frame_instances)
    num_clusters = len(frame_instances)/percentage + 1
    medoids, clusters = kmedoids.kMedoids(squareform(condensed_matrix), num_clusters)
    medoid_instances = {}

    for point_index in medoids:
        frame_id = instance_indexes[point_index]
        medoid_instances[frame_id] = format_instance(frame_instances[frame_id])

    return medoid_instances

def hierarchical_approach(frame_instances, threshold=0.3):
    ''' Find prototypical frame instances using hierarchical clustering approach '''
    condensed_matrix, instance_indexes = create_distance_matrix(frame_instances)
    assignments = fcluster(linkage(condensed_matrix, method='average'), threshold)
    clusters = {}

    for i in xrange(len(assignments)):
        id_cluster = assignments[i]
        element_cluster = instance_indexes[i]
        if id_cluster not in clusters: clusters[id_cluster] = []
        clusters[id_cluster].append(element_cluster)

    medoids = find_medoids(clusters, instance_indexes, squareform(condensed_matrix))
    medoid_instances = {}

    for frame_id in medoids:
        medoid_instances[frame_id] = format_instance(frame_instances[frame_id])

    return medoid_instances

def frequency_approach(frame_instances, top=10):
    ''' Find prototypical frame instances using the frequency approach '''
    frequency_instances = {}
    frequent_instances = {}

    for frame_id in frame_instances.keys():
        index = create_index(frame_instances[frame_id])
        if index not in frequency_instances:
            frequency_instances[index] = []
        frequency_instances[index].append(frame_id)

    for index, frame_ids in sorted(frequency_instances.items(), key=lambda x:len(x[1]), reverse=True)[:top]:
        frame_id = frame_ids[0]
        frequent_instances[frame_id] = format_instance(frame_instances[frame_id])

    return frequent_instances

def create_distance_matrix(frame_instances):
    ''' Create the distance matrix in condensed format '''
    frame_keys = frame_instances.keys()
    size = len(frame_keys)
    instance_indexes = []
    tuple_list = []

    for i in xrange(size):
        frame1 = frame_instances[frame_keys[i]]
        instance_indexes.append(frame_keys[i])
        for j in xrange(i+1, size):
            frame2 = frame_instances[frame_keys[j]]
            tuple_list.append((frame1, frame2))

    pool = Pool(processes=4)
    condensed_matrix = pool.map(calculate_distance, tuple_list)

    return np.array(condensed_matrix), instance_indexes

def calculate_distance(frames):
    distance = 1 - sim_evaluator.frame_instance_similarity(frames[0], frames[1], alpha=0)

    return distance

def find_medoids(clusters, instance_indexes, square_matrix, min_elements=3):
    ''' Find the medoids for a set of clusters '''
    medoids = []

    for cluster in clusters:
        elements = clusters[cluster]
        if len(elements) >= min_elements:
            indexes = [instance_indexes.index(x) for x in elements]
            medoid = instance_indexes[get_medoid_id(indexes, square_matrix)]
            medoids.append(medoid)

    return medoids

def get_medoid_id(indexes, square_matrix):
    ''' Get the medoid of a cluster '''
    size = len(indexes)
    min_distance = float('inf')
    medoid_id = None
        
    for i in xrange(size):
        global_distance = 0
        for j in xrange(size):
            if j != i:
                distance = square_matrix[indexes[i]][indexes[j]]
                global_distance += distance
                if global_distance > min_distance:
                    break
        if global_distance < min_distance:
            min_distance = global_distance
            medoid_id = indexes[i]

    return medoid_id

def format_instance(frame_instance):
    ''' Convert a frane instance to dict format '''
    frame_type = frame_instance.frame_type
    frame_elements = {x.role.lower():x.entity.split('/')[-1][:-1] for x in frame_instance.frame_elements}

    return {'type':frame_type, 'elements':frame_elements}