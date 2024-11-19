from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from pathlib import Path

from accb.utils import log
from accb.database import DatabaseManager

if TYPE_CHECKING:
    from accb.scraper import Scraper


class State:
    """Dados utilizados ao longo do programa"""

    def __init__(self) -> None:
        self.wait_reload: bool = False
        """Se o servidor deve esperar uma nova conexão (a página conetada está recarregando)."""

        self.connected_count: int = 0
        """Conta a quantidade de clientes conectados."""

        self.scraper: Optional[Scraper] = None
        """Scraper utilizado para pesquisar."""

        self.db_manager = DatabaseManager()

    def get_output_path(self) -> Optional[Path]:
        path = self.db_manager.get_option("path")

        if path is None:
            return None
        else:
            assert isinstance(path, str)
            return Path(path)
