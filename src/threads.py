import argparse
import concurrent
import queue
import threading
import time
from pathlib import Path

import requests
from tqdm import tqdm

from utils import parse_deck_to_identifier, CARD_IMGS_ENDPOINT, file_path, get_img_link_from_card_obj, \
    full_link_to_image


def worker(inq, outq, work, pbar, event):
    while not event.is_set():
        try:
            conf = inq.get(timeout=2)
        except:
            continue

        work_res = work(conf)

        if outq is not None:
            outq.put(work_res)
        if pbar is not None:
            pbar.update()

        inq.task_done()

def create_workers(in_q, out_q, work, num_workers, executor, tasks, event, pbar=None):
    for idx in range(num_workers):
        tasks.append(executor.submit(worker, in_q, out_q, work, pbar, idx, event))


def map_sigint(event):
    import sys
    import signal
    def signal_handler(sig, frame):
        event.set()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)


# def cards_to_pdf(pdf_file, card_batch):
#     pdf = FPDF(orientation='P', unit="mm", format="A4")
#     for i in tqdm(range(0, len(cards), 9), desc='>>> Generating proxy pages'):
#         card_batch = cards[i:i + 9]
#         page = build_card_page(card_batch)
#         pdf.add_page()
#         temp_page_filename = f'page_{i // 9}.png'
#         save_page(temp_page_filename, page)
#         pdf.image(temp_page_filename, x=0, y=0, w=210, h=297)
#         os.remove(temp_page_filename)


if __name__ == '__main__':

    # Event to terminate workers
    running_flag = threading.Event()
    map_sigint(running_flag)

    start = time.monotonic()

    parser = argparse.ArgumentParser(description='Generate Magic The Gathering proxy decks ready to print')
    parser.add_argument('--path', type=file_path, default="decklist.txt", help='path to the decklist .txt file')
    parser.add_argument('--proxy_mark', type=bool, default=False, help='add proxy mark to each card')
    parser.add_argument('--add_mark', type=bool, default=True, help='add author mark to page empty space')
    args = parser.parse_args()

    decklist_path = Path(args.path)

    # Parse decklist
    print(f'>>> Parsing decklist in {decklist_path}')
    card_ids = parse_deck_to_identifier(decklist_path)
    num_cards = len(card_ids)

    print(f'>>> Fetching {num_cards} card{"s" if num_cards > 1 else ""}')

    card_objs = []
    objs = queue.Queue()
    links = queue.Queue()
    imgs = queue.Queue()

    # TODO turn this into pipeline obj
    for i in tqdm(range(0, len(card_ids), 75), desc="API Name   Fetch"):
        offset = min(75, len(card_ids) - i)
        my_obj = {"identifiers": card_ids[i:i + offset]}
        resp = requests.post(CARD_IMGS_ENDPOINT, json=my_obj)
        data = resp.json()['data']
        card_objs += data
        for item in data:
            objs.put_nowait(item)

    with concurrent.futures.ThreadPoolExecutor() as main_executor:
        # Progress bars
        pbar = tqdm(total=num_cards)
        pbar2 = tqdm(total=num_cards, position=0)

        # Container for task futures
        tasks = []

        # Hand crafted pipeline

        # - JSON -> img_link
        create_workers(objs, links, get_img_link_from_card_obj, 3, main_executor, tasks, running_flag, pbar)

        # - img_link to cv2_img
        create_workers(links, imgs, full_link_to_image, 10, main_executor, tasks, running_flag, pbar2)

        # - cv2_img -> 9 card batches TODO
        # - 9 card batches -> pdf_pages TODO
        # - pdf_pages ->  pdf_file TODO

        objs.join()
        pbar.close()

        result = []
        while not imgs.empty() or len(result) < num_cards:
            result.append(imgs.get())

        running_flag.set()
        pbar2.close()

        print(f"execution time {time.monotonic() - start} seconds")
