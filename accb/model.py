from dataclasses import dataclass
from typing import Optional


@dataclass
class Backup:
    search_id: int
    active: str
    city: str
    done: bool
    estab_info: dict
    product_info: dict
    duration: int
    progress_value: float = -1  # FIXME: remover isso


@dataclass
class City:
    name: str


@dataclass
class Estab:
    name: str
    address: str
    city_name: str
    web_name: str


@dataclass
class Product:
    name: str
    keywords: list[str]


@dataclass
class Search:
    id: Optional[int]
    city_name: str
    start_date: str
    total_duration: float

    _done: bool


@dataclass
class SearchItem:
    id: Optional[int]
    product_name: str
    web_name: str
    address: str
    price: str
    keyword: str


@dataclass
class OngoingSearch:
    search_id: int
    city_name: str
    estabs: list[Estab]
    products: list[Product]
    current_product: int
    current_keyword: int
    start_epoch: float
