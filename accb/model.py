from typing import TypedDict


class Backup(TypedDict):
    active: str
    city: str
    done: bool
    estab_info: str  # TODO: consertar isso (p/ n ser JSON cru)
    product_info: str  # TODO: consertar isso (p/ n ser JSON cru)
    search_id: str
    duration: int
    progress_value: float
