import sqlite3
import sys
from os.path import exists
import subprocess

# corrigir select , ASC
class Database:

    conn = None

    def __init__(self):

        self.conn = self.db_connection()

    def db_start(self):

        cursor = sqlite3.connect("accb.sqlite").cursor()
        sql_file = open("schema.sql")
        sql_as_string = sql_file.read()
        cursor.executescript(sql_as_string)
        # subprocess.check_call(["attrib", "+H", "accb.sqlite"])

    def db_connection(self):

        conn = None
        if exists("accb.sqlite"):
            conn = sqlite3.connect("accb.sqlite")
            conn.execute("PRAGMA foreign_keys = ON")
        else:
            self.db_start()
            conn = sqlite3.connect("accb.sqlite")
            conn.execute("PRAGMA foreign_keys = ON")
            self.db_update_city(
                {"city_name": "Ilhéus", "primary_key": "IlhÃ©us"})

        return conn

    def db_save_city(self, name):

        self.conn = self.db_connection()
        cursor = self.conn.cursor()

        sql_query = """INSERT INTO city(city_name) VALUES(?)"""
        cursor = cursor.execute(sql_query, (name))
        self.conn.commit()
        self.db_end_conn()

    def db_save_product(self, product):

        self.conn = self.db_connection()
        cursor = self.conn.cursor()

        sql_query = """INSERT INTO product(product_name, keywords) VALUES(?,?)"""
        cursor = cursor.execute(
            sql_query, (product['product_name'], product['keywords']))
        self.conn.commit()
        self.db_end_conn()

    def db_save_estab(self, estab):

        self.conn = self.db_connection()
        cursor = self.conn.cursor()
        sql_query = """INSERT INTO estab(city_name, estab_name, adress, web_name) VALUES(?,?,?,?)"""
        cursor = cursor.execute(
            sql_query, (estab["city_name"], estab["estab_name"], estab["adress"], estab["web_name"]))
        self.conn.commit()
        self.db_end_conn()

    def db_save_city(self, city):

        self.conn = self.db_connection()
        cursor = self.conn.cursor()
        sql_query = """INSERT INTO city(city_name) VALUES(?)"""
        cursor = cursor.execute(sql_query, (city,))
        self.conn.commit()
        self.db_end_conn()

    def db_delete(self, table, where, value):

        self.conn = self.db_connection()
        cursor = self.conn.cursor()
        sql_query = """DELETE FROM {} WHERE {} = "{}" """.format(
            table, where, value)
        cursor = cursor.execute(sql_query)
        self.conn.commit()
        self.db_end_conn()

    def db_get_city(self):

        self.conn = self.db_connection()
        cursor = self.conn.cursor()
        cursor = self.conn.execute("SELECT * FROM city ORDER BY city_name ASC")
        cities = cursor.fetchall()
        self.db_end_conn()

        return cities

    def db_get_product(self):

        self.conn = self.db_connection()
        cursor = self.conn.cursor()
        cursor = self.conn.execute(
            "SELECT * FROM product ORDER BY product_name ASC")
        products = cursor.fetchall()
        self.db_end_conn()

        return products

    def db_get_estab(self):

        self.conn = self.db_connection()
        cursor = self.conn.cursor()
        cursor = self.conn.execute("SELECT * FROM estab")
        estabs = cursor.fetchall()
        self.db_end_conn()

        return estabs

    def db_update_estab(self, estab):

        self.conn = self.db_connection()
        cursor = self.conn.cursor()
        sql_query = """UPDATE estab SET city_name="{}", estab_name="{}", adress="{}", web_name="{}" WHERE estab_name = "{}" """.format(
            estab["city_name"], estab["estab_name"], estab["adress"], estab["web_name"], estab["primary_key"])
        cursor = cursor.execute(sql_query)
        self.conn.commit()
        self.db_end_conn()

    def db_update_product(self, product):

        self.conn = self.db_connection()
        cursor = self.conn.cursor()
        sql_query = """UPDATE product SET product_name="{}", keywords="{}" WHERE product_name = "{}" """.format(
            product['product_name'], product['keywords'], product['primary_key'])
        cursor = cursor.execute(sql_query)
        self.conn.commit()
        self.db_end_conn()

    def db_update_city(self, city):

        self.conn = self.db_connection()
        cursor = self.conn.cursor()
        sql_query = """UPDATE city SET city_name="{}" WHERE city_name = "{}" """.format(
            city['city_name'], city['primary_key'])
        cursor = cursor.execute(sql_query)
        self.conn.commit()
        self.db_end_conn()

    def db_end_conn(self):

        if self.conn:
            self.conn.close()


# db = Database()
