#!/usr/bin/python
# -*- coding: utf-8 -*-
""" Server da aplicação. """
# import eventlet

# eventlet.patcher.monkey_patch(select=True, socket=True)
# from engineio.async_drivers import gevent
from engineio.async_drivers import threading

"""Necessário para evitar bugs com aplicações que rodam tarefas no background."""
from flask import Flask, render_template, request, g
from flask_material import Material
from flask_socketio import SocketIO, send, emit
import time
import json
import sqlite3
import sys
import os
from werkzeug import debug
import database
import traceback
import scrapper
import pandas as pd
import webbrowser
from datetime import date
import datetime
from xlsxwriter.workbook import Workbook
import subprocess
from openpyxl.styles import Border, Side, Alignment
from tabulate import tabulate
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)
Material(app)
socketio = SocketIO(app, manage_session=False, async_mode="threading")
connected = 0
# os.environ["WDM_LOG_LEVEL"] = "0"
"""Conta os clientes conectados"""
session_data = {}
"""Armazenamento de sessão"""
session_data["software_reload"] = False
"""Responsável pelo controle de reload do programa."""
chrome_installed = None
""" Variavel indicativa da instalação do Google Chrome."""


def is_chrome_installed():

    try:

        manager = ChromeDriverManager().install()
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-features=NetworkService")
        chrome_options.add_argument("--window-size=1920x1080")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        service = Service(manager)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.close()
        driver.quit()

        if driver:
            return True
        else:
            return False

    except:

        exc_type, exc_value, exc_tb = sys.exc_info()
        log_error(traceback.format_exception(exc_type, exc_value, exc_tb))

        return False


def get_time(start):

    """Calcula o tempo de execução dado um tempo inicial e retorna o tempo em minutos horas e segundos."""
    end = time.time()
    temp = end - start
    hours = temp // 3600
    temp = temp - 3600 * hours
    minutes = temp // 60
    seconds = temp - 60 * minutes
    return {"minutes": minutes, "seconds": seconds, "hours": hours}


def print_tab(df):

    """Printa um set de dados iteráveis de forma organizada e tabulada no console."""
    print(tabulate(df, headers="keys", tablefmt="psql"))


def is_port_in_use(port):

    """Confere se uma dada porta port está em uso pelo sistema."""
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def process_exists(process_name):
    """Confere se um processo existe no sistema (windows)."""

    try:
        from subprocess import DEVNULL
    except ImportError:
        DEVNULL = os.open(os.devnull, os.O_RDWR)

    call = "TASKLIST", "/FI", "imagename eq %s" % process_name
    # use buildin check_output right away
    output = subprocess.check_output(call, stdin=DEVNULL, stderr=DEVNULL).decode(
        "latin-1"
    )
    # check in last line for process name
    last_line = output.strip().split("\r\n")[-1]

    # because Fail message could be translated
    is_app_name = last_line.lower().startswith(process_name.lower())
    instances = int(last_line.strip().split()[3])

    try:
        return not (is_app_name and instances <= 3)
        """ app_name = Nome do programa em questão. """
        """ instances = numero de processos com esse numero, no caso 1 deles é o cleaner do pyinstaller, o 2 é o nosso programa e o 3 é a instancia do driver chamado para conferir se o driver está instalado ou quando o driver é executado."""
    except:
        return False


def xlsx_to_bd(db, city_name):

    """Função para debug, injeta uma pesquisa com nome da cidade_todos.xlsx no banco de dados."""
    df = pd.read_excel("{}_todos.xlsx".format(city_name), skiprows=0, index_col=0)
    duration = get_time(time.time())
    search_id = db.db_save_search(1, city_name, duration["minutes"])

    for index, row in df.iterrows():

        name, local, keyword, adress, price = row
        # print(name, local, keyword, adress, price)

        try:
            db.db_save_search_item(
                {
                    "search_id": search_id,
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
    """Loga um erro que aconteceu durante a execução do programa no arquivo error.log"""

    with open("error.log", "w+", encoding="latin-1") as outfile:

        outfile.write("Date : {} \n".format(time.asctime()))
        for error in err:
            outfile.write(str(error))

    return


def bd_to_xlsx(db, search_id, estab_data, city):

    """Transforma uma dada pesquisa com id search_id em uma coleção de arquivos na pasta da cidade em questão (cidade) [data] [hora de geração dos arquivos]"""

    today = date.today()
    # day = today.strftime("%d-%m-%Y")
    day = datetime.datetime.now()
    day = "[{}-{}] [{}h {}m]".format(day.day, day.month, day.hour, day.minute)
    dic = "{} {}".format(city, day)

    folder_name = dic

    if not os.path.exists(dic):

        os.makedirs(dic)

    for city, name, adress, web_name in estab_data:

        # print("Geran do Arquivo ... {}.xlsx , ADDRESS : {}".format(name, adress))
        new_file = name
        if os.name == "nt":
            path = "{}\{}.xlsx".format(folder_name, new_file)
        else:
            path = "{}/{}.xlsx".format(folder_name, new_file)

        products = db.db_run_query(
            "SELECT product_name, web_name, keyword, adress, price FROM search_item WHERE search_id = {} AND web_name = '{}' ORDER BY price ASC".format(
                search_id, web_name, adress
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
        writer = pd.ExcelWriter(path, engine="openpyxl")

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


@app.route("/")
def home():
    """Rota inicial do programa, realiza os tratamentos de backup e passa as informações básicas para o estado inicial da aplicação"""

    db = database.Database()

    search_id = db.db_run_query(
        "SELECT id FROM search WHERE done = 0 AND search_date = '{}' ORDER BY city_name ASC".format(
            str(date.today())
        )
    )

    product_len = db.db_run_query("SELECT product_name FROM product")
    search = False
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
        if not len(product_len) == 0:
            progress_value = 100 / len(product_len)
        else:
            progress_value = 0
        pass

    day = datetime.datetime.now()
    search_info = db.db_run_query(
        "SELECT * FROM search WHERE done = 1 AND search_date LIKE '%%-{}-%%'".format(
            day.month
        )
    )

    # sys.exit()

    city = db.db_get_city()
    estab_names = db.db_get_estab()
    product = db.db_get_product()

    # print("CONNECTED {}".format(connected))
    # Se tiver mais que uma pagina aberta, renderiza o notallowed.html,
    # por algum motivo o flask com socketio chama a função de conexão 2x então
    # acaba ficando 0 ou 2 já que , 0 + 1 + 1 = 2
    template = "home.html" if 0 >= connected <= 2 else "notallowed.html"

    month = [
        "Janeiro",
        "Fevereiro",
        "Março",
        "Abril",
        "Maio",
        "Junho",
        "Julho",
        "Agosto",
        "Setembro",
        "Outubro",
        "Novembro",
        "Dezembro",
    ]
    return render_template(
        template,
        data=city,
        search=search,
        product="Iniciando Pesquisa",
        city=city[0][0],
        estab_names=estab_names,
        products=product,
        active=active,
        product_len=len(product_len),
        search_info=search_info,
        progress_value=progress_value,
        month=month,
        active_month=day.month,
        chrome_installed=chrome_installed,
    )


@app.route("/insert_product")
def insert_product():
    """Rota de inserção de produtos no banco de dados."""
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
    """Rota de remoção de produtos no banco de dados."""

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
    """Rota de seleção de produtos."""

    db = database.Database()
    products = db.db_get_product()

    return json.dumps([product for product in products])


@app.route("/select_search_data")
def select_search_data():
    """Rota de seleção de pesquisas no banco de dados."""

    search_id = request.args.get("search_id")
    city_name = request.args.get("city_name")
    # print(search_id)

    db = database.Database()
    search_data = db.db_run_query(
        "SELECT * FROM search JOIN search_item ON search.id = search_item.search_id AND search.id = {} AND search.done = '1' ORDER BY search_item.product_name, search_item.price ASC".format(
            search_id
        )
    )

    # print(search_data)

    return json.dumps(search_data)


@app.route("/select_search_info")
def select_search_info():

    """Rota de seleção de informação das pesquisas no banco de dados."""
    db = database.Database()
    month = request.args.get("month")

    try:

        search_data = db.db_run_query(
            "SELECT * FROM search WHERE done = 1 AND search_date LIKE '%%-{}-%%' ORDER BY city_name ASC".format(
                month
            )
        )

        return {"success": True, "data": json.dumps(search_data)}

    except sqlite3.Error as er:

        exc_type, exc_value, exc_tb = sys.exc_info()
        log_error(traceback.format_exception(exc_type, exc_value, exc_tb))

        return {
            "success": False,
        }


@app.route("/update_product")
def update_product():

    """Rota de atualização de produtos no banco de dados."""
    global session_data
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
        session_data["software_reload"] = True
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
    """Rota de seleção de estabelecimentos no banco de dados."""

    db = database.Database()
    city = request.args.get("city")
    g.estab = db.db_get_estab()
    g.estab_list = [estab for estab in g.estab if estab[0] == city]
    return json.dumps(g.estab_list)


@app.route("/remove_estab")
def remove_estab():

    """Rota de remoção de estabelecimentos no banco de dados."""
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

    """Rota de atualização de estabelecimentos no banco de dados."""
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
    """Rota de inserção de estabelecimentos no banco de dados."""

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
    """Rota de seleção de cidades no banco de dados."""

    db = database.Database()
    g.cities = db.db_get_city()
    return json.dumps(g.cities)


@app.route("/insert_city")
def insert_city():
    """Rota de inserção de cidades no banco de dados."""
    global session_data
    db = database.Database()
    city_name = request.args.get("city_name")

    try:

        db.db_save_city(city_name)
        session_data["software_reload"] = True
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
    """Rota de atualização de cidades no banco de dados."""

    global session_data
    db = database.Database()
    city_name = request.args.get("city_name")
    primary_key = request.args.get("primary_key")

    try:

        db.db_update_city({"city_name": city_name, "primary_key": primary_key})
        session_data["software_reload"] = True
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
def delete_city():
    """Rota de deleção de cidades no banco de dados."""

    global session_data
    db = database.Database()
    city_name = request.args.get("city_name")

    try:

        db.db_delete("city", "city_name", city_name)
        session_data["software_reload"] = True
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


# Gerando Arquivos


@app.route("/delete_search")
def delete_search():
    """Rota de deleção de pesquisa no banco de dados."""
    global session_data
    try:

        db = database.Database()
        search_id = request.args.get("search_id")

        db.db_delete("search", "id", search_id)
        session_data["software_reload"] = True
        return {"status": "success", "message": "Pesquisa deletada com sucesso."}

    except:
        exc_type, exc_value, exc_tb = sys.exc_info()
        log_error(traceback.format_exception(exc_type, exc_value, exc_tb))
        return {
            "status": "error",
            "message": "Ocorreu um erro durante a deleção da pesquisa, mais detalhes no arquivo err.log.",
        }


@app.route("/export_database")
def export_database():
    """Rota responsável por exportar os dados do banco"""
    try:
        db = database.Database()
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
def import_database():
    """Rota responsável por importar os dados do banco"""
    global session_data
    try:
        db = database.Database()
        file = request.files["file"]
        db.import_database(file)

        session_data["software_reload"] = True
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


@app.route("/generate_file")
def bd_to_xlsx_route():

    """Rota geradora de coleção de dados das pesquisas em excel."""
    db = database.Database()

    try:
        city = request.args.get("city_name")
        estab_names = json.loads(request.args.get("names"))
        estabs = db.db_get_estab()
        product = db.db_get_product()
        search_id = request.args.get("search_id")

        estab_data = [
            estab for estab in estabs if estab[0] == city and estab[1] in estab_names
        ]

        # day = today.strftime("%d-%m-%Y")
        day = datetime.datetime.now()
        day = "[{}-{}] [{}h {}m]".format(day.day, day.month, day.hour, day.minute)
        dic = "{} {}".format(city, day)

        folder_name = dic

        if not os.path.exists(dic):

            os.makedirs(dic)

        for city, name, adress, web_name in estab_data:

            # print("Geran do Arquivo ... {}.xlsx , ADDRESS : {}".format(name, adress))
            new_file = name
            if os.name == "nt":
                path = "{}\{}.xlsx".format(folder_name, new_file)
            else:
                path = "{}/{}.xlsx".format(folder_name, new_file)

            products = db.db_run_query(
                "SELECT product_name, web_name, keyword, adress, price FROM search_item WHERE search_id = {} AND web_name = '{}' ORDER BY price ASC".format(
                    search_id, web_name, adress
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
            writer = pd.ExcelWriter(path, engine="openpyxl")

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
def handle_reload():
    """Rota responsável por controlar a variavel de reload."""
    global session_data
    session_data["software_reload"] = True


@socketio.on("pause")
def handle_pause(cancel=False):
    """Rota responsável por pausar a pesquisa"""
    global session_data

    if cancel != False:
        # Cancela
        session_data["cancel"] = True
        session_data["scrap"].pause(True)
    else:
        session_data["scrap"].pause()
        session_data["pause"] = True


@socketio.on("cancel")
def handle_cancel():
    """Rota cancelar por pausar a pesquisa"""

    global session_data
    # log_error([session_data])

    db = database.Database()
    query = "DELETE FROM search WHERE id = {}".format(session_data["search_id"])
    db.db_run_query(query)


@socketio.on("connect")
def connect():
    """Rota contas os clientes conectados."""
    global connected
    connected += 1
    print("connnected {}".format(connected))


@socketio.on("disconnect")
def disconnect():
    """Rota contas os clientes desconectados."""
    global connected
    global session_data
    connected -= 1
    # print("disconnnected {}".format(connected))
    if connected == 0 and not session_data["software_reload"]:
        log_error([connected, session_data])
        os._exit(0)
    else:
        try:

            if session_data["software_reload"] and connected == 0:

                session_data["software_reload"] = False
                log_error([connected, session_data])

        except:

            pass


# Inicia pesquisa
@socketio.on("search")
def handle_search(search_info):
    """Rota responsável por iniciar a pesquisa."""

    db = database.Database()

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
            scrap = scrapper.Scrap(
                estab_data,
                city,
                estab_names,
                product,
                active,
                search_id,
                False,
                duration,
                progress_value,
            )

    else:

        if search_info["backup"] == 1 and len(backup_info) != 0:
            query = "DELETE FROM search WHERE id = {}".format(search_id)
            db.db_run_query(query)
        # comentar para injeção
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
        # comentar para injeção
        scrap = scrapper.Scrap(
            estab_data,
            city,
            estab_names,
            product,
            active,
            search_id,
            False,
            0,
            progress_value,
        )

        # comentar para injeção
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

    global session_data
    # comentar para injeção
    session_data["scrap"] = scrap
    session_data["search_id"] = search_id
    session_data["cancel"] = False
    session_data["pause"] = False
    session_data["modified"] = True

    try:

        # comentar para injeção
        is_chrome_installed = scrap.run()

        # comentar para injeção
        if not is_chrome_installed:

            emit(
                "captcha",
                {"type": "chrome", "installed": False},
                broadcast=True,
            )
            session_data["cancel"] = True
            session_data["pause"] = True

        if not session_data["cancel"] and not session_data["pause"]:

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
            session_data["software_reload"] = True
            # search_id = xlsx_to_bd(db, search_info["city"])
            """Comentar o outro processo de aquisição de id para realizar a injeção de dados de pesquisa."""

            bd_to_xlsx(db, search_id, estab_data, city)

    except:

        emit(
            "captcha",
            {"type": "notification", "message": "Ocorreu um erro durante a pesquisa."},
            broadcast=True,
        )
        exc_type, exc_value, exc_tb = sys.exc_info()
        log_error(traceback.format_exception(exc_type, exc_value, exc_tb))


@app.context_processor
def utility_processor():
    """Insere a função para ser chamada em todos os templates a qualquer momento"""

    def decode(text):
        return text.encode("utf8").decode("utf8")

    def replace(text, char):
        return text.replace(char, "")

    def json_stringfy(var):
        return json.dumps(var)

    return dict(
        enumerate=enumerate,
        decode=decode,
        len=len,
        replace=replace,
        json_stringfy=json_stringfy,
    )


def run_app():
    """Inicia o programa com as configurações da plataforma atual, windows ou linux."""
    config_name = "ACCB.cfg"
    url = "http://127.0.0.1:5000"
    global chrome_installed

    # Determina se a aplicação está rodando por um bundle feito pelo pyinstaller (exe) ou command line
    if getattr(sys, "frozen", False):
        application_path = os.path.dirname(sys.executable)
        config_path = os.path.join(application_path, config_name)
        # windows
        if os.name == "nt":
            if not process_exists("ACCB.exe"):
                os.environ["WDM_LOCAL"] = "1"
                chrome_installed = str(is_chrome_installed())
                webbrowser.open(url)
                # eventlet.wsgi.server(
                #     eventlet.listen(("127.0.0.1", 5000)), app, debug=False
                # )
                socketio.run(app, debug=False)
            else:
                webbrowser.open(url)
        else:
            # por motivos especificos não conseguimos utilizar a mesma lógica no linux, então se a porta tiver em uso assumimos que o programa está aberto
            if not is_port_in_use(5000):
                os.environ["WDM_LOCAL"] = "1"
                chrome_installed = str(is_chrome_installed())
                webbrowser.open(url)
                # eventlet.wsgi.server(
                #     eventlet.listen(("127.0.0.1", 5000)), app, debug=False
                # )
                socketio.run(app, debug=False)
            else:
                webbrowser.open(url)

    elif __file__:
        # DEV
        application_path = os.path.dirname(__file__)
        config_path = os.path.join(application_path, config_name)
        # windows
        if os.name == "nt":
            os.environ["WDM_LOCAL"] = "1"
            chrome_installed = str(is_chrome_installed())
            webbrowser.open(url)
            # eventlet.wsgi.server(
            #     eventlet.listen(("127.0.0.1", 5000)), app, debug=True
            # )
            socketio.run(app, debug=True)
        else:
            # os.environ["WDM_LOCAL"] = "1"
            webbrowser.open(url)
            # eventlet.wsgi.server(
            #     eventlet.listen(("127.0.0.1", 5000)), app, debug=True
            # )
            socketio.run(app, debug=True)


if __name__ == "__main__":

    # run_app()
    run_app()
