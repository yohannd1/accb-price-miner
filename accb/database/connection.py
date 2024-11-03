from __future__ import annotations

import sqlite3

from accb.utils import log


class Connection:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._closed: bool = False
        self._conn = conn
        self._cursor = conn.cursor()

    def get_cursor(self) -> sqlite3.Cursor:
        return self._cursor

    def __enter__(self) -> Connection:
        return self

    def _close(self, has_errored: bool) -> None:
        if self._closed:
            return

        self._cursor.close()

        if has_errored:
            log("Ocorreu um erro - revertendo mudanças ao banco de dados")
            self._conn.rollback()
        else:
            self._conn.commit()
        self._conn.close()

        self._closed = True

    def __exit__(self, ext_type, exc_value, traceback) -> None:
        has_errored = isinstance(exc_value, Exception)
        self._close(has_errored)

    def __del__(self) -> None:
        self._close(has_errored=False)
