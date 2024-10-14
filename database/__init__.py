#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import sqlite3
import sys
from os.path import exists
import subprocess
from datetime import date
import os
from os import path
import json


class Database:

    conn = None

    def __init__(self) -> None:
        """Inicia a conexão com o banco de dados."""
        self.conn = self.db_connection()

    def dump_table(self, table_name):
        """Importa um arquivo sql para ser injetado no banco de dados."""

        # Mimic the sqlite3 console shell's .dump command
        # Author: Paul Kippes <kippesp@gmail.com>

        """
        Returns an iterator to the dump of the database in an SQL text format.

        Used to produce an SQL dump of the database.  Useful to save an in-memory
        database for later restoration.  This function should not be called
        directly but instead called from the Connection method, iterdump().
        """

        schema = self.resource_path("schema.sql")
        cursor = sqlite3.connect("accb.sqlite").cursor()
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

    def import_database(self, file_path=None):
        """Importa um arquivo sql e injeta ele no banco de dados."""
        if file_path == None:
            """Metodo de importação para debug."""
            schema = self.resource_path("importar.sql")
            cursor = sqlite3.connect("accb.sqlite").cursor()
            with open(schema, "r", encoding="latin-1") as fp:
                text = fp.read().split(";")
                for command in text:
                    try:
                        cursor.execute(command)
                    except sqlite3.Error:
                        pass
        else:

            cursor = sqlite3.connect("accb.sqlite").cursor()
            for command in file_path.read().decode("latin-1").split(";"):
                try:
                    cursor.execute(command)
                except sqlite3.Error:
                    pass

    def log_error(self, err):
        """Loga um erro que aconteceu durante a execução do programa no arquivo error.log"""

        import time

        with open("error.log", "w+") as outfile:

            outfile.write("Date : {} \n".format(time.asctime()))
            for error in err:
                outfile.write(str(error))

        return

    def resource_path(self, path):
        """Recupera o caminho de um recurso da aplicação."""

        try:
            base_path = sys._MEIPASS
        except:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, path)

    def db_start(self):

        """Cria a estrutura do banco e inicia a conexão com o banco de dados uma vez que ele existe."""
        schema = self.resource_path("schema.sql")
        cursor = sqlite3.connect("accb.sqlite").cursor()
        sql_file = open(schema, encoding="utf-8")
        sql_as_string = sql_file.read()
        cursor.executescript(sql_as_string)
        sql_file.close()
        # subprocess.check_call(["attrib", "+H", "accb.sqlite"])

    def db_connection(self):
        """Realiza a conexão com o banco de dados ou o povoa caso não exista."""
        conn = None
        if exists("accb.sqlite"):
            conn = sqlite3.connect("accb.sqlite")
            conn.execute("PRAGMA foreign_keys = ON")
        else:
            self.db_start()
            conn = sqlite3.connect("accb.sqlite")
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA case_sensitive_like = true")
            self.db_update_city({"city_name": "Ilhéus", "primary_key": "IlhÃ©us"})

            # Salvar itabuna.json no exe e usar MEIAS.PATH
            # Salvar ilheus.json no exe e usar MEIAS.PATH
            with open(self.resource_path("itabuna.json"), "r", encoding="utf-8") as f:

                estab_info = json.load(f)

                for estab in estab_info:

                    self.db_save_estab(estab)

            with open(self.resource_path("ilheus.json"), "r", encoding="utf-8") as f:

                estab_info = json.load(f)

                for estab in estab_info:

                    self.db_save_estab(estab)

        return conn

    def db_save_city(self, name):
        """Salva as cidades no banco de dados."""
        self.conn = self.db_connection()
        cursor = self.conn.cursor()

        sql_query = """INSERT INTO city(city_name) VALUES(?)"""
        cursor = cursor.execute(sql_query, (name))
        self.conn.commit()
        self.db_end_conn()

    def db_save_product(self, product):
        """Salva os produtos no banco de dados."""

        self.conn = self.db_connection()
        cursor = self.conn.cursor()

        sql_query = """INSERT INTO product(product_name, keywords) VALUES(?,?)"""
        cursor = cursor.execute(
            sql_query, (product["product_name"], product["keywords"])
        )
        self.conn.commit()
        self.db_end_conn()

    def db_save_search(self, done, city_name, duration):
        """Salva as pesquisas no banco de dados."""

        self.conn = self.db_connection()
        cursor = self.conn.cursor()

        sql_query = """INSERT INTO search(done, city_name,search_date,duration) VALUES(?,?,?,?)"""
        cursor = cursor.execute(
            sql_query,
            (done, city_name, str(date.today()), duration),
        )
        self.conn.commit()
        self.db_end_conn()

        return cursor.lastrowid

    def db_save_estab(self, estab):
        """Salva os estabelecimentos no banco de dados."""

        self.conn = self.db_connection()
        cursor = self.conn.cursor()
        sql_query = """INSERT INTO estab(city_name, estab_name, adress, web_name) VALUES(?,?,?,?)"""
        cursor = cursor.execute(
            sql_query,
            (
                estab["city_name"],
                estab["estab_name"],
                estab["adress"],
                estab["web_name"],
            ),
        )
        self.conn.commit()
        self.db_end_conn()

    def db_save_backup(self, backup):
        """Salva o estado do backup no banco de dados."""

        self.conn = self.db_connection()
        cursor = self.conn.cursor()

        sql_query = """INSERT INTO backup(active, city, done, estab_info, product_info, search_id, duration, progress_value ) VALUES(?,?,?,?,?,?,?,?)"""
        cursor = cursor.execute(
            sql_query,
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
        self.conn.commit()
        self.db_end_conn()

    def db_save_search_item(self, search_item):
        """Salva os itens da pesquisa no banco de dados."""

        self.conn = self.db_connection()
        cursor = self.conn.cursor()

        sql_query = """INSERT INTO search_item(search_id, product_name, web_name,adress, price, keyword) VALUES(?,?,?,?,?,?)"""
        cursor = cursor.execute(
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
        self.conn.commit()
        self.db_end_conn()

    def db_save_city(self, city):
        """Salva as cidades no banco de dados."""

        self.conn = self.db_connection()
        cursor = self.conn.cursor()
        sql_query = """INSERT INTO city(city_name) VALUES(?)"""
        cursor = cursor.execute(sql_query, (city,))
        self.conn.commit()
        self.db_end_conn()

    # query
    def db_delete(self, table, where, value):
        """Deleta um elemento do banco de dados."""

        self.conn = self.db_connection()
        cursor = self.conn.cursor()
        sql_query = """DELETE FROM {} WHERE {} = "{}" """.format(table, where, value)
        cursor = cursor.execute(sql_query)
        self.conn.commit()
        self.db_end_conn()

    def db_get_city(self):
        """Seleciona uma cidade do banco de dados."""

        self.conn = self.db_connection()
        cursor = self.conn.cursor()
        cursor = self.conn.execute("SELECT * FROM city ORDER BY city_name ASC")
        cities = cursor.fetchall()
        self.db_end_conn()

        return cities

    # query
    def db_get_search(self, where=None, value=None):
        """Seleciona uma pesquisa do banco de dados."""

        self.conn = self.db_connection()
        cursor = self.conn.cursor()
        if value != None:
            cursor = self.conn.execute(
                "SELECT * FROM search WHERE {} = '{}' ORDER BY id ASC".format(
                    where, value
                )
            )
            search = cursor.fetchall()
        else:
            cursor = self.conn.execute("SELECT * FROM search ORDER BY id ASC")
            search = cursor.fetchall()
        self.db_end_conn()

        return search

    # query
    def db_get_search_item(self, search_id=None):
        """Seleciona itens de uma pesquisa do banco de dados."""

        self.conn = self.db_connection()
        cursor = self.conn.cursor()
        if search_id != None:
            cursor = self.conn.execute(
                "SELECT * FROM search_item WHERE search_id = '{}' ORDER BY search_id ASC".format(
                    search_id
                )
            )
            search_item = cursor.fetchall()
        else:
            cursor = self.conn.execute(
                "SELECT * FROM search_item ORDER BY search_id ASC"
            )
            search_item = cursor.fetchall()
        self.db_end_conn()

        return search_item

    # query
    def db_get_backup(self, id=None):
        """Seleciona um backup do banco de dados."""

        self.conn = self.db_connection()
        cursor = self.conn.cursor()
        if id != None:
            cursor = self.conn.execute(
                "SELECT * FROM backup WHERE search_id = {}".format(id)
            )
            backup = cursor.fetchall()
        else:
            cursor = self.conn.execute("SELECT * FROM backup")
            backup = cursor.fetchall()
        self.db_end_conn()

        return backup

    def db_get_product(self):
        """Seleciona produtos do banco de dados."""

        self.conn = self.db_connection()
        cursor = self.conn.cursor()
        cursor = self.conn.execute("SELECT * FROM product ORDER BY product_name ASC")
        products = cursor.fetchall()
        self.db_end_conn()

        return products

    def db_get_estab(self):
        """Seleciona estabelecimentos do banco de dados."""

        self.conn = self.db_connection()
        cursor = self.conn.cursor()
        cursor = self.conn.execute("SELECT * FROM estab")
        estabs = cursor.fetchall()
        self.db_end_conn()

        return estabs

    def db_update_estab(self, estab):
        """Atualiza estabelecimentos do banco de dados."""

        self.conn = self.db_connection()
        cursor = self.conn.cursor()
        sql_query = """UPDATE estab SET city_name="{}", estab_name="{}", adress="{}", web_name="{}" WHERE estab_name = "{}" """.format(
            estab["city_name"],
            estab["estab_name"],
            estab["adress"],
            estab["web_name"],
            estab["primary_key"],
        )
        cursor = cursor.execute(sql_query)
        self.conn.commit()
        self.db_end_conn()

    def db_update_product(self, product):
        """Atualiza produtos do banco de dados."""

        self.conn = self.db_connection()
        cursor = self.conn.cursor()
        sql_query = """UPDATE product SET product_name="{}", keywords="{}" WHERE product_name = "{}" """.format(
            product["product_name"], product["keywords"], product["primary_key"]
        )
        cursor = cursor.execute(sql_query)
        self.conn.commit()
        self.db_end_conn()

    def db_update_city(self, city):
        """Atualiza cidades do banco de dados."""

        self.conn = self.db_connection()
        cursor = self.conn.cursor()
        sql_query = """UPDATE city SET city_name="{}" WHERE city_name = "{}" """.format(
            city["city_name"], city["primary_key"]
        )
        cursor = cursor.execute(sql_query)
        self.conn.commit()
        self.db_end_conn()

    def db_update_backup(self, backup):
        """Atualiza um backup de pesquisa do banco de dados."""

        self.conn = self.db_connection()
        cursor = self.conn.cursor()
        sql_query = """UPDATE backup SET active ='{}', city = '{}', done = '{}', estab_info = '{}',product_info = '{}',duration = {} WHERE search_id = "{}" """.format(
            str(backup["active"]),
            backup["city"],
            backup["done"],
            backup["estab_info"],
            backup["product_info"],
            backup["duration"],
            backup["search_id"],
        )
        cursor = cursor.execute(sql_query)
        self.conn.commit()
        self.db_end_conn()

    # query
    def db_update_search(self, search):
        """Atualiza uma pesquisa de pesquisa do banco de dados."""

        self.conn = self.db_connection()
        cursor = self.conn.cursor()
        sql_query = (
            """UPDATE search SET done="{}", duration = {} WHERE id = "{}" """.format(
                search["done"], search["duration"], search["id"]
            )
        )
        cursor = cursor.execute(sql_query)
        self.conn.commit()
        self.db_end_conn()

    def db_run_query(self, query):
        """Roda uma query espeicifica no banco de dados."""

        self.conn = self.db_connection()
        cursor = self.conn.cursor()
        self.conn.commit()
        cursor = cursor.execute(query)
        values = cursor.fetchall()
        self.conn.commit()
        self.db_end_conn()

        return values

    def db_update_keyword(self, keyword):
        """Atualiza uma palavra chave do banco de dados."""

        self.conn = self.db_connection()
        cursor = self.conn.cursor()
        sql_query = """UPDATE keyword SET keyword="{}", rate={}, similarity={} WHERE id = {} """.format(
            keyword["keyword"], keyword["rate"], keyword["similarity"]
        )
        cursor = cursor.execute(sql_query)
        self.conn.commit()
        self.db_end_conn()

    def db_save_keyword(self, keyword):
        """Salva uma palavra chave no banco de dados."""

        self.conn = self.db_connection()
        cursor = self.conn.cursor()

        sql_query = """INSERT INTO keyword(product_name, keyword, rate, similarity) VALUES(?,?,?,?)"""
        cursor = cursor.execute(
            sql_query, (keyword["keyword"], keyword["rate"], keyword["similarity"])
        )
        self.conn.commit()
        self.db_end_conn()

    def db_end_conn(self):
        """Termina a conexão com o banco de dados."""

        if self.conn:
            self.conn.close()


# db = Database()
