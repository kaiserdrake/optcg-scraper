from lxml import html
import requests_cache
from collections import deque
import logging
import argparse
import os

from .pack import Pack, PackFormatter
from .card import Card, CardFormatter

__is_debug__ = False  # set --debug via command line argument


class OptcgScraper:

    def __init__(self):
        self.session = requests_cache.CachedSession('optcg_scrape', expire_after=7200)
        self.base_url = "https://asia-en.onepiece-cardgame.com"

    def fetch_packs(self):
        packs = deque()
        logging.info("Fetching packs from website...")
        resp = self.session.get(self.base_url + "/cardlist")
        tree = html.fromstring(resp.content)
        if __is_debug__:
            if resp.status_code == 200:
                file_path = "/tmp/packs_data.txt"
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(resp.text)
                logging.info(f"Content from {self.base_url} successfully dumped to {file_path}")

        elements = tree.xpath('//*[@id="series" and @name="series"]/option')
        for element in elements:
            if not element.attrib.get('value'):
                continue
            try:
                packs.append(Pack.from_title(element.text, element.attrib['value']))
            except ValueError as e:
                logging.debug(f"Error processing pack title '{element.text}': {e}")
                continue
        return packs

    def fetch_cards(self, series_id=None):
        cards = deque()
        if not series_id:
            logging.error("No pack name provided, aborting.")
            return cards

        params = {'series': series_id} if series_id else {}
        logging.info("Fetching cards for series_id={series_id} from website...")
        resp = self.session.get(self.base_url + "/cardlist/", params=params)
        tree = html.fromstring(resp.content)

        if __is_debug__:
            if resp.status_code == 200:
                file_path = "/tmp/cards_data.txt"
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(resp.text)
                logging.info(f"Content from {self.base_url} successfully dumped to {file_path}")

        elements = tree.xpath('//*[@id="cardlist"]/main/article/div/div[@class="resultCol"]//dl[@class="modalCol"]')
        for element in elements:
            try:
                card = Card.from_xpathtree(element)
                cards.append(card)
            except ValueError as e:
                logging.debug(f"Error processing card title '{element.id}': {e}")
                logging.debug("Card info" + html.tostring(element, encoding='unicode'))
                continue
        return cards


def parse_args():
    """
    Parse command line arguments for the OPTCG scraper.
    Returns:
        argparse.Namespace: Parsed command line arguments.
    """

    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        '-f', '--format',
        choices=['json', 'csv', 'text', 'img'],
        default='text',
        help='Output format for the results (default: text).')

    parent_parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output.')

    parent_parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output.')

    parser = argparse.ArgumentParser(description="Fetch OPTCG card details from the website.")
    subparsers = parser.add_subparsers(
        dest='command',
        required=True,
        help="The command to execute (e.g. 'packs', 'cards').")

    packs_parser = subparsers.add_parser('packs', help='List all available packs.', parents=[parent_parser])
    packs_parser.add_argument(
        'action',
        type=str,
        nargs='?',  # This makes the argument optional
        choices=['all'],
        default=None,
        help='Use "all" to fetch all cards from every pack.'
    )

    cards_parser = subparsers.add_parser('cards', help='List all cards available cards.', parents=[parent_parser])
    cards_parser.add_argument(
        'series_id',
        type=str,
        help='Series identifier for pack (e.g. "556101" for OP-01).')

    args = parser.parse_args()
    return args


def run_scraper(args):
    """
    Main logic for the scraper, callable from other scripts.
    """
    global __is_debug__
    if args.debug:
        __is_debug__ = True
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    elif args.verbose:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

    scraper = OptcgScraper()

    if args.command == 'packs':
        if args.action == 'all':
            logging.info("Fetching all available pack metadata...")
            available_packs = scraper.fetch_packs()

            if args.format == 'img':
                output_dir = "/tmp/downloaded_images"
                logging.info(f"Image download directory is {output_dir}")
            else:
                output_dir = "/tmp/cards/"
                os.makedirs(output_dir, exist_ok=True)
                logging.info(f"Output directory is set to {output_dir}")

            logging.info(f"Beginning to fetch cards for all {len(available_packs)} packs found...")
            for pack in available_packs:
                if not pack.series or not pack.code or pack.code == "None":
                    logging.warning(f"Skipping pack '{pack.name}' due to missing series ID or code.")
                    continue
                logging.info(f"Fetching cards for {pack.code} - {pack.name}...")
                cards_from_pack = scraper.fetch_cards(pack.series)
                if not cards_from_pack:
                    logging.warning(f"No cards found for pack {pack.code}. Skipping file creation.")
                    continue
                if args.format == 'img':
                    CardFormatter.format(list(cards_from_pack), 'img')
                else:
                    formatted_cards = CardFormatter.format(list(cards_from_pack), args.format)
                    filename = f"{pack.code}.{args.format}"
                    filepath = os.path.join(output_dir, filename)
                    try:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(formatted_cards)
                        logging.info(f"Successfully saved cards to {filepath}")
                    except IOError as e:
                        logging.error(f"Failed to write to file {filepath}: {e}")

            return f"Processing complete. Files saved in {output_dir}"
        else:
            packs = scraper.fetch_packs()
            return PackFormatter.format(list(packs), args.format)

    elif args.command == 'cards':
        cards = scraper.fetch_cards(args.series_id)
        return CardFormatter.format(list(cards), args.format)


if __name__ == "__main__":
    args = parse_args()
    result = run_scraper(args)
    if result:
        print(result)
