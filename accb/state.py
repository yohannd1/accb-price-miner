from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from accb.database import DatabaseManager
    from accb.scraper import Scraper


@dataclass
class State:
    """Dados utilizados ao longo do programa"""

    db_manager: DatabaseManager

    wait_reload: bool = False
    """Se o servidor deve esperar uma nova conexão (a página conetada está recarregando)."""

    connected_count: int = 0
    """Conta a quantidade de clientes conectados"""

    scraper: Optional[Scraper] = None
    """Scraper utilizado para pesquisar."""

    cancel: bool = False
    # TODO: explicação

    pause: bool = False
    # TODO: explicação

    search_id: Optional[int] = None
    """O ID da pesquisa atualmente ocorrendo (None se nenhuma pesquisa estiver ocorrendo)"""
