from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class State:
    """Dados utilizados ao longo do programa"""

    db_manager: Any

    wait_reload: bool = False
    """Se o servidor deve esperar uma nova conexão (a página conetada está recarregando)."""

    connected_count: int = 0
    """Conta a quantidade de clientes conectados"""

    scraper: Any = None
    """Scraper utilizado para pesquisar."""

    cancel: bool = False
    # TODO: explicação

    pause: bool = False
    # TODO: explicação

    search_id: str = ""
    # TODO: explicação

    modified: bool = False
    # TODO: explicação
    # FIXME: isso é usado?
