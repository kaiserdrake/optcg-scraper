from lxml import html
import requests_cache
from collections import deque
from pack import Pack, PackFormatter
from card import Card, CardFormatter
import logging
import argparse

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
    subparsers.add_parser('packs', help='List all available packs.', parents=[parent_parser])
    cards_parser = subparsers.add_parser('cards', help='List all cards available cards.', parents=[parent_parser])

    cards_parser.add_argument(
        'series_id',
        type=str,
        help='Series identifier for pack (e.g. "556101" for OP-01).')

    args = parser.parse_args()
    return args


if __name__ == "__main__":

    args = parse_args()

    if args.debug:
        __is_debug__ = True
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    elif args.verbose:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

    scraper = OptcgScraper()

    if args.command == 'packs':
        packs = scraper.fetch_packs()
        packs_text = PackFormatter.format(packs, args.format)
        print(packs_text)
    elif args.command == 'cards':
        cards = scraper.fetch_cards(args.series_id)
        cards_output = CardFormatter.format(cards, args.format)
        print(cards_output)
