import requests
import cv2
import numpy as np
import os
from fpdf import FPDF

CARD_IMGS_ENDPOINT = 'https://api.scryfall.com/cards/collection'


def link_to_image(link):
    response = requests.get(link)
    data = np.frombuffer(response.content, np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_UNCHANGED)
    return image


def build_card_page(cards):
    page = np.ones((3508, 2480, 3)).astype(np.uint8) * 255

    padding = 1
    for idx, card in enumerate(cards):
        card_h, card_w, _ = card.shape

        x_idx = (idx % 3)
        y_idx = (idx // 3)

        x_offset = (x_idx * card_w) + (x_idx * padding)
        y_offset = (y_idx * card_h) + (y_idx * padding)

        page[80 + y_offset:80 + y_offset + card_h, 80 + x_offset:80 + x_offset + card_w] = card

    return page


def save_page(filename, page):
    cv2.imwrite(filename, page)


def get_img_link_from_card_obj(card_obj):
    return card_obj["image_uris"]['png']


def parse_deck_to_identifier(decklist_path):
    try:
        with open(decklist_path) as f:
            lines = f.readlines()
    except:
        print('')

    card_ids = []
    for line in lines:
        line_data = line.strip().split(' ')
        quantity = line_data[0]
        name = ' '.join(line_data[1:])

        for _ in range(int(quantity)):
            if "-" in name and len(name) == 36:  # TODO better pattern matching for UUID's
                card_id = {'id': name}
            else:
                card_id = {'name': name}
            card_ids.append(card_id)

    return card_ids


def file_path(path):
    if os.path.isfile(path):
        return path
    else:
        raise FileNotFoundError(path)


