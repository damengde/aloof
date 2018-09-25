# -*- coding: utf-8 -*-

import re
import os
import time
import urllib
import logging
import requests
from os.path import join
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
YOUR_BABELNET_KEY = 'YOUR_BABELNET_KEY'

def download_images(urls, images_path, delay=5):
    ''' Download images from urls of Knowledge Database '''
    existing_images = get_existing_images(images_path)
    urls = urls.difference(existing_images)
    logging.debug('%s images to download' % len(urls))
    
    for url in urls:      
        logging.debug('Processing URL %s' % url)
        if url.startswith('http://dbpedia.org/'):
            file_path = join(images_path, 'dbpedia', url.split('/')[-1])
            download_image_dbpedia(url, file_path)
        elif url.startswith('http://babelnet.org'):
            file_path = join(images_path, 'babelnet', url.split('/')[-1])
            download_image_babelnet(url, file_path)
        elif url.startswith('http://en.wiktionary.org/'):
            file_path = join(images_path, 'wiktionary', url.split('/')[-1])
            download_image_wiktionary(url, file_path)
        else:
            logging.error('Not supported Knowledge Database to download image %s' % url)

        time.sleep(delay)

def download_image_dbpedia(url, file_path):
    ''' Download an image from DBpedia page '''
    data = requests.get(url).content
    soup = BeautifulSoup(data, 'html.parser')
    result = soup.find('a', {'class': 'uri', 'rel':'dbo:thumbnail'})
    if result:
        urllib.urlretrieve(result.get('href').encode('utf-8'), file_path)
    else:
        logging.warning('No image for url %s' % url)

def download_image_babelnet(url, file_path):
    ''' Download an image using Babelnet API '''
    base_query = 'https://babelnet.io/v5/getSynset?id=%s&key=%s'
    babelnet_id = 'bn:' + url.split('/')[-1][1:]

    try:
        data = requests.get(base_query % (babelnet_id, YOUR_BABELNET_KEY)).json()
        if len(data['images']) > 0:
            urllib.urlretrieve(data['images'][0]['url'].encode('utf-8'), file_path)
    except:
        query = base_query % (babelnet_id, YOUR_BABELNET_KEY)
        logging.error('Corrupted JSON file in "%s"' % query)   

def download_image_wiktionary(url, file_path):
    ''' Download an image from Wiktionary page '''
    data = requests.get(url).content
    soup = BeautifulSoup(data, 'html.parser')
    result = soup.find('img', {'class': 'thumbimage'})
    if result:
        urllib.urlretrieve('https:' + result.get('src'), file_path)
    else:
        logging.warning('No image for url %s' % url)

def get_existing_images(images_path):
    ''' Collect all the already downloaded images '''
    images_url = set()

    for dir_path, dir_names, file_names in os.walk(images_path):
        for file_name in file_names:
            resource = dir_path.split('/')[-1]
            if resource == 'dbpedia':
                images_url.add('http://dbpedia.org/resource/' + file_name)
            elif resource == 'babelnet':
                images_url.add('http://babelnet.org/rdf/' + file_name)
                
    return images_url