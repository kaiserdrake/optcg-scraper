from enum import StrEnum, auto
from dataclasses import dataclass, asdict, fields
from typing import Optional, List
from urllib.parse import urljoin
from lxml import html
import requests
import json
import logging
import os
import io
import csv


@dataclass
class Card:

    class Color(StrEnum):
        def _generate_next_value_(name, start, count, last_values):
            return name.capitalize()
        RED = auto()
        GREEN = auto()
        BLUE = auto()
        PURPLE = auto()
        BLACK = auto()
        YELLOW = auto()

    class Attribute(StrEnum):
        def _generate_next_value_(name, start, count, last_values):
            return name.capitalize()
        SLASH = auto()
        STRIKE = auto()
        RANGED = auto()
        SPECIAL = auto()
        WISDOM = auto()
        UNKNOWN = "?"

    class Category(StrEnum):
        def _generate_next_value_(name, start, count, last_values):
            return name.upper()
        LEADER = auto()
        CHARACTER = auto()
        EVENT = auto()
        STAGE = auto()
        DON = auto()

    class Rarity(StrEnum):
        COMMON = "C"
        UNCOMMON = "UC"
        RARE = "R"
        SUPER_RARE = "SR"
        SECRET_RARE = "SEC"
        LEADER = "L"
        SPECIAL = "SP CARD"
        TREASURE_RARE = "TR"
        PROMO = "P"

    card_id: str
    card_code: str
    rarity: Rarity
    category: Category

    name: str
    img_url: str

    attributes: list[Attribute]

    block: int

    color: Color
    effect: str

    cost: Optional[int] = None
    power: Optional[int] = None
    counter: Optional[int] = None

    types: Optional[list[str]] = None
    trigger: Optional[str] = None

    @staticmethod
    def get_xpath_value(tree, xpath, get_text=True):
        try:
            node = tree.xpath(xpath)[0]
            if get_text:
                return str(node).strip()
            else:
                return node
        except (IndexError, AttributeError):
            return None

    @staticmethod
    def get_text_after_anchor(tree, xpath_to_anchor, delimiter=' '):
        try:
            text_nodes = tree.xpath(f"{xpath_to_anchor}/following-sibling::*/text() | {xpath_to_anchor}/following-sibling::text()")

            # Clean up and join the text parts
            clean_parts = [t.strip() for t in text_nodes if t.strip()]
            full_text = delimiter.join(clean_parts)
            return full_text if full_text else None
        except Exception:
            return None

    @staticmethod
    def get_inner_html_without_h3(element):
        if element is None:
            return None

        h3 = element.find('h3')
        if h3 is None:
            return None

        # The content is the text after the <h3> (h3.tail) plus any following sibling elements
        content_parts = []
        if h3.tail and h3.tail.strip():
            content_parts.append(h3.tail.strip())

        for sibling in h3.itersiblings():
            content_parts.append(html.tostring(sibling, encoding='unicode'))

        full_content = "".join(content_parts).strip()
        return full_content if full_content else None

    @classmethod
    def from_xpathtree(cls, tree):

        card_info = tree.xpath('.//div[@class="infoCol"]/span/text()')
        base_url = tree.xpath('//meta[@property="og:image"]/@content')[0].strip()

        attributes_list = []
        raw_attributes_string = Card.get_xpath_value(tree, './/div[@class="attribute"]/i/text()')
        if raw_attributes_string:
            for attr_str in raw_attributes_string.split('/'):
                clean_attr_str = attr_str.strip()
                try:
                    attributes_list.append(Card.Attribute(clean_attr_str))
                except ValueError:
                    logging.error(f"Warning: Unknown attribute found: '{clean_attr_str}'")
                    attributes_list.append(clean_attr_str)

        power_val = Card.get_text_after_anchor(tree, './/div[@class="power"]/h3')
        counter_val = Card.get_text_after_anchor(tree, './/div[@class="counter"]/h3')
        img_url = Card.get_xpath_value(tree, './/img[@class="lazy"]/@data-src')
        if img_url and '?' in img_url:
            img_url = img_url.split('?')[0]

        try:
            effect_element = Card.get_xpath_value(tree, './/div[@class="text"]', get_text=False)
            effect_html = Card.get_inner_html_without_h3(effect_element)

            trigger_element = Card.get_xpath_value(tree, './/div[@class="trigger"]', get_text=False)
            trigger_html = Card.get_inner_html_without_h3(trigger_element)

            data = {
                'card_id': tree.get('id'),
                'card_code': card_info[0].strip() if len(card_info) > 0 else None,
                'rarity': Card.Rarity(card_info[1].strip()) if len(card_info) > 0 else None,
                'category': Card.Category(card_info[2].strip()) if len(card_info) > 0 else None,
                'name': Card.get_xpath_value(tree, './/div[@class="cardName"]/text()'),
                'img_url': urljoin(base_url, img_url),
                'cost': Card.get_text_after_anchor(tree, './/div[@class="cost"]/h3'),
                'attributes': attributes_list or None,
                'power': None if power_val == '-' else power_val,
                'counter': None if counter_val == '-' else counter_val,
                'color': Card.get_text_after_anchor(tree, './/div[@class="color"]/h3'),
                'block': Card.get_text_after_anchor(tree, './/div[@class="block"]/h3'),
                'types': Card.get_text_after_anchor(tree, './/div[@class="feature"]/h3', delimiter='\n'),
                'effect': effect_html,
                'trigger': trigger_html,
            }
            logging.info(f"Adding card: {data['card_code']}, {data['rarity']}, {data['category']}, {data['name']}")
        except (IndexError, ValueError, KeyError):
            raise ValueError("Card ID not found in the provided tree.")
        return cls(**data)


class CardFormatter:

    def download_image(url, save_path):
        if os.path.exists(save_path):
            logging.info(f"File already exists at {save_path}. Skipping download...")
            return True
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        except requests.exceptions.RequestException as e:
            logging.error(f"Error downloading the image: {e}")
        return False

    @staticmethod
    def to_text(cards: List[Card]) -> str:
        logging.info("Formatting card data to text...")
        lines = [
            f"  {card.card_code}, {card.rarity}, {card.name}, {card.category}, {card.card_id} "
            for card in cards
        ]
        return "\n".join(lines)

    @staticmethod
    def to_json(cards: List[Card]) -> str:
        logging.info("Formatting card data to JSON...")
        data = [asdict(card) for card in cards]
        return json.dumps(data, indent=2)

    @staticmethod
    def field_to_csv(val):
        if isinstance(val, list):
            return ",".join(str(v) for v in val)
        if hasattr(val, "value"):
            return str(val.value)
        return "" if val is None else str(val)

    @staticmethod
    def to_csv(cards: List[Card]) -> str:

        logging.info("Formatting card data to CSV...")
        if not cards:
            return ""

        header_row = [field.name for field in fields(Card)]
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        writer.writerow(header_row)
        for card in cards:
            row_values = [CardFormatter.field_to_csv(getattr(card, header)) for header in header_row]
            writer.writerow(row_values)
        return output.getvalue().strip()

    @staticmethod
    def to_img(cards: List[Card]) -> str:
        logging.info("Downloading card images...")
        if not cards:
            return "No cards to download images for."

        save_directory = "/tmp/downloaded_images"
        os.makedirs(save_directory, exist_ok=True)
        for card in cards:
            if not card.img_url:
                logging.warning(f"Card {card.card_id} has no image URL.")
                continue
            try:
                img_filename = f"{card.card_id}.jpg"
                file_path = os.path.join(save_directory, img_filename)
                CardFormatter.download_image(card.img_url, file_path)
                print(f" {card.card_id} dowloaded successfully to {img_filename}")
            except Exception as e:
                logging.error(f"Failed to download image for card {card.card_id}: {e}")
        return "DONE downloading."

    @classmethod
    def format(cls, packs: List[Card], format_type: str) -> str:
        formatters = {
            'text': cls.to_text,
            'json': cls.to_json,
            'csv': cls.to_csv,
            'img': cls.to_img,
        }

        formatter_func = formatters.get(format_type)

        if formatter_func:
            return formatter_func(packs)
        else:
            raise ValueError(f"Invalid format type specified: '{format_type}'. "
                             f"Available formats: {list(formatters.keys())}")
