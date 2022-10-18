from cgi import print_directory
from re import L
import requests
import cv2
import numpy as np
import urllib.request
import matplotlib.pyplot as plt
from utils import link_to_image, build_card_page, get_img_link_from_card_obj, save_page, parse_deck_to_identifier
from tqdm import tqdm

decklist_path = 'C:\\Users\\FredOliveira\\Documents\\PythonProjects\\mtg-proxy-gen\\src\\decklist.txt'
card_ids = parse_deck_to_identifier(decklist_path)

url = 'https://api.scryfall.com/cards/collection'

card_objs = []
for i in range(0, len(card_ids), 75):
    offset = min(75, len(card_ids)-i)
    myobj = {"identifiers": card_ids[i:i+offset]}
    resp = requests.post(url, json = myobj)
    card_objs += resp.json()['data']


cards = []

for card_obj in card_objs:
    link = get_img_link_from_card_obj(card_obj)
    card_img = link_to_image(link=link)[:, :, :3]
    cards.append(card_img)

for i in tqdm(range(0, len(cards), 9)):
    card_batch = cards[i:i+9]
    page = build_card_page(card_batch)
    save_page(f'page_{i//9}.png', page)
    # plt.imshow(page)
    # plt.show()



