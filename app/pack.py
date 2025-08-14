from dataclasses import dataclass, asdict, fields
from typing import List
import re
import unittest
import logging
import json


@dataclass
class Pack:

    series: str
    prefix: str
    name: str
    code: str

    @classmethod
    def from_title(cls, title, series):

        sanitized_title = re.sub('<[^>]+>', '', title)
        match = re.match(r'^(.*?)\s*-\s*(.*?)\s*-\s*(\[.*\])$', sanitized_title)
        if match:
            prefix, name, code = match.groups()
            code = code.strip('[]')
        else:
            # fallback or error handling
            raise ValueError(f"Invalid title format: {title}")
        logging.info(f"Adding pack: {series}, {prefix.strip()}, {name.strip()}, {code.strip()}")
        return cls(series, prefix.strip(), name.strip(), code.strip())


class PackFormatter:

    @staticmethod
    def to_text(packs: List[Pack]) -> str:
        logging.info("Formatting pack data to text...")
        lines = [
            f"  {pack.code}, {pack.series}, {pack.name}, {pack.prefix}, "
            for pack in packs
        ]
        return "\n".join(lines)

    @staticmethod
    def to_json(packs: List[Pack]) -> str:
        logging.info("Formatting pack data to JSON...")
        data = [asdict(pack) for pack in packs]
        return json.dumps(data, indent=2)

    @staticmethod
    def to_csv(packs: List[Pack]) -> str:
        logging.info("Formatting card data to CSV...")
        if not packs:
            return ""

        header_row = [field.name for field in fields(Pack)]
        output = [",".join(header_row)]

        # Get values using getattr for each field in the header
        for pack in packs:
            row_values = [str(getattr(pack, header)) for header in header_row]
            output.append(",".join(row_values))

        return "\n".join(output)

    @classmethod
    def format(cls, packs: List[Pack], format_type: str) -> str:
        formatters = {
            'text': cls.to_text,
            'json': cls.to_json,
            'csv': cls.to_csv,
        }

        formatter_func = formatters.get(format_type)

        if formatter_func:
            return formatter_func(packs)
        else:
            raise ValueError(f"Invalid format type specified: '{format_type}'. "
                             f"Available formats: {list(formatters.keys())}")


class TestPack(unittest.TestCase):
    def test_from_title_valid(self):
        title = "Prefix 1 - Starter Deck - [SD01]"
        series = "Series 1"
        pack = Pack.from_title(title, series)
        self.assertEqual(pack.series, series)
        self.assertEqual(pack.prefix, "Prefix 1")
        self.assertEqual(pack.name, "Starter Deck")
        self.assertEqual(pack.code, "SD01")

    def test_from_title_invalid(self):
        title = "Invalid Title Format"
        series = "Series 1"
        with self.assertRaises(ValueError):
            Pack.from_title(title, series)


if __name__ == "__main__":
    unittest.main()
