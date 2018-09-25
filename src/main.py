# -*- coding: utf-8 -*

import sys
import logging
import utils.object_filter as objs
import frames.dataset as frms
import conceptnet.dataset as cnet
import visualgenome.dataset as vgen
from datetime import datetime
from os.path import join, dirname


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

if __name__ == '__main__':
    start_time = datetime.now()
    option = sys.argv[1]

    #*********************** Frames ***********************#
    frame_raw_path = join(dirname(__file__), '../resource/frames/raw/')
    frame_parsed_path = join(dirname(__file__), '../resource/frames/parsed/')

    #********************* Attributes *********************#
    visualgenome_raw_path = join(dirname(__file__), '../resource/visualgenome/raw/')
    visualgenome_parsed_path = join(dirname(__file__), '../resource/visualgenome/parsed/')

    #********************* Conceptnet *********************#
    conceptnet_raw_path = join(dirname(__file__), '../resource/conceptnet/raw/')
    conceptnet_parsed_path = join(dirname(__file__), '../resource/conceptnet/parsed/')

    #********************** General ***********************#
    all_objects_path = join(dirname(__file__), '../resource/seeds/objects_sundatabase.json')
    house_objects_path = join(dirname(__file__), '../resource/seeds/objects_house.json')
    house_rooms_path = join(dirname(__file__), '../resource/seeds/house_rooms.txt')
    relations_path = join(dirname(__file__), '../resource/seeds/relations.txt')
    downloaded_images_path = join(dirname(__file__), '../resource/images/')
    embeddings_path = join(dirname(__file__), '../resource/embeddings/googlenews_negative300')
    

    if option == 'objects':
        objs.select_objects(all_objects_path, house_rooms_path, house_objects_path)
        objs.download_images(house_objects_path, downloaded_images_path)
    elif option == 'attributes':
        vgen.create_dataset(visualgenome_raw_path, visualgenome_parsed_path)
        vgen.select_relations(visualgenome_parsed_path, house_objects_path, embeddings_path)
        vgen.download_images(visualgenome_parsed_path, downloaded_images_path)
    elif option == 'frames':
        validator = sys.argv[2] if len(sys.argv) > 2 else 'core'
        frms.create_dataset(validator, frame_raw_path, frame_parsed_path)
        frms.select_relations(frame_parsed_path, house_objects_path)
        frms.download_images(frame_parsed_path, downloaded_images_path)

    elif option == 'conceptnet':
        cnet.create_dataset(conceptnet_raw_path, house_objects_path, relations_path)
        cnet.select_relations(conceptnet_raw_path, conceptnet_parsed_path, house_objects_path)
        cnet.download_images(conceptnet_parsed_path, downloaded_images_path)
    else:
        logging.error('Unknown "%s" argument' % option)

    end_time = datetime.now()
    logging.info('Duration {}'.format(end_time - start_time))