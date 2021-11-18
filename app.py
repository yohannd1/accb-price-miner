#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, g
from engineio.async_drivers import gevent
from flask_material import Material
from flask_socketio import SocketIO, send, emit
import time
import json
import sqlite3
import sys
import os
import database
import traceback
import scrapper
import pandas as pd
import webbrowser
from datetime import date
import datetime
from xlsxwriter.workbook import Workbook
from openpyxl.styles import Border, Side, Alignment


app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
Material(app)
socketio = SocketIO(app)


def get_keywords(db):

    keywords = db.db_run_query("SELECT keywords FROM product")
    # Gera uma lista de lista de keywords
    keywords = [keyword[0].split(",") for keyword in keywords]
    # Flatten the list
    keywords = [keyword for sublist in keywords for keyword in sublist]
    print(keywords)


def xlsx_to_bd(db):

    df = pd.read_excel("keywords.xlsx", skiprows=0, index_col=0)
    search_id = db.db_save_search(1)

    for index, row in df.iterrows():

        name, local, keyword, adress, price = row
        # print(name, local, keyword, adress, price)

        try:
            db.db_save_search_item(
                {
                    "search_id": search_id,
                    "city_name": "Itabuna",
                    "web_name": local,
                    "adress": adress,
                    "product_name": name,
                    "price": price,
                    "keyword": keyword,
                }
            )
        except:
            pass

    return search_id


def log_error(err):

    with open("error.log", "w+") as outfile:

        outfile.write("Date : {} \n".format(time.asctime()))
        for error in err:
            outfile.write(str(error))

    return


def bd_to_xlsx(db, search_id, estab_data, city):

    today = date.today()
    # day = today.strftime("%d-%m-%Y")
    day = datetime.datetime.now()
    day = "[{}-{}]  [{} {}]".format(day.day, day.month, day.hour, day.minute)
    dic = "{} {}".format(city, day)

    folder_name = dic

    if not os.path.exists(dic):

        os.makedirs(dic)

    for city, name, adress, web_name in estab_data:

        print("Gerando Arquivo ... {}.xlsx , ADDRESS : {}".format(name, adress))
        new_file = name
        path = "{}\{}.xlsx".format(folder_name, new_file)
        products = db.db_run_query(
            "SELECT product_name, web_name, keyword, adress, price FROM search_item WHERE search_id = {} AND web_name = '{}' ORDER BY price ASC".format(
                search_id, web_name, adress
            )
        )

        print("QUERY RESULTS:")
        df = pd.DataFrame(
            data=products,
            columns=[
                "PRODUTO",
                "ESTABELECIMENTO",
                "PALAVRA-CHAVE",
                "ENDEREÇO",
                "PREÇO",
            ],
        )

        # df = df[df.ENDEREÇO.str.contains(adress.upper())]

        writer = pd.ExcelWriter(path, engine="openpyxl")

        df = df.to_excel(
            writer, sheet_name="Pesquisa", index=False, startrow=0, startcol=1
        )
        border = Border(
            left=Side(border_style="thin", color="FF000000"),
            right=Side(border_style="thin", color="FF000000"),
            top=Side(border_style="thin", color="FF000000"),
            bottom=Side(border_style="thin", color="FF000000"),
            diagonal=Side(border_style="thin", color="FF000000"),
            diagonal_direction=0,
            outline=Side(border_style="thin", color="FF000000"),
            vertical=Side(border_style="thin", color="FF000000"),
            horizontal=Side(border_style="thin", color="FF000000"),
        )

        workbook = writer.book["Pesquisa"]
        worksheet = workbook
        for cell in worksheet["B"]:

            cell.border = border
            cell.alignment = Alignment(horizontal="center")

        for cell in worksheet["C"]:

            cell.border = border
            cell.alignment = Alignment(horizontal="center")

        for cell in worksheet["D"]:

            cell.border = border
            cell.alignment = Alignment(horizontal="center")

        for cell in worksheet["E"]:

            cell.border = border
            cell.alignment = Alignment(horizontal="center")

        for cell in worksheet["F"]:

            cell.border = border
            cell.alignment = Alignment(horizontal="center")

        for col in worksheet.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2) * 1.2
            worksheet.column_dimensions[column].width = adjusted_width

        writer.save()


@app.route("/")
def home():

    db = database.Database()

    # get_keywords(db)
    # sys.exit()

    search_id = db.db_run_query(
        "SELECT id FROM search WHERE done = 0 AND search_date = '{}'".format(
            str(date.today())
        )
    )
    search = False
    active = "0.0"
    try:
        search_id = search_id[0]

        backup_info = db.db_get_backup(search_id)
        if len(backup_info) != 0:

            active, city, done, estab_info, product_info, search_id = backup_info[0]
            estab_info = json.loads(estab_info)
            estab_names = estab_info["names"]
            estab_data = estab_info["info"]
            product = json.loads(product_info)

            if done == 0:

                search = True

    except:
        pass

    product_len = db.db_run_query("SELECT product_name FROM product")
    search_info = db.db_run_query("SELECT * FROM search WHERE done = 1")

    city = db.db_get_city()
    estab = db.db_get_estab()
    product = db.db_get_product()

    return render_template(
        "home.html",
        data=city,
        search=search,
        product=" Iniciando Pesquisa ",
        city=city[0][0],
        estab_names=estab,
        products=product,
        active=active,
        product_len=len(product_len),
        search_info=search_info,
    )


@app.route("/insert_product")
def insert_product():

    db = database.Database()
    product_name = request.args.get("product_name")
    keywords = request.args.get("keywords")

    try:

        db.db_save_product({"product_name": product_name, "keywords": keywords})
        return {
            "success": True,
            "message": "O produto {} foi inserido com sucesso".format(product_name),
        }

    except sqlite3.Error as er:

        # print('SQLite error: %s' % (' '.join(er.args)))
        # print("Exception class is: ", er.__class__)
        # print('SQLite traceback: ')
        exc_type, exc_value, exc_tb = sys.exc_info()
        log_error(traceback.format_exception(exc_type, exc_value, exc_tb))

        return {
            "success": False,
            "message": "O produto {} não pode ser inserido.".format(product_name),
        }


@app.route("/remove_product")
def remove_product():

    db = database.Database()
    product_name = request.args.get("product_name")
    try:
        db.db_delete("product", "product_name", product_name)
        return {
            "success": True,
            "message": "O produto {} foi removido com sucesso".format(product_name),
        }

    except sqlite3.Error as er:

        # print('SQLite error: %s' % (' '.join(er.args)))
        # print("Exception class is: ", er.__class__)
        # print('SQLite traceback: ')
        exc_type, exc_value, exc_tb = sys.exc_info()
        log_error(traceback.format_exception(exc_type, exc_value, exc_tb))

        return {
            "success": False,
            "message": "O produto {} não pode ser removido.".format(product_name),
        }


@app.route("/select_product")
def select_product():

    db = database.Database()
    products = db.db_get_product()

    return json.dumps([product for product in products])


@app.route("/select_search_data")
def select_search_data():

    search_id = request.args.get("search_id")

    db = database.Database()
    search_data = db.db_run_query(
        "SELECT * FROM search JOIN search_item ON search.id = search_item.search_id AND search.id = {} AND search.done = '1' ORDER BY search_item.product_name, search_item.price ASC".format(
            search_id
        )
    )

    return json.dumps(search_data)


@app.route("/update_product")
def update_product():

    db = database.Database()
    product_name = request.args.get("product_name")
    keywords = request.args.get("keywords")
    primary_key = request.args.get("primary_key")

    try:

        db.db_update_product(
            {
                "product_name": product_name,
                "keywords": keywords,
                "primary_key": primary_key,
            }
        )
        return {
            "success": True,
            "message": "O produto {} foi atualizado com sucesso".format(primary_key),
        }

    except sqlite3.Error as er:

        # print('SQLite error: %s' % (' '.join(er.args)))
        # print("Exception class is: ", er.__class__)
        # print('SQLite traceback: ')
        exc_type, exc_value, exc_tb = sys.exc_info()
        log_error(traceback.format_exception(exc_type, exc_value, exc_tb))

        return {
            "success": False,
            "message": "O produto {} não pode ser atualizado.".format(primary_key),
        }


@app.route("/select_estab")
def select_estab():

    db = database.Database()
    city = request.args.get("city")
    g.estab = db.db_get_estab()
    g.estab_list = [estab for estab in g.estab if estab[0] == city]
    return json.dumps(g.estab_list)


@app.route("/remove_estab")
def remove_estab():

    db = database.Database()
    estab_name = request.args.get("estab_name")
    try:
        db.db_delete("estab", "estab_name", estab_name)
        return {
            "success": True,
            "message": "O estabelecimento {} foi removido com sucesso".format(
                estab_name
            ),
        }

    except sqlite3.Error as er:

        # print('SQLite error: %s' % (' '.join(er.args)))
        # print("Exception class is: ", er.__class__)
        # print('SQLite traceback: ')
        exc_type, exc_value, exc_tb = sys.exc_info()
        log_error(traceback.format_exception(exc_type, exc_value, exc_tb))

        return {
            "success": False,
            "message": "O estabelecimento {} não pode ser removido.".format(estab_name),
        }


@app.route("/update_estab")
def update_estab():

    db = database.Database()
    city_name = request.args.get("city_name")
    estab_name = request.args.get("estab_name")
    primary_key = request.args.get("primary_key")
    web_name = request.args.get("web_name")
    adress = request.args.get("adress")

    try:

        db.db_update_estab(
            {
                "primary_key": primary_key,
                "city_name": city_name,
                "estab_name": estab_name,
                "web_name": web_name,
                "adress": adress,
            }
        )
        return {
            "success": True,
            "message": "O estabelecimento {} foi atualizado com sucesso".format(
                estab_name
            ),
        }

    except sqlite3.Error as er:

        # print('SQLite error: %s' % (' '.join(er.args)))
        # print("Exception class is: ", er.__class__)
        # print('SQLite traceback: ')
        exc_type, exc_value, exc_tb = sys.exc_info()
        log_error(traceback.format_exception(exc_type, exc_value, exc_tb))

        return {
            "success": False,
            "message": "O estabelecimento {} não pode ser atualizado.".format(
                estab_name
            ),
        }


@app.route("/insert_estab")
def insert_estab():

    db = database.Database()
    city_name = request.args.get("city_name")
    estab_name = request.args.get("estab_name")
    web_name = request.args.get("web_name")
    adress = request.args.get("adress")

    try:

        db.db_save_estab(
            {
                "city_name": city_name,
                "estab_name": estab_name,
                "web_name": web_name,
                "adress": adress,
            }
        )
        return {
            "success": True,
            "message": "O estabelecimento {} foi adicionado com sucesso".format(
                estab_name
            ),
        }

    except sqlite3.Error as er:

        # print('SQLite error: %s' % (' '.join(er.args)))
        # print("Exception class is: ", er.__class__)
        # print('SQLite traceback: ')
        exc_type, exc_value, exc_tb = sys.exc_info()
        log_error(traceback.format_exception(exc_type, exc_value, exc_tb))

        return {
            "success": False,
            "message": "O estabelecimento {} não pode ser adicionado.".format(
                estab_name
            ),
        }


@app.route("/select_city")
def select_city():

    db = database.Database()
    g.cities = db.db_get_city()
    return json.dumps(g.cities)


@app.route("/insert_city")
def insert_city():

    db = database.Database()
    city_name = request.args.get("city_name")

    try:

        db.db_save_city(city_name)
        return {
            "success": True,
            "message": "A cidade {} foi adicionado com sucesso".format(city_name),
        }

    except sqlite3.Error as er:

        # print('SQLite error: %s' % (' '.join(er.args)))
        # print("Exception class is: ", er.__class__)
        # print('SQLite traceback: ')
        exc_type, exc_value, exc_tb = sys.exc_info()
        log_error(traceback.format_exception(exc_type, exc_value, exc_tb))

        return {
            "success": False,
            "message": "A cidade {} não pode ser adicionado.".format(city_name),
        }


@app.route("/update_city")
def update_city():

    db = database.Database()
    city_name = request.args.get("city_name")
    primary_key = request.args.get("primary_key")

    try:

        db.db_update_city({"city_name": city_name, "primary_key": primary_key})
        return {
            "success": True,
            "message": "A cidade {} foi editada com sucesso".format(city_name),
        }

    except sqlite3.Error as er:

        print("SQLite error: %s" % (" ".join(er.args)))
        print("Exception class is: ", er.__class__)
        print("SQLite traceback: ")
        exc_type, exc_value, exc_tb = sys.exc_info()
        log_error(traceback.format_exception(exc_type, exc_value, exc_tb))

        return {
            "success": False,
            "message": "A cidade {} não pode ser editada.".format(city_name),
        }


@app.route("/delete_city")
def delete_city():

    db = database.Database()
    city_name = request.args.get("city_name")

    try:

        db.db_delete("city", "city_name", city_name)
        return {
            "success": True,
            "message": "A cidade {} foi deletada com sucesso".format(city_name),
        }

    except sqlite3.Error as er:

        # print('SQLite error: %s' % (' '.join(er.args)))
        # print("Exception class is: ", er.__class__)
        # print('SQLite traceback: ')
        exc_type, exc_value, exc_tb = sys.exc_info()
        log_error(traceback.format_exception(exc_type, exc_value, exc_tb))

        return {
            "success": False,
            "message": "A cidade {} não pode ser deletada.".format(city_name),
        }


# SocketIO

# Inicia pesquisa
@socketio.on("search")
def handle_search(search_info):

    db = database.Database()

    search = db.db_get_search("search_date", str(date.today()))
    search_id = search[0][0] if len(search) != 0 else None

    backup_info = db.db_get_backup(search_id)

    if len(backup_info) != 0 and search_info["backup"] == 1:

        emit(
            "captcha",
            {"type": "notification", "message": "Retomando pesquisa ..."},
            broadcast=True,
        )
        active, city, done, estab_info, product_info, search_id = backup_info[0]
        estab_info = json.loads(estab_info)
        estab_names = estab_info["names"]
        estab_data = estab_info["info"]
        product = json.loads(product_info)

        if done == 0:
            scrap = scrapper.Scrap(
                estab_data, city, estab_names, product, active, search_id, False
            )

    else:
        emit(
            "captcha",
            {"type": "notification", "message": "Iniciando pesquisa ..."},
            broadcast=True,
        )
        if search_info["backup"] == 1 and len(backup_info) != 0:
            query = "DELETE * FROM search WHERE id = {}".format(search_id)
            db.db_run_query(query)

        search_id = db.db_save_search(0)
        active = "0.0"
        city = search_info["city"]
        estab_names = json.loads(search_info["names"])
        estabs = db.db_get_estab()
        product = db.db_get_product()

        estab_data = [
            estab for estab in estabs if estab[0] == city and estab[1] in estab_names
        ]

        scrap = scrapper.Scrap(
            estab_data, city, estab_names, product, active, search_id, False
        )

        db.db_save_backup(
            {
                "active": "0.0",
                "city": city,
                "done": 0,
                "estab_info": json.dumps({"names": estab_names, "info": estab_data}),
                "product_info": json.dumps(product),
                "search_id": search_id,
            }
        )

    try:

        scrap.run()
        emit(
            "captcha",
            {"type": "notification", "message": "Pesquisa concluida."},
            broadcast=True,
        )
        emit(
            "captcha",
            {"type": "progress", "done": 1},
            broadcast=True,
        )
        # search_id = xlsx_to_bd(db)
        bd_to_xlsx(db, search_id, estab_data, city)

    except:

        emit(
            "captcha",
            {"type": "notification", "message": "Ocorreu um erro durante a pesquisa."},
            broadcast=True,
        )
        exc_type, exc_value, exc_tb = sys.exc_info()
        log_error(traceback.format_exception(exc_type, exc_value, exc_tb))


# @socketio.on("quit")
# def handle_quit(quit_info):

#     print("quitting")
#     os._exit(0)


# Insere a função para ser chamada em todos os templates a qualquer momento


@app.context_processor
def utility_processor():
    def decode(text):
        return text.encode("utf8").decode("utf8")

    def replace(text, char):
        return text.replace(char, "")

    return dict(enumerate=enumerate, decode=decode, len=len, replace=replace)


if __name__ == "__main__":

    # app.run(debug=True)
    url = "http://127.0.0.1:5000"
    webbrowser.open(url)
    socketio.run(app, debug=False)
