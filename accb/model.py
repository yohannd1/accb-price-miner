from dataclasses import dataclass
from typing import Optional


@dataclass
class City:
    name: str


@dataclass
class Estab:
    name: str
    address: str
    city: str
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
    total_duration_mins: float


@dataclass
class SearchItem:
    search_id: int
    product_name: str
    web_name: str
    address: str
    price: str
    keyword: str


@dataclass
class OngoingSearch:
    """Uma pesquisa que ainda não foi finalizada.

    A ideia é armazenar todo o estado possível dentro disso, para que modificações no banco de dados não afetem a pesquisa.

    Substitui o antigo conceito de Backup, mas tal nome ainda é usado na interface.
    """

    search_id: int
    city: str
    estabs: list[Estab]
    products: list[Product]
    current_product: int
    current_keyword: int
    duration_mins: float
