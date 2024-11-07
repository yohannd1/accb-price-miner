from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from pathlib import Path

from accb.utils import log
from accb.database import DatabaseManager

if TYPE_CHECKING:
    from accb.scraper import Scraper


class State:
    """Dados utilizados ao longo do programa"""

    output_path: Optional[Path]
    """Caminho de saída dos dados (Excel)."""

    def __init__(self) -> None:
        self.wait_reload: bool = False
        """Se o servidor deve esperar uma nova conexão (a página conetada está recarregando)."""

        self.connected_count: int = 0
        """Conta a quantidade de clientes conectados."""

        self.scraper: Optional[Scraper] = None
        """Scraper utilizado para pesquisar."""

        self.db_manager = DatabaseManager()

        out_path = self.db_manager.get_option("path")
        if isinstance(out_path, str):
            self.output_path = Path(out_path)
        else:
            log("Caminho de saída de dados inválido!")
            self.output_path = None
