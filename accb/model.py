from dataclasses import dataclass
from typing import TypedDict


# TODO: portar para dataclass
class Backup(TypedDict):
    active: str
    city: str
    done: bool
    estab_info: str  # TODO: consertar isso (p/ n ser JSON cru)
    product_info: str  # TODO: consertar isso (p/ n ser JSON cru)
    search_id: str
    duration: int
    progress_value: float


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
