from dataclasses import dataclass
from typing import TypedDict


@dataclass
class Backup:
    active: str
    city: str
    done: bool
    estab_info: dict
    product_info: dict
    search_id: str
    duration: int
    progress_value: float = -1  # FIXME: remover isso


@dataclass
class Product:
    name: str
    keywords: list[str]


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
class Search:
    id: int
    done: bool
    city_name: str
    search_date: str
    duration: float
