#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import annotations

import re
import sqlite3
import sys
from os.path import exists
import subprocess
from datetime import date
import os
from os import path
import json

from typing import Any, Sequence, Generator

from accb.utils import log

DB_PATH = "accb.sqlite"

class DatabaseConnection:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._closed: bool = False
        self._conn = conn
        self._cursor = conn.cursor()

    def get_cursor(self):
        return self._cursor

    def __enter__(self) -> DatabaseConnection:
        return self

    def _close(self, has_errored: bool) -> None:
        if self._closed:
            return

        self._cursor.close()

        if has_errored:
            log(f"Ocorreu um erro - revertendo mudanças ao banco de dados")
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


class DatabaseManager:
    def __init__(self) -> None:
        pass

    def dump_table(self, table_name: str) -> Generator[str, None, None]:
        """Importa um arquivo sql para ser injetado no banco de dados.

        Mimic the sqlite3 console shell's .dump command

        Author: Paul Kippes <kippesp@gmail.com>

        Returns an iterator to the dump of the database in an SQL text format.

        Used to produce an SQL dump of the database.  Useful to save an in-memory
        database for later restoration.  This function should not be called
        directly but instead called from the Connection method, iterdump().
        """

        schema = self.resource_path("schema.sql")
        cursor = sqlite3.connect(DB_PATH).cursor()
        table_name = table_name

        yield ("BEGIN TRANSACTION;")

        # sqlite_master table contains the SQL CREATE statements for the database.
        q = """
            SELECT name, type, sql
            FROM sqlite_master
                WHERE sql NOT NULL AND
                type == 'table' AND
                name == :table_name
            """
        schema_res = cursor.execute(q, {"table_name": table_name})
        for table_name, type, sql in schema_res.fetchall():
            if table_name == "sqlite_sequence":
                yield ("DELETE FROM sqlite_sequence;")
            elif table_name == "sqlite_stat1":
                yield ("ANALYZE sqlite_master;")
            elif table_name.startswith("sqlite_"):
                continue
            else:
                yield ("%s;" % sql)

            # Build the insert statement for each row of the current table
            res = cursor.execute("PRAGMA table_info('%s')" % table_name)
            column_names = [str(table_info[1]) for table_info in res.fetchall()]
            q = 'SELECT \'INSERT INTO "%(tbl_name)s" VALUES('
            q += ",".join(["'||quote(" + col + ")||'" for col in column_names])
            q += ")' FROM '%(tbl_name)s'"
            query_res = cursor.execute(q % {"tbl_name": table_name})
            for row in query_res:
                yield ("%s;" % row[0])

        yield ("COMMIT;")

    def import_database(self, file_path=None) -> None:
        """Importa um arquivo sql e injeta ele no banco de dados."""

        ENCODING = "utf-8" # or "latin-1"?

        if file_path is not None:
            sql_script = file_path.read().decode(ENCODING)
        else:
            schema_path = self.resource_path("importar.sql")
            with open(schema_path, "r", encoding=ENCODING) as file:
                sql_script = file.read()

        # FIXME: evitar isso - é melhor limpar o banco de dados ou serializar p/ um arquivo JSON o conteúdo
        with self.db_connection() as conn:
            cursor = conn.get_cursor()

            for command in sql_script.split(";"):
                # XXX: se tiver um texto com SQL, isso quebra
                try:
                    cursor.execute(command)
                except sqlite3.Error:
                    pass

            # Tentativa mais segura (mas não funciona porque dá erro e para a execução inteira):
            # try:
            #     cursor.executescript(sql_script)
            # except sqlite3.Error:
            #     pass

    def resource_path(self, path: str) -> str:
        """Recupera o caminho de um recurso da aplicação."""

        base_path = getattr(sys, "_MEIPASS", None) or os.path.abspath(".")
        return os.path.join(base_path, path)

    def db_start(self):
        """Cria a estrutura do banco e inicia a conexão com o banco de dados uma vez que ele existe."""
        schema = self.resource_path("schema.sql")
        cursor = sqlite3.connect(DB_PATH).cursor()
        sql_file = open(schema, encoding="utf-8")
        sql_as_string = sql_file.read()
        cursor.executescript(sql_as_string)
        sql_file.close()
        # subprocess.check_call(["attrib", "+H", DB_PATH])

    def db_connection(self) -> DatabaseConnection:
        """Realiza a conexão com o banco de dados ou o povoa caso não exista."""

        if exists(DB_PATH):
            conn = sqlite3.connect(DB_PATH)
            conn.execute("PRAGMA foreign_keys = ON")
        else:
            self.db_start()
            conn = sqlite3.connect(DB_PATH)
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA case_sensitive_like = true")
            self.db_update_city({"city_name": "Ilhéus", "primary_key": "IlhÃ©us"})

            for estab_name in ("itabuna.json", "ilheus.json"):
                with open(self.resource_path(estab_name), "r", encoding="utf-8") as f:
                    estab_info = json.load(f)
                    for estab in estab_info:
                        self.db_save_estab(estab)

        return DatabaseConnection(conn)

    def db_save_city(self, city):
        """Salva as cidades no banco de dados."""

        with self.db_connection() as conn:
            cursor = conn.get_cursor()
            sql_query = """INSERT INTO city(city_name) VALUES(?)"""
            cursor.execute(sql_query, (city,))

    def db_save_product(self, product_name: str, keywords: str) -> None:
        """Salva um produto no banco de dados."""

        with self.db_connection() as conn:
            cursor = conn.get_cursor()
            query = """INSERT INTO product(product_name, keywords) VALUES(?, ?)"""
            cursor.execute(query, (product_name, keywords))

    def db_save_search(self, done, city_name, duration) -> int:
        """Salva as pesquisas no banco de dados. Retorna o ID da última pesquisa"""
        # TODO: analisar isso direito - tá funcionando certo?

        with self.db_connection() as conn:
            cursor = conn.get_cursor()
            query = """INSERT INTO search(done, city_name, search_date, duration) VALUES(?, ?, ?, ?)"""
            cursor.execute(query, (done, city_name, str(date.today()), duration))
            return cursor.lastrowid

    def db_save_estab(self, estab):
        """Salva os estabelecimentos no banco de dados."""

        with self.db_connection() as conn:
            cursor = conn.get_cursor()
            query = """INSERT INTO estab(city_name, estab_name, adress, web_name) VALUES(?, ?, ?, ?)"""
            cursor.execute(
                query,
                (
                    estab["city_name"],
                    estab["estab_name"],
                    estab["adress"],
                    estab["web_name"],
                ),
            )

    def db_save_backup(self, backup):
        """Salva o estado do backup no banco de dados."""

        with self.db_connection() as conn:
            cursor = conn.get_cursor()
            query = """INSERT INTO backup(active, city, done, estab_info, product_info, search_id, duration, progress_value) VALUES(?,?,?,?,?,?,?,?)"""
            cursor.execute(
                query,
                (
                    str(backup["active"]),
                    backup["city"],
                    backup["done"],
                    backup["estab_info"],
                    backup["product_info"],
                    backup["search_id"],
                    backup["duration"],
                    backup["progress_value"],
                ),
            )

    def db_save_search_item(self, search_item):
        """Salva os itens da pesquisa no banco de dados."""

        with self.db_connection() as conn:
            cursor = conn.get_cursor()
            sql_query = """INSERT INTO search_item(search_id, product_name, web_name,adress, price, keyword) VALUES(?,?,?,?,?,?)"""
            cursor.execute(
                sql_query,
                (
                    search_item["search_id"],
                    search_item["product_name"],
                    search_item["web_name"],
                    search_item["adress"],
                    search_item["price"],
                    search_item["keyword"],
                ),
            )

    # query
    def db_delete(self, table, where, value):
        """Deleta um elemento do banco de dados."""

        with self.db_connection() as conn:
            cursor = conn.get_cursor()
            query = self.safe_query_format(""" DELETE FROM {} WHERE {} = ? """, table, where)
            cursor.execute(query, (value,))

    def db_get_city(self):
        """Seleciona uma cidade do banco de dados."""

        with self.db_connection() as conn:
            cursor = conn.get_cursor()
            cursor.execute("""SELECT * FROM city ORDER BY city_name ASC""")
            cities = cursor.fetchall()
            return cities

    # query
    def db_get_search(self, where: str, equals: Any = None) -> list[Any]:
        """Seleciona uma pesquisa do banco de dados."""

        args: Sequence
        if equals is None:
            query = """SELECT * FROM search ORDER BY id ASC"""
            args = ()
        else:
            query = self.safe_query_format(""" SELECT * FROM search WHERE {} = ? ORDER BY id ASC """, where)
            args = (equals,)

        with self.db_connection() as conn:
            cursor = conn.get_cursor()
            res = cursor.execute(query, args)
            return res.fetchall()

    # query
    def db_get_search_item(self, search_id=None):
        """Seleciona itens de uma pesquisa do banco de dados."""

        if search_id is None:
            query = "SELECT * FROM search_item ORDER BY search_id ASC"
            args = ()
        else:
            query = "SELECT * FROM search_item WHERE search_id = ? ORDER BY search_id ASC"
            args = (search_id,)

        with self.db_connection() as conn:
            cursor = conn.get_cursor()
            res = cursor.execute(query, args)
            return res.fetchall()

    # query
    def db_get_backup(self, id=None):
        """Seleciona um backup do banco de dados."""

        if id is None:
            query = "SELECT * FROM backup"
            args = ()
        else:
            query = "SELECT * FROM backup WHERE search_id = ?"
            args = (id,)

        with self.db_connection() as conn:
            cursor = conn.get_cursor()
            res = cursor.execute(query, args)
            return res.fetchall()

    def db_get_product(self):
        """Seleciona produtos do banco de dados."""

        with self.db_connection() as conn:
            cursor = conn.get_cursor()
            res = cursor.execute("""SELECT * FROM product ORDER BY product_name ASC""")
            return res.fetchall()

    def db_get_estab(self):
        """Seleciona estabelecimentos do banco de dados."""

        with self.db_connection() as conn:
            cursor = conn.get_cursor()
            res = cursor.execute("""SELECT * FROM estab""")
            return res.fetchall()

    def db_update_estab(self, estab):
        """Atualiza estabelecimentos do banco de dados."""

        with self.db_connection() as conn:
            cursor = conn.get_cursor()
            query = """ UPDATE estab SET city_name=?, estab_name=?, adress=?, web_name=? WHERE estab_name = ? """
            cursor.execute(
                query,
                (
                    estab["city_name"],
                    estab["estab_name"],
                    estab["adress"],
                    estab["web_name"],
                    estab["primary_key"],
                ),
            )

    def db_update_product(self, product):
        """Atualiza produtos do banco de dados."""

        with self.db_connection() as conn:
            cursor = conn.get_cursor()
            query = """ UPDATE product SET product_name=?, keywords=? WHERE product_name = ? """
            cursor.execute(
                query,
                (product["product_name"], product["keywords"], product["primary_key"]),
            )

    def db_update_city(self, city):
        """Atualiza cidades do banco de dados."""

        with self.db_connection() as conn:
            cursor = conn.get_cursor()
            query = """ UPDATE city SET city_name = ? WHERE city_name = ? """
            cursor.execute(query, (city["city_name"], city["primary_key"]))

    def db_update_backup(self, backup):
        """Atualiza um backup de pesquisa do banco de dados."""

        with self.db_connection() as conn:
            cursor = conn.get_cursor()
            query = """ UPDATE backup SET active = ?, city = ?, done = ?, estab_info = ?, product_info = ?, duration = ? WHERE search_id = ? """
            cursor.execute(
                query,
                (
                    str(backup["active"]),
                    backup["city"],
                    backup["done"],
                    backup["estab_info"],
                    backup["product_info"],
                    backup["duration"],
                    backup["search_id"],
                ),
            )

    # query
    def db_update_search(self, search):
        """Atualiza uma pesquisa de pesquisa do banco de dados."""

        with self.db_connection() as conn:
            cursor = conn.get_cursor()
            query = """ UPDATE search SET done = ?, duration = ? WHERE id = ? """
            cursor.execute(query, (search["done"], search["duration"], search["id"]))

    def db_run_query(self, query: str, args: tuple = ()) -> list[Any]:
        """Roda uma query específica no banco de dados."""

        with self.db_connection() as conn:
            cursor = conn.get_cursor()
            res = cursor.execute(query, args)
            return res.fetchall()

    def db_update_keyword(self, keyword):
        """Atualiza uma palavra chave do banco de dados."""

        with self.db_connection() as conn:
            cursor = conn.get_cursor()
            query = """ UPDATE keyword SET keyword = ?, rate = ?, similarity = ? WHERE id = ? """
            cursor.execute(
                query, (keyword["keyword"], keyword["rate"], keyword["similarity"])
            )

    def db_save_keyword(self, keyword):
        """Salva uma palavra chave no banco de dados."""

        with self.db_connection() as conn:
            cursor = conn.get_cursor()
            query = """ INSERT INTO keyword(product_name, keyword, rate, similarity) VALUES(?, ?, ?, ?) """
            cursor.execute(
                query,
                (
                    keyword["product_name"],
                    keyword["keyword"],
                    keyword["rate"],
                    keyword["similarity"],
                ),
            )

    @staticmethod
    def safe_query_format(fmt: str, *args: str) -> str:
        patt = re.compile(r"^[a-zA-Z0-9_]+$")
        for a in args:
            if patt.match(a) is not None:
                continue
            raise ValueError(f"valor não passou o check de argumento seguro para query: {repr(a)}")

        return fmt.format(*args)
