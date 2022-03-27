from dataclasses import dataclass
from typing import Optional

from yaml import load, SafeLoader


def to_multipart_form_data(data: dict) -> dict:
    result = dict()
    for k, v in data.items():
        result[k] = (None, v)
    return result


@dataclass
class ScraperConfig:
    CALCULATOR_URL: str
    TRADE_RESULTS_URL: str
    API_ENDPOINT_URL: str
    FUEL_NAME_TO_INSTRUMENT_CODES: dict[str, list[str]]
    FUEL_NAME_TO_CALCULATOR_ITEM: dict[str, Optional[str]]
    CALCULATOR_ITEM_WEIGHTS: dict[str, int]
    DELIVERY_BASIS_TO_CALCULATOR_STATION_NAME: dict[str, str]


def load_scraper_config(path: str) -> ScraperConfig:
    with open(path, 'r') as file:
        data = load(file, Loader=SafeLoader)
    return ScraperConfig(**data)
