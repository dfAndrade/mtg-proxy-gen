import requests
from tqdm import tqdm
import argparse
from pathlib import Path
from utils import link_to_image, build_card_page, get_img_link_from_card_obj, \
    save_page, parse_deck_to_identifier, CARD_IMGS_ENDPOINT, file_path
import os
from fpdf import FPDF

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Generate Magic The Gathering proxy decks ready to print')
    parser.add_argument('--path', type=file_path, default="decklist.txt", help='path to the decklist .txt file')
    parser.add_argument('--proxy_mark', type=bool, default=False, help='add proxy mark to each card')
    parser.add_argument('--add_mark', type=bool, default=True, help='add author mark to page empty space')
    args = parser.parse_args()
    # print(args)
    # print(args.path)
    decklist_path = Path(args.path)

    # Parse decklist
    print(f'>>> Parsing decklist in {decklist_path}')
    card_ids = parse_deck_to_identifier(decklist_path)

    # Get card objects from Scryfall API
    print(f'>>> Getting card objects from Scryfall API')
    card_objs = []
    for i in range(0, len(card_ids), 75):
        offset = min(75, len(card_ids)-i)
        myobj = {"identifiers": card_ids[i:i+offset]}
        resp = requests.post(CARD_IMGS_ENDPOINT, json = myobj)
        card_objs += resp.json()['data']

    # Get Images from card objects
    cards = []
    for card_obj in tqdm(card_objs, desc='>>> Fetching card images'):
        link = get_img_link_from_card_obj(card_obj)
        card_img = link_to_image(link=link)[:, :, :3]
        cards.append(card_img)

    # Build and generate proxy pages
    pdf = FPDF(orientation='P', unit="mm", format="A4")
    for i in tqdm(range(0, len(cards), 9), desc='>>> Generating proxy pages'):
        card_batch = cards[i:i+9]
        page = build_card_page(card_batch)
        pdf.add_page()
        temp_page_filename = f'page_{i//9}.png'
        save_page(temp_page_filename, page)
        pdf.image(temp_page_filename, x=0, y=0, w=210, h=297)
        os.remove(temp_page_filename)

    pdf.output(f"{str(decklist_path).split(os.sep)[-1].split('.')[0]}.pdf", "F")

