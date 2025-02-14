from __future__ import annotations

import re
import sqlite3
import sys
from os.path import exists
from datetime import date
import os
import json
from dataclasses import asdict
from typing import Any, Sequence, Generator, Optional, Iterable
from threading import Lock

from accb.model import Product, City, Estab, Search, SearchItem, OngoingSearch
from accb.utils import log
from accb.database.connection import Connection
from accb.database.upgrader import Upgrader

DB_PATH = "accb.sqlite"
ENCODING = "utf-8"  # or "latin-1"?

JsonValue = str | int | float | dict | list


class DatabaseManager:
    def __init__(self) -> None:
        self._conn_count = 0
        """A quantidade de vezes que uma conexão foi criada."""

        self._lock = Lock()

    def import_database_from_script(self, script: str) -> None:
        """Importa um arquivo sql e injeta ele no banco de dados."""

        # FIXME: evitar isso - é melhor limpar o banco de dados ou serializar p/ um arquivo JSON o conteúdo
        with self.db_connection() as conn:
            cursor = conn.get_cursor()

            for command in script.split(";"):
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

    def _init_conn(self) -> sqlite3.Connection:
        """Inicializa o banco de dados no caminho padrão, e retorna sua conexão."""

        schema = self.resource_path("schema.sql")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        with open(schema, "r", encoding=ENCODING) as f:
            cursor.executescript(f.read())

        conn.commit()
        return conn

    def _perform_conn_upgrade(self, cursor: sqlite3.Cursor, version: int) -> int:
        """Faz os upgrades necessários, e retorna a versão mais recente."""

        upgrader = Upgrader()

        @upgrader.until_version(0)
        def uv0() -> None:
            query = """
            PRAGMA foreign_keys = ON;
            PRAGMA case_sensitive_like = true;

            UPDATE city SET city_name = "Ilhéus" WHERE city_name = "IlhÃ©us";

            CREATE TABLE option (
                key text,
                value text,

                PRIMARY KEY (key)
            );
            """
            cursor.executescript(query)

        @upgrader.until_version(1)
        def uv1() -> None:
            # essa tabela parece não ser usada
            if cursor.execute("SELECT * FROM keyword").fetchone() is None:
                cursor.execute("DROP TABLE keyword")

        @upgrader.until_version(2)
        def uv2() -> None:
            query = """
            CREATE TABLE ongoing_search (
                search_id integer,
                city text,
                estabs_json text,
                products_json text,
                current_product integer,
                current_keyword integer,

                FOREIGN KEY (search_id) REFERENCES search (id),
                FOREIGN KEY (city) REFERENCES city (city)

                ON UPDATE CASCADE
                ON DELETE CASCADE
            );
            """
            cursor.executescript(query)

            backups = cursor.execute(
                """
            SELECT
                active, city, estab_info,
                product_info, search_id, done
            FROM backup
            """
            )

            for b in backups:
                done = b[5]
                if done == 1:
                    # ignorar backups de pesquisas já finalizadas
                    continue

                (current_product, current_keyword) = [int(x) for x in b[0].split(".")]
                city = b[1]

                estabs_old = json.loads(b[2])
                estabs_new = []
                for city, name, address, web_name in estabs_old["info"]:
                    estabs_new.append(
                        {
                            "name": name,
                            "city": city,
                            "address": address,
                            "web_name": web_name,
                        }
                    )
                estabs_json = json.dumps(estabs_new)

                products_old = json.loads(b[3])
                products_new = []
                for name, keywords in products_old:
                    products_new.append(
                        {
                            "name": name,
                            "keywords": keywords,
                        }
                    )
                products_json = json.dumps(products_new)

                search_id = int(b[4])

                query = """
                INSERT INTO ongoing_search
                    (search_id, city, estabs_json, products_json, current_product, current_keyword)
                VALUES
                    (?, ?, ?, ?, ?, ?)
                """

                cursor.execute(
                    query,
                    (
                        search_id,
                        city,
                        estabs_json,
                        products_json,
                        current_product,
                        current_keyword,
                    ),
                )

            cursor.execute("DROP TABLE backup")

        @upgrader.until_version(3)
        def uv3() -> None:
            query = """
            ALTER TABLE estab RENAME COLUMN adress TO address;
            ALTER TABLE search_item RENAME COLUMN adress TO address;
            """
            cursor.executescript(query)

        @upgrader.until_version(4)
        def uv4() -> None:
            query = """
            ALTER TABLE ongoing_search ADD duration_mins decimal DEFAULT 0.0;
            """
            cursor.executescript(query)

        @upgrader.until_version(5)
        def uv5() -> None:
            query = """
            CREATE TABLE search_log (
                search_id integer,
                message text,
                timestamp date,

                FOREIGN KEY (search_id) REFERENCES search (id),
                PRIMARY KEY (message, timestamp)
            );
            """
            cursor.executescript(query)

        upgrader.upgrade(version)
        final_version = upgrader.get_final_version()

        def set_option(key: str, value: str) -> None:
            if (
                cursor.execute("SELECT key FROM option WHERE key=?", (key,)).fetchone()
                is not None
            ):
                cursor.execute("UPDATE option SET value=? WHERE key=?", (value, key))
            else:
                cursor.execute(
                    "INSERT INTO option (key, value) VALUES (?, ?)", (key, value)
                )

        set_option("version", str(final_version))

        return final_version

    def _upgrade_conn(self, conn: sqlite3.Connection) -> None:
        cursor = conn.cursor()

        has_option_table = (
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='option';"
            ).fetchone()
            is not None
        )

        if has_option_table:
            (val,) = cursor.execute(
                "SELECT value FROM option WHERE key='version'"
            ).fetchone()
            version = int(val)
        else:
            version = 0

        log(f"Banco de dados está na versão {version}. Fazendo upgrades necessários...")
        new_version = self._perform_conn_upgrade(cursor, version)

        if version == new_version:
            log("Nenhum upgrade foi preciso.")
        else:
            log(f"Upgrade feito para a versão {new_version}.")

    def db_connection(self) -> Connection:
        """Realiza a conexão com o banco de dados ou o povoa caso não exista."""

        if exists(DB_PATH):
            conn = sqlite3.connect(DB_PATH)
        else:
            conn = self._init_conn()
            for estab_name in ("itabuna.json", "ilheus.json"):
                with open(self.resource_path(estab_name), "r", encoding=ENCODING) as f:
                    for entry in json.load(f):
                        estab = Estab(
                            name=entry["estab_name"],
                            city=entry["city_name"],
                            web_name=entry["web_name"],
                            address=entry["address"],
                        )
                        self.save_estab(estab)

        if self._conn_count == 0:
            try:
                self._upgrade_conn(conn)
                conn.commit()
            except sqlite3.Error as exc:
                conn.rollback()
                raise exc

        self._conn_count += 1

        return Connection(conn, self._lock)

    def create_city(self, name: str) -> None:
        with self.db_connection() as conn:
            cursor = conn.get_cursor()
            sql_query = """INSERT INTO city (city_name) VALUES (?)"""
            cursor.execute(sql_query, (name,))

    def save_product(self, product_name: str, keywords: str) -> None:
        """Salva um produto no banco de dados."""

        with self.db_connection() as conn:
            cursor = conn.get_cursor()
            query = """INSERT INTO product(product_name, keywords) VALUES(?, ?)"""
            cursor.execute(query, (product_name, keywords))

    def create_search(self, city: str) -> int:
        """Cria uma pesquisa e retorna seu ID."""
        return self.save_search(False, city, 0)

    def save_search(self, done: bool, city_name: str, duration: int) -> int:
        """Salva as pesquisas no banco de dados. Retorna o ID da última pesquisa"""

        with self.db_connection() as conn:
            cursor = conn.get_cursor()
            query = """INSERT INTO search(done, city_name, search_date, duration) VALUES(?, ?, ?, ?)"""
            cursor.execute(query, (int(done), city_name, str(date.today()), duration))
            id_ = cursor.lastrowid
            assert id_ is not None
            return id_

    def save_estab(self, estab: Estab) -> None:
        """Salva os estabelecimentos no banco de dados."""

        with self.db_connection() as conn:
            cursor = conn.get_cursor()
            query = """INSERT INTO estab(estab_name, city_name, address, web_name) VALUES(?, ?, ?, ?)"""
            cursor.execute(
                query,
                (
                    estab.name,
                    estab.city,
                    estab.address,
                    estab.web_name,
                ),
            )

    def save_search_item(self, search_item: SearchItem) -> None:
        """Salva os itens da pesquisa no banco de dados."""

        with self.db_connection() as conn:
            cursor = conn.get_cursor()

            tup = (
                search_item.search_id,
                search_item.product_name,
                search_item.web_name,
                search_item.address,
                search_item.price,
                search_item.keyword,
            )

            sql_query = """SELECT search_id FROM search_item WHERE search_id=? AND product_name=? AND web_name=? AND address=? AND price=? LIMIT 1"""
            if cursor.execute(sql_query, tup[:-1]).fetchone() is not None:
                log("Item de pesquisa a ser inserido já existe - ignorando")
                return

            sql_query = """INSERT INTO search_item(search_id, product_name, web_name, address, price, keyword) VALUES(?,?,?,?,?,?)"""
            cursor.execute(sql_query, tup)

    def delete(self, table: str, where: str, value: Any) -> None:
        """Deleta um elemento do banco de dados."""

        with self.db_connection() as conn:
            cursor = conn.get_cursor()
            query = self.safe_query_format(
                """ DELETE FROM {} WHERE {}=? """, table, where
            )
            cursor.execute(query, (value,))

    def get_cities(self) -> Iterable[City]:
        """Seleciona uma cidade do banco de dados."""

        with self.db_connection() as conn:
            cursor = conn.get_cursor()
            cursor.execute("""SELECT city_name FROM city ORDER BY city_name ASC""")
            return (City(name=name) for (name,) in cursor.fetchall())

    def get_search(self, where: str, equals: Any = None) -> list[Any]:
        """Seleciona uma pesquisa do banco de dados."""

        args: Sequence
        if equals is None:
            query = """SELECT * FROM search ORDER BY id ASC"""
            args = ()
        else:
            query = self.safe_query_format(
                "SELECT * FROM search WHERE {}=? ORDER BY id ASC", where
            )
            args = (equals,)

        with self.db_connection() as conn:
            cursor = conn.get_cursor()
            res = cursor.execute(query, args)
            return res.fetchall()

    def get_search_items(self, search_id: Optional[int] = None) -> list[SearchItem]:
        """Seleciona itens de uma pesquisa (ou todas, se `search_id` = None) do banco de dados."""

        args: tuple = ()
        if search_id is None:
            query = "SELECT search_id, product_name, web_name, address, price, keyword FROM search_item ORDER BY search_id, product_name, price ASC"
            args = ()
        else:
            query = "SELECT search_id, product_name, web_name, address, price, keyword FROM search_item WHERE search_id=? ORDER BY product_name, price ASC"
            args = (search_id,)

        with self.db_connection() as conn:
            cursor = conn.get_cursor()
            return [
                SearchItem(
                    search_id=search_id,
                    product_name=product_name,
                    web_name=web_name,
                    address=address,
                    price=price,
                    keyword=keyword,
                )
                for (
                    search_id,
                    product_name,
                    web_name,
                    address,
                    price,
                    keyword,
                ) in cursor.execute(query, args)
            ]

    def get_products(self) -> Iterable[Product]:
        """Obtém a lista de produtos do banco de dados."""

        with self.db_connection() as conn:
            cursor = conn.get_cursor()
            res = cursor.execute(
                """SELECT product_name, keywords FROM product ORDER BY product_name ASC"""
            )
            return (
                Product(name=name, keywords=keywords.split(","))
                for (name, keywords) in res.fetchall()
            )

    def get_product(self, name: str) -> Product:
        with self.db_connection() as conn:
            cursor = conn.get_cursor()
            res = cursor.execute("SELECT product_name, keywords FROM product WHERE product_name=?", (name,)).fetchall()
            (name, keywords) = res[0]
            return Product(name=name, keywords=keywords.split(","))

    def get_estabs(self) -> Iterable[Estab]:
        with self.db_connection() as conn:
            cursor = conn.get_cursor()
            res = cursor.execute(
                """SELECT city_name, estab_name, address, web_name FROM estab"""
            )
            return (
                Estab(city=city_name, name=name, address=address, web_name=web_name)
                for (city_name, name, address, web_name) in res.fetchall()
            )

    def get_estabs_for_city(self, city: str) -> Iterable[Estab]:
        with self.db_connection() as conn:
            cursor = conn.get_cursor()
            res = cursor.execute(
                """SELECT city_name, estab_name, address, web_name FROM estab WHERE city_name=?""",
                (city,),
            )
            return (
                Estab(city=city_name, name=name, address=address, web_name=web_name)
                for (city_name, name, address, web_name) in res.fetchall()
            )

    def get_estab_old(self) -> Iterable[Any]:
        """Seleciona estabelecimentos do banco de dados."""
        # FIXME: parar de usar isso (usar get_estabs)

        with self.db_connection() as conn:
            cursor = conn.get_cursor()
            res = cursor.execute("""SELECT * FROM estab""")
            return res.fetchall()

    def update_estab(self, estab: Estab, old_name: Optional[str] = None) -> None:
        """Atualiza estabelecimentos do banco de dados."""

        with self.db_connection() as conn:
            cursor = conn.get_cursor()
            query = """UPDATE estab SET city_name=?, estab_name=?, address=?, web_name=? WHERE estab_name=?"""
            key = old_name or estab.name
            cursor.execute(
                query,
                (
                    estab.city,
                    estab.name,
                    estab.address,
                    estab.web_name,
                    key,
                ),
            )

    def update_product(self, product: Product, old_name: Optional[str] = None) -> None:
        """Atualiza produtos do banco de dados."""

        with self.db_connection() as conn:
            cursor = conn.get_cursor()
            query = (
                """UPDATE product SET product_name=?, keywords=? WHERE product_name=?"""
            )

            key = old_name or product.name
            cursor.execute(
                query,
                (product.name, ",".join(product.keywords), key),
            )

    def update_city(self, city: City, old_name: str) -> None:
        """Atualiza cidades do banco de dados."""

        with self.db_connection() as conn:
            cursor = conn.get_cursor()
            query = """UPDATE city SET city_name=? WHERE city_name=?"""
            cursor.execute(query, (city.name, old_name))

    def update_search(self, search: Search) -> None:
        """Atualiza uma pesquisa de pesquisa do banco de dados."""

        with self.db_connection() as conn:
            cursor = conn.get_cursor()
            query = """UPDATE search SET done=-1, duration=? WHERE id=?"""
            cursor.execute(query, (search.total_duration_mins, search.id))

    def run_query(self, query: str, args: tuple = ()) -> list[Any]:
        """Roda uma query específica no banco de dados."""

        with self.db_connection() as conn:
            cursor = conn.get_cursor()
            res = cursor.execute(query, args)
            return list(res)

    @staticmethod
    def safe_query_format(fmt: str, *args: str) -> str:
        patt = re.compile(r"^[a-zA-Z0-9_]+$")
        for a in args:
            if patt.match(a) is not None:
                continue
            raise ValueError(
                f"{repr(a)} não passou o check de argumento seguro para query"
            )

        return fmt.format(*args)

    def get_incomplete_search_id(self) -> Optional[int]:
        query = "SELECT id FROM search WHERE done = 0 ORDER BY search_date DESC"
        result = self.run_query(query)

        if len(result) == 0:
            return None

        (id_,) = result[0]
        return id_

    def get_search_by_id(self, id_: int) -> Optional[Search]:
        result = self.run_query(
            "SELECT city_name, search_date, duration FROM search WHERE id=?",
            (id_,),
        )

        if len(result) == 0:
            return None

        (tup,) = result

        return Search(
            id=id_,
            city_name=tup[0],
            start_date=tup[1],
            total_duration_mins=tup[2],
        )

    def delete_search_by_id(self, id_: int) -> None:
        self.run_query("DELETE FROM search WHERE id=?", (id_,))

    def delete_ongoing_search_by_id(self, id_: int) -> None:
        self.run_query("DELETE FROM ongoing_search WHERE search_id=?", (id_,))

    def create_ongoing_search(self, o: OngoingSearch) -> None:
        self.run_query(
            "INSERT INTO ongoing_search (search_id, city, estabs_json, products_json, current_product, current_keyword, duration_mins) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                o.search_id,
                o.city,
                json.dumps([asdict(e) for e in o.estabs]),
                json.dumps(
                    [
                        {"name": p.name, "keywords": ",".join(p.keywords)}
                        for p in o.products
                    ]
                ),
                o.current_product,
                o.current_keyword,
                o.duration_mins,
            ),
        )

    def update_ongoing_search(self, o: OngoingSearch) -> None:
        self.run_query(
            "UPDATE ongoing_search SET search_id=?, city=?, estabs_json=?, products_json=?, current_product=?, current_keyword=?, duration_mins=? WHERE search_id=?",
            (
                o.search_id,
                o.city,
                json.dumps([asdict(e) for e in o.estabs]),
                json.dumps(
                    [
                        {"name": p.name, "keywords": ",".join(p.keywords)}
                        for p in o.products
                    ]
                ),
                o.current_product,
                o.current_keyword,
                o.duration_mins,
                o.search_id,
            ),
        )

    def get_ongoing_search_by_id(self, id_: int) -> Optional[OngoingSearch]:
        result = self.run_query(
            "SELECT city, estabs_json, products_json, current_product, current_keyword, duration_mins FROM ongoing_search WHERE search_id = ?",
            (id_,),
        )

        if len(result) == 0:
            return None

        (tup,) = result

        estabs = [Estab(**e) for e in json.loads(tup[1])]

        products = [
            Product(name=e["name"], keywords=e["keywords"].split(","))
            for e in json.loads(tup[2])
        ]

        return OngoingSearch(
            search_id=id_,
            city=tup[0],
            estabs=estabs,
            products=products,
            current_product=tup[3],
            current_keyword=tup[4],
            duration_mins=tup[5],
        )

    def get_ongoing_searches(self) -> list[OngoingSearch]:
        def unwrap(x):
            assert x is not None
            return x

        ids = self.run_query("SELECT search_id FROM ongoing_search")
        return [unwrap(self.get_ongoing_search_by_id(id_)) for (id_,) in ids]

    def get_option(self, key: str) -> Optional[JsonValue]:
        result = self.run_query("SELECT value FROM option WHERE key=?", (key,))

        if len(result) == 0:
            return None

        return json.loads(result[0][0])

    def set_option(self, key: str, value: JsonValue) -> None:
        if self.run_query("SELECT * FROM option WHERE key=?", (key,)):
            self.run_query(
                "UPDATE option SET value=? WHERE key=?", (json.dumps(value), key)
            )
            return

        self.run_query(
            "INSERT INTO option (key, value) VALUES (?, ?)", (key, json.dumps(value))
        )

    def add_log(self, message: str, timestamp: str, search_id: int) -> None:
        self.run_query(
            "INSERT INTO search_log (message, timestamp, search_id) VALUES (?, ?, ?)",
            (message, timestamp, search_id),
        )

    def get_logs(self, search_id: int) -> Iterable[str]:
        result = self.run_query(
            "SELECT message, timestamp FROM search_log WHERE search_id = ?",
            (search_id,),
        )
        return (f"[{timestamp}] {message}" for (message, timestamp) in result)

    def get_item_count_with(self, search_id: int, estab: Estab) -> int:
        result = self.run_query(
            "SELECT search_id FROM search_item WHERE search_id=? AND web_name=?",
            (search_id, estab.web_name),
        )
        return len(result)


def table_dump(conn: Connection, table_name: str) -> Generator[str, None, None]:
    """Importa um arquivo sql para ser injetado no banco de dados.

    ```
    Mimic the sqlite3 console shell's .dump command

    Author: Paul Kippes <kippesp@gmail.com>

    Returns an iterator to the dump of the database in an SQL text format.

    Used to produce an SQL dump of the database.  Useful to save an in-memory
    database for later restoration.  This function should not be called
    directly but instead called from the Connection method, iterdump().
    ```
    """

    cursor = conn.get_cursor()

    yield "BEGIN TRANSACTION;"

    # sqlite_master table contains the SQL CREATE statements for the database.
    q = """
        SELECT name, type, sql
        FROM sqlite_master
            WHERE sql NOT NULL AND
            type == 'table' AND
            name == :table_name
        """
    schema_res = cursor.execute(q, {"table_name": table_name})
    for name, _type, sql in schema_res.fetchall():
        if name == "sqlite_sequence":
            yield "DELETE FROM sqlite_sequence;"
        elif name == "sqlite_stat1":
            yield "ANALYZE sqlite_master;"
        elif name.startswith("sqlite_"):
            continue
        else:
            yield f"{sql};"

        # Build the insert statement for each row of the current table
        res = cursor.execute("PRAGMA table_info('%s')" % name)
        column_names = [str(table_info[1]) for table_info in res.fetchall()]
        q = 'SELECT \'INSERT INTO "%(tbl_name)s" VALUES('
        q += ",".join(["'||quote(" + col + ")||'" for col in column_names])
        q += ")' FROM '%(tbl_name)s'"
        query_res = cursor.execute(q % {"tbl_name": name})
        for row in query_res:
            yield f"{row[0]};"

    yield "COMMIT;"
