"""Ponto de entrada da aplicação."""

from threading import Thread


def before_anything() -> None:
    from tkinter.messagebox import showwarning

    showwarning("ACCB", "Carregando. Por favor aguarde...")


Thread(target=before_anything).start()

# import eventlet
# eventlet.patcher.monkey_patch(select=True, socket=True)
# from engineio.async_drivers import gevent

# necessário para evitar bugs com aplicações que rodam tarefas no background.
# from engineio.async_drivers import threading

import math
import time
import json
import sqlite3
import sys
import os
from datetime import date, datetime
import traceback
import webbrowser
import subprocess
from typing import Optional
from pathlib import Path

from flask import Flask, render_template, request, g
from flask_material import Material
from flask_socketio import SocketIO, emit

import pandas as pd

from openpyxl.styles import Border, Side, Alignment

# from webdriver_manager.chrome import ChromeDriverManager
# from webdriver_manager.core.driver_cache import DriverCacheManager

from accb.scraper import Scraper, ScraperOptions
from accb.utils import (
    log,
    log_error,
    is_windows,
    ask_user_directory,
    get_time_hms,
)
from accb.state import State
from accb.consts import MONTHS_PT_BR
from accb.web_driver import is_chrome_installed
from accb.database import DatabaseManager

app = Flask(__name__)
Material(app)
socketio = SocketIO(app, manage_session=False, async_mode="threading")
# os.environ["WDM_LOG_LEVEL"] = "0"

state = State(
    db_manager=DatabaseManager(),
)

path = None
"""Variável de caminho padrão para gerar coleção excel."""


def is_port_in_use(port):
    """Confere se uma dada porta port está em uso pelo sistema."""
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def xlsx_to_bd(db, city_name):
    """Função para debug, injeta uma pesquisa com nome da cidade_todos.xlsx no banco de dados."""
    df = pd.read_excel("{}_todos.xlsx".format(city_name), skiprows=0, index_col=0)
    duration = get_time_hms(time.time())  # FIXME: ... tempo desde agora?
    search_id = db.db_save_search(1, city_name, duration["minutes"])

    for _index, row in df.iterrows():

        name, local, keyword, adress, price = row
        # print(name, local, keyword, adress, price)

        try:
            info = {
                "search_id": search_id,
                "web_name": local,
                "adress": adress,
                "product_name": name,
                "price": price,
                "keyword": keyword,
            }
            db.db_save_search_item(info)
        except Exception:
            pass

    return search_id


def get_time_filename() -> str:
    return datetime.now().strftime("[%d-%m] [%Hh %Mm]")


def bd_to_xlsx(db, search_id, estab_data, city):
    """Transforma uma dada pesquisa com id search_id em uma coleção de arquivos na pasta da cidade em questão (cidade) [data] [hora de geração dos arquivos]"""

    dic = f"{get_time_filename()} {city}"

    folder_name = dic

    final = Path(f"{path}/{dic}")
    final.mkdir(parents=True, exist_ok=True)

    for city, name, adress, web_name in estab_data:
        # print("Gerando Arquivo ... {}.xlsx , ADDRESS : {}".format(name, adress))
        new_file = name
        file_path = "{}/{}/{}.xlsx".format(path, folder_name, new_file)

        products = db.db_run_query(
            "SELECT product_name, web_name, keyword, adress, price FROM search_item WHERE search_id = {} AND web_name = '{}' ORDER BY price ASC".format(
                search_id, web_name
            )
        )

        # print("QUERY RESULTS:")
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

        # Filtra por endereço
        pattern = "|".join(adress.upper().split(" "))
        df = df[df.ENDEREÇO.str.contains(pattern, regex=True)]

        # df = df[df.ENDEREÇO.str.contains(adress.upper())]
        writer = pd.ExcelWriter(file_path, engine="openpyxl")

        df = df.to_excel(
            writer,
            sheet_name="Pesquisa",
            index=False,
            startrow=0,
            startcol=1,
            engine="openpyxl",
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
                except Exception:
                    pass
            adjusted_width = (max_length + 2) * 1.2
            worksheet.column_dimensions[column].width = adjusted_width

        writer.save()


@app.route("/")
def route_home():
    """Rota inicial do programa, realiza os tratamentos de backup e passa as informações básicas para o estado inicial da aplicação"""

    db = state.db_manager

    search_id = db.db_run_query(
        "SELECT id FROM search WHERE done = 0 AND search_date = '{}' ORDER BY city_name ASC".format(
            str(date.today())
        )
    )

    product_names = db.db_run_query("SELECT product_name FROM product")
    search = False
    progress_value = 0
    active = "0.0"
    try:
        search_id = search_id[0][0]

        backup_info = db.db_get_backup(search_id)
        # log_error(backup_info[0])
        if len(backup_info) != 0:
            (
                active,
                city,
                done,
                estab_info,
                product_info,
                search_id,
                duration,
                progress_value,
            ) = backup_info[0]
            if done == 0:

                search = True

    except:
        if not len(product_names) == 0:
            progress_value = 100 / len(product_names)

    day = str(date.today()).split("-")[1]
    search_info = db.db_run_query(
        "SELECT * FROM search WHERE done = 1 AND search_date LIKE '%%-{}-%%'".format(
            day
        )
    )

    search_years = db.db_run_query(
        "SELECT DISTINCT SUBSTR(search_date, '____',5) FROM search WHERE done = 1"
    )

    city = db.db_get_city()
    estab_names = db.db_get_estab()
    product = db.db_get_product()

    # print("CONNECTED {}".format(state.connected_count))
    # Se tiver mais que uma pagina aberta, renderiza o notallowed.html,
    # por algum motivo o flask com socketio chama a função de conexão 2x então
    # acaba ficando 0 ou 2 já que , 0 + 1 + 1 = 2
    template = "home.html" if 0 >= state.connected_count <= 2 else "notallowed.html"

    if not is_chrome_installed():
        initial_message = (
            "Instale uma versão qualquer do Google Chrome para realizar uma pesquisa."
        )
    elif len(product_names) == 0:
        initial_message = "Cadastre pelo menos um produto para realizar uma pesquisa"
    else:
        initial_message = "Selecione um município para prosseguir com a pesquisa"

    return render_template(
        template,
        initial_message=initial_message,
        data=city,
        search=search,
        product="Iniciando Pesquisa",
        city=city[0][0],
        estab_names=estab_names,
        products=product,
        active=active,
        product_len=len(product_names),
        search_info=search_info,
        progress_value=math.floor(progress_value),
        month=MONTHS_PT_BR,
        active_month=day,
        active_year=str(date.today()).split("-")[0],
        chrome_installed=str(is_chrome_installed()),
        years=search_years,
    )


@app.route("/insert_product")
def route_insert_product():
    """Rota de inserção de produtos no banco de dados."""
    db = state.db_manager
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
def route_remove_product():
    """Rota de remoção de produtos no banco de dados."""

    db = state.db_manager
    product_name = request.args.get("product_name")
    try:
        db.db_delete("product", "product_name", product_name)
        return {
            "success": True,
            "message": "O produto {} foi removido com sucesso".format(product_name),
        }

    except sqlite3.Error:
        exc_type, exc_value, exc_tb = sys.exc_info()
        log_error(traceback.format_exception(exc_type, exc_value, exc_tb))

        return {
            "success": False,
            "message": "O produto {} não pode ser removido.".format(product_name),
        }


@app.route("/select_product")
def route_select_product():
    """Rota de seleção de produtos."""

    db = state.db_manager
    products = db.db_get_product()

    return json.dumps([product for product in products])


@app.route("/select_search_data")
def route_select_search_data():
    """Rota de seleção de pesquisas no banco de dados."""

    search_id = request.args.get("search_id")
    city_name = request.args.get("city_name")
    # print(search_id)

    db = state.db_manager
    search_data = db.db_run_query(
        "SELECT * FROM search JOIN search_item ON search.id = search_item.search_id AND search.id = {} AND search.done = '1' ORDER BY search_item.product_name, search_item.price ASC".format(
            search_id
        )
    )

    # print(search_data)

    return json.dumps(search_data)


@app.route("/select_search_info")
def route_select_search_info():
    """Rota de seleção de informação das pesquisas no banco de dados."""
    db = state.db_manager
    month = request.args.get("month")
    search_data = ""
    try:
        year = request.args.get("year")
    except Exception:
        year = ""

    try:
        # print(f"month {month}")
        if year is None:
            month = "0" + month if int(month) < 10 else month
            search_data = db.db_run_query(
                "SELECT * FROM search WHERE done = 1 AND search_date LIKE '%-{}-%' ORDER BY city_name ASC".format(
                    month
                )
            )
        else:
            search_data = db.db_run_query(
                f"SELECT * FROM search WHERE done = 1 AND search_date LIKE '{year}%' ORDER BY city_name ASC"
            )
        print(f"search_data {search_data}")
        return {"success": True, "data": json.dumps(search_data)}

    except sqlite3.Error as er:
        exc_type, exc_value, exc_tb = sys.exc_info()
        log_error(traceback.format_exception(exc_type, exc_value, exc_tb))

        return {
            "success": False,
        }


@app.route("/update_product")
def route_update_product():
    """Rota de atualização de produtos no banco de dados."""
    db = state.db_manager
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
        state.wait_reload = True
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
def route_select_estab():
    """Rota de seleção de estabelecimentos no banco de dados."""

    db = state.db_manager
    city = request.args.get("city")
    g.estab = db.db_get_estab()
    g.estab_list = [estab for estab in g.estab if estab[0] == city]
    return json.dumps(g.estab_list)


@app.route("/remove_estab")
def route_remove_estab():
    """Rota de remoção de estabelecimentos no banco de dados."""
    db = state.db_manager
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
def route_update_estab():
    """Rota de atualização de estabelecimentos no banco de dados."""
    db = state.db_manager
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
def route_insert_estab():
    """Rota de inserção de estabelecimentos no banco de dados."""

    db = state.db_manager
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
def route_select_city():
    """Rota de seleção de cidades no banco de dados."""

    db = state.db_manager
    g.cities = db.db_get_city()
    return json.dumps(g.cities)


@app.route("/insert_city")
def route_insert_city():
    """Rota de inserção de cidades no banco de dados."""
    db = state.db_manager
    city_name = request.args.get("city_name")

    try:

        db.db_save_city(city_name)
        state.wait_reload = True
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
def route_update_city():
    """Rota de atualização de cidades no banco de dados."""

    db = state.db_manager
    city_name = request.args.get("city_name")
    primary_key = request.args.get("primary_key")

    try:

        db.db_update_city({"city_name": city_name, "primary_key": primary_key})
        state.wait_reload = True
        return {
            "success": True,
            "message": "A cidade {} foi editada com sucesso".format(city_name),
        }

    except sqlite3.Error as er:

        # print("SQLite error: %s" % (" ".join(er.args)))
        # print("Exception class is: ", er.__class__)
        # print("SQLite traceback: ")
        exc_type, exc_value, exc_tb = sys.exc_info()
        log_error(traceback.format_exception(exc_type, exc_value, exc_tb))

        return {
            "success": False,
            "message": "A cidade {} não pode ser editada.".format(city_name),
        }


@app.route("/delete_city")
def route_delete_city():
    """Rota de deleção de cidades no banco de dados."""

    db = state.db_manager
    city_name = request.args.get("city_name")

    try:

        db.db_delete("city", "city_name", city_name)
        state.wait_reload = True
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


@app.route("/set_path")
def route_set_path():
    try:
        global path

        directory = ask_user_directory()
        if directory is None:
            raise Exception("No directory selected")

        path = directory
        Path(path).mkdir(exist_ok=True)

        return {
            "success": True,
            "message": "Caminho configurado com sucesso.",
            "path": path,
        }

    except Exception:
        exc_type, exc_value, exc_tb = sys.exc_info()
        log_error(traceback.format_exception(exc_type, exc_value, exc_tb))

        return {
            "success": False,
            "message": "Ocorreu um erro durante a configuração de caminho padrão.",
        }


# Gerando Arquivos


@app.route("/delete_search")
def route_delete_search():
    """Rota de deleção de pesquisa no banco de dados."""
    try:

        db = state.db_manager
        search_id = request.args.get("search_id")

        db.db_delete("search", "id", search_id)
        state.wait_reload = True
        return {"status": "success", "message": "Pesquisa deletada com sucesso."}

    except:
        exc_type, exc_value, exc_tb = sys.exc_info()
        log_error(traceback.format_exception(exc_type, exc_value, exc_tb))
        return {
            "status": "error",
            "message": "Ocorreu um erro durante a deleção da pesquisa, mais detalhes no arquivo err.log.",
        }


@app.route("/export_database")
def route_export_database():
    """Rota responsável por exportar os dados do banco"""
    try:
        db = state.db_manager
        tables = ["city", "estab", "product"]
        with open("importar.sql", "w+") as f:
            for table in tables:
                for line in db.dump_table(table):
                    f.write("%s\n" % line)

        return {
            "status": "success",
            "message": "Dados exportados com sucesso, agora é possível importa-lo em outro computador com o arquivo importar.sql.",
        }

    except:
        exc_type, exc_value, exc_tb = sys.exc_info()
        log_error(traceback.format_exception(exc_type, exc_value, exc_tb))
        return {
            "status": "error",
            "message": "Ocorreu um erro durante a exportação dos dados.",
        }


@app.route("/import_database", methods=["POST"])
def route_import_database():
    """Rota responsável por importar os dados do banco"""
    try:
        db = state.db_manager
        file = request.files["file"]
        db.import_database(file)

        state.wait_reload = True
        return {
            "status": "success",
            "message": "Dados importados com sucesso.",
        }

    except:
        exc_type, exc_value, exc_tb = sys.exc_info()
        log_error(traceback.format_exception(exc_type, exc_value, exc_tb))
        return {
            "status": "error",
            "message": "Ocorreu um erro durante a importação dos dados.",
        }


def bd_to_xlsx_all(city, search_id, db):

    result = db.db_run_query(
        """
          SELECT DISTINCT * FROM search_item
          WHERE search_item.web_name NOT IN (SELECT web_name FROM estab)
          AND search_id={}
          GROUP BY web_name
        """.format(
            search_id
        )
    )

    # with open("estabs.log", "w+", encoding="latin-1") as outfile:

    #   outfile.write(json.dumps(result, indent=4, sort_keys=True))
    if not os.path.exists(f"{path}/Todos/"):
        os.makedirs(f"{path}/Todos")

    dic = f"{get_time_filename()} {city}"

    folder_name = dic

    if not os.path.exists(f"{path}/Todos/{dic}"):

        os.makedirs(f"{path}/Todos/{dic}")

    for id, product, web_name, adress, price, keyword in result:

        # print("Gerando Arquivo ... {}.xlsx , ADDRESS : {}".format(name, adress))
        new_file = web_name
        file_path = "{}/Todos/{}/{}.xlsx".format(path, folder_name, new_file)

        products = db.db_run_query(
            "SELECT product_name, web_name, keyword, adress, price FROM search_item WHERE search_id = {} AND web_name = '{}' ORDER BY price ASC".format(
                search_id, web_name
            )
        )

        # print("QUERY RESULTS:")
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
        # Filtra por endereço
        pattern = "|".join(adress.upper().split(" "))
        df = df[df.ENDEREÇO.str.contains(pattern, regex=True)]

        # df = df[df.ENDEREÇO.str.contains(adress.upper())]
        writer = pd.ExcelWriter(file_path, engine="openpyxl")

        df = df.to_excel(
            writer,
            sheet_name="Pesquisa",
            index=False,
            startrow=0,
            startcol=1,
            engine="openpyxl",
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

    return dic


@app.route("/open_folder")
def route_open_explorer():
    try:
        custom_path = request.args.get("path")
        custom_path = custom_path.replace("/", "\\")
        print(f"explorer {custom_path}")
        subprocess.Popen(f"explorer {custom_path}")
        return {"status": "success"}
    except:
        exc_type, exc_value, exc_tb = sys.exc_info()
        log_error(traceback.format_exception(exc_type, exc_value, exc_tb))
        return {"status": "error"}


@app.route("/clean_search")
def route_clean_search():
    """Rota que deleta todas as pesquisas e ou gera coleção de deletar as mesmas."""
    generate = request.args.get("generate")
    db = state.db_manager
    global path
    generate = True if generate == "false" else False
    if not generate:
        db.db_run_query("DELETE FROM search_item")
        db.db_run_query("DELETE FROM search")
        return {"status": "success", "message": "Pesquisas deletadas com sucesso."}
    try:

        cities = db.db_get_city()
        if not os.path.exists(f"{path}/Limpeza"):

            os.makedirs(f"{path}/Limpeza")

        for city in cities:

            estab_data = db.db_run_query(
                "SELECT * FROM estab WHERE city_name = '{}'".format(city[0])
            )
            folder_name = f"{path}/Limpeza/{city[0]}"
            new_path = f"{path}/Limpeza/{city[0]}"
            search_info = db.db_run_query(
                "SELECT DISTINCT id,search_date FROM search WHERE done = 1"
            )

            if not os.path.exists(new_path):

                os.makedirs(new_path)

            for id, search_date in search_info:

                for city, name, adress, web_name in estab_data:

                    # print(id, web_name)

                    # print("Gerando Arquivo ... {}.xlsx , ADDRESS : {}".format(name, adress))
                    new_file = name
                    file_path = "{}/{}/{}.xlsx".format(new_path, search_date, new_file)
                    if not os.path.exists("{}/{}".format(new_path, search_date)):

                        os.makedirs("{}/{}".format(new_path, search_date))

                    products = db.db_run_query(
                        "SELECT product_name, web_name, keyword, adress, price FROM search_item WHERE search_id = {} AND web_name = '{}' ORDER BY price ASC".format(
                            id, web_name
                        )
                    )
                    # print("QUERY RESULTS:")
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
                    # Filtra por endereço
                    # pattern = "|".join(adress.upper().split(" "))
                    # df = df[df.ENDEREÇO.str.contains(pattern, regex=True)]

                    # df = df[df.ENDEREÇO.str.contains(adress.upper())]
                    writer = pd.ExcelWriter(file_path, engine="openpyxl")

                    df = df.to_excel(
                        writer,
                        sheet_name="Pesquisa",
                        index=False,
                        startrow=0,
                        startcol=1,
                        engine="openpyxl",
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

        db.db_run_query("DELETE FROM search_item")
        db.db_run_query("DELETE FROM search")
        return {
            "status": "success",
            "dic": f"{path}/Limpeza",
            "message": "Pesquisas deletadas com sucesso.",
        }

    except:
        exc_type, exc_value, exc_tb = sys.exc_info()
        log_error(traceback.format_exception(exc_type, exc_value, exc_tb))
        return {"status": "error"}


@app.route("/generate_file")
def route_bd_to_xlsx():
    """Rota geradora de coleção de dados das pesquisas em excel."""
    db = state.db_manager
    global path

    try:

        format_type = request.args.get("format")
        city = request.args.get("city_name")
        search_id = request.args.get("search_id")

        dic = f"{get_time_filename()} {city}"

        # TODO; Criar função pra formatar todos os estabelecimentos não cadastrados e retornar uma coleção formatada deles bd_to_xlsx_all

        if format_type == "all":
            dic = bd_to_xlsx_all(city, search_id, db)
            return {"status": "success", "dic": dic}

        estab_names = json.loads(request.args.get("names"))
        estabs = db.db_get_estab()
        product = db.db_get_product()

        estab_data = [
            estab for estab in estabs if estab[0] == city and estab[1] in estab_names
        ]

        # day = today.strftime("%d-%m-%Y")

        folder_name = dic

        if is_windows():
            if not os.path.exists(f"{path}/{dic}"):

                os.makedirs(f"{path}/{dic}")
        else:
            if not os.path.exists(f"{path}/{dic}"):
                os.makedirs(f"{path}/{dic}")

        for city, name, adress, web_name in estab_data:

            # print("Gerando Arquivo ... {}.xlsx , ADDRESS : {}".format(name, adress))
            new_file = name
            if is_windows():
                file_path = "{}/{}/{}.xlsx".format(path, folder_name, new_file)
            else:
                file_path = "{}/{}/{}.xlsx".format(path, folder_name, new_file)

            products = db.db_run_query(
                "SELECT product_name, web_name, keyword, adress, price FROM search_item WHERE search_id = {} AND web_name = '{}' ORDER BY price ASC".format(
                    search_id, web_name
                )
            )

            # print("QUERY RESULTS:")
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
            # Filtra por endereço
            pattern = "|".join(adress.upper().split(" "))
            df = df[df.ENDEREÇO.str.contains(pattern, regex=True)]

            # df = df[df.ENDEREÇO.str.contains(adress.upper())]
            writer = pd.ExcelWriter(file_path, engine="openpyxl")

            df = df.to_excel(
                writer,
                sheet_name="Pesquisa",
                index=False,
                startrow=0,
                startcol=1,
                engine="openpyxl",
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

        return {"status": "success", "dic": dic}

    except:
        exc_type, exc_value, exc_tb = sys.exc_info()
        log_error(traceback.format_exception(exc_type, exc_value, exc_tb))
        return {"status": "error"}


# SocketIO
@socketio.on("reload")
def on_reload():
    state.wait_reload = True


@socketio.on("pause")
def on_pause(cancel: bool = False) -> None:
    """Rota responsável por pausar a pesquisa"""
    state.wait_reload = True

    scraper = state.scraper

    if cancel != False:
        state.cancel = True
        if scraper is not None:
            scraper.pause(True)
    else:
        if scraper is not None:
            scraper.pause()
        state.pause = True


@socketio.on("cancel")
def on_cancel():
    """Rota cancelar por pausar a pesquisa"""

    state.wait_reload = True

    db = state.db_manager
    query = "DELETE FROM search WHERE id = {}".format(state.search_id)
    db.db_run_query(query)


@socketio.on("connect")
def on_connect():
    """Quando algum cliente conecta"""
    state.connected_count += 1
    log(f"Nova conexão; total: {state.connected_count}")


@socketio.on("disconnect")
def on_disconnect():
    """Rota contas os clientes desconectados."""
    state.connected_count -= 1
    log(f"Conexão fechada; total: {state.connected_count}")

    if state.connected_count <= 0:
        if not state.wait_reload:
            log(f"Todos os clientes desconectaram; aguardando...")
            # TODO: implementar aguardar-para-fechar
            log(f"Ninguém mais se conectou - fechando o programa")
            os._exit(0)  # forçar a fechar o programa

        log(
            "Último cliente desconectou, mas `wait_reload` está ativado; aguardando nova conexão"
        )
        state.wait_reload = False


@socketio.on("set_path")
def on_set_path(config_path):
    global path
    path = config_path["path"]
    if not os.path.exists(path):
        emit("set_path", broadcast=True)


@socketio.on("exit")
def on_exit():
    os._exit(0)


# Inicia pesquisa
@socketio.on("search")
def on_search(search_info):
    """Rota responsável por iniciar a pesquisa."""

    db = state.db_manager

    search = db.db_run_query(
        "SELECT id FROM search WHERE done = 0 AND search_date = '{}' ORDER BY city_name ASC".format(
            str(date.today())
        )
    )

    search_id = search[0][0] if len(search) != 0 else None

    backup_info = db.db_get_backup(search_id)

    if len(backup_info) != 0 and search_info["backup"] == 1:

        (
            active,
            city,
            done,
            estab_info,
            product_info,
            search_id,
            duration,
            progress_value,
        ) = backup_info[0]
        estab_info = json.loads(estab_info)
        estab_names = estab_info["names"]
        estab_data = estab_info["info"]
        product = json.loads(product_info)

        if done == 0:
            emit(
                "captcha",
                {"type": "notification", "message": "Retomando pesquisa ..."},
                broadcast=True,
            )

            opts = ScraperOptions(
                locals=estab_data,
                city=city,
                locals_name=estab_names,
                product_info=product,
                active=active,
                id=search_id,
                backup=False,
                duration=duration,
                progress_value=progress_value,
            )
            scrap = Scraper(opts)

    else:

        if search_info["backup"] == 1 and len(backup_info) != 0:
            query = "DELETE FROM search WHERE id = {}".format(search_id)
            db.db_run_query(query)
        search_id = db.db_save_search(0, search_info["city"], 0)
        active = "0.0"
        city = search_info["city"]
        estab_names = json.loads(search_info["names"])
        estabs = db.db_get_estab()
        product = db.db_get_product()

        estab_data = [
            estab for estab in estabs if estab[0] == city and estab[1] in estab_names
        ]

        progress_value = 100 / len(product)

        opts = ScraperOptions(
            locals=estab_data,
            city=city,
            locals_name=estab_names,
            product_info=product,
            active=active,
            id=search_id,
            backup=False,
            duration=0,
            progress_value=progress_value,
        )
        scrap = Scraper(opts, state)

        db.db_save_backup(
            {
                "active": "0.0",
                "city": city,
                "done": 0,
                "estab_info": json.dumps({"names": estab_names, "info": estab_data}),
                "product_info": json.dumps(product),
                "search_id": search_id,
                "duration": 0,
                "progress_value": progress_value,
            }
        )

    state.scraper = scrap
    state.search_id = search_id
    state.cancel = False
    state.pause = False
    state.modified = True

    try:

        result = scrap.run()

        if not result:
            emit(
                "captcha",
                {"type": "chrome", "installed": False},
                broadcast=True,
            )
            state.cancel = True
            state.pause = True

        if not state.cancel and not state.pause:

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
            state.wait_reload = True
            # search_id = xlsx_to_bd(db, search_info["city"])

            # comentar o outro processo de aquisição de id para realizar a injeção de dados de pesquisa.
            bd_to_xlsx(db, search_id, estab_data, city)

    except Exception:

        try:
            if "error" not in search_info:
                search_info["error"] = 0
            search_info["error"] += 1
            if search_info["error"] > 3:
                emit(
                    "captcha",
                    {
                        "type": "error",
                        "message": "Ocorreram muitos erros em sucessão, a pesquisa será parada, inicie manualmente para garantir a segurança do processo.",
                    },
                    broadcast=True,
                )

                exc_type, exc_value, exc_tb = sys.exc_info()
                log_error(traceback.format_exception(exc_type, exc_value, exc_tb))

                return

        except:

            exc_type, exc_value, exc_tb = sys.exc_info()
            log_error(traceback.format_exception(exc_type, exc_value, exc_tb))
            search_info["error"] = 1

            emit(
                "captcha",
                {
                    "type": "notification",
                    "message": "Ocorreu um erro durante a pesquisa, a pesquisa será reiniciada, aguarde um instante.",
                },
                broadcast=True,
            )

            on_search(search_info)


@app.context_processor
def utility_processor():
    """Insere a função para ser chamada em todos os templates a qualquer momento"""

    def decode(text):
        return text.encode("utf8").decode("utf8")

    def replace(text, char):
        return text.replace(char, "")

    def json_stringfy(var):
        return json.dumps(var)

    return {
        "enumerate": enumerate,
        "decode": decode,
        "len": len,
        "replace": replace,
        "json_stringfy": json_stringfy,
    }


def run_app() -> None:
    """Inicia o programa com as configurações da plataforma atual, Windows ou Linux."""

    config_name = "ACCB.cfg"
    url = "http://127.0.0.1:5000"

    is_in_bundle = getattr(sys, "frozen", False)

    debug_enabled = bool(__file__)
    if debug_enabled:
        os.environ["WDM_LOCAL"] = "1"
    else:
        os.environ["WDM_LOG_LEVEL"] = "0"

    if is_port_in_use(5000):
        webbrowser.open(url)
    else:
        webbrowser.open(url)
        socketio.run(app, debug=debug_enabled)

    # Determina se a aplicação está rodando por um bundle feito pelo pyinstaller (exe) ou command line

    # if is_in_bundle:
    # application_path = os.path.dirname(sys.executable)
    # config_path = os.path.join(application_path, config_name)


if __name__ == "__main__":
    # log = logging.getLogger("werkzeug")
    # log.disabled = True

    cli = sys.modules["flask.cli"]

    # def noop(*_): pass
    # cli.show_server_banner = noop

    run_app()
