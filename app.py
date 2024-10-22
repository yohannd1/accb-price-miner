"""Ponto de entrada da aplicação."""

from threading import Thread, Lock, Timer


def before_anything() -> None:
    from tkinter.messagebox import showwarning

    showwarning("ACCB", "Carregando. Por favor aguarde...")


if __name__ == "__main__":
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
from datetime import date
import traceback
import webbrowser
import subprocess
from pathlib import Path
import socket

from flask import Flask, render_template, request, g, Response
from flask_material import Material
from flask_socketio import SocketIO, emit

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
    get_time_filename,
    open_folder,
)
from accb.state import State
from accb.consts import MONTHS_PT_BR
from accb.web_driver import is_chrome_installed
from accb.database import DatabaseManager
from accb.excel import db_to_xlsx, db_to_xlsx_all, export_to_xlsx

app = Flask(__name__)
Material(app)
socketio = SocketIO(app, manage_session=False, async_mode="threading")

state = State(
    db_manager=DatabaseManager(),
)

watchdog_lock = Lock()
watchdog = None


path = None
"""Variável de caminho padrão para gerar coleção excel."""


def is_port_in_use(port):
    """Confere se uma dada porta port está em uso pelo sistema."""

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


@app.route("/")
def route_home():
    """Rota inicial do programa, realiza os tratamentos de backup e passa as informações básicas para o estado inicial da aplicação"""

    db = state.db_manager

    search_id = db.db_run_query(
        "SELECT id FROM search WHERE done = 0 AND search_date = ? ORDER BY city_name ASC",
        (str(date.today()),),
    )
    log(f"{search_id=}")

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

    except Exception:  # FIXME: remove this except
        exc_type, exc_value, exc_tb = sys.exc_info()
        log_error(traceback.format_exception(exc_type, exc_value, exc_tb))

        if not len(product_names) == 0:
            progress_value = 100 / len(product_names)

    day = str(date.today()).split("-")[1]
    search_info = db.db_run_query(
        "SELECT * FROM search WHERE done = 1 AND search_date LIKE ?",
        (f"%%-{day}-%%",),
    )

    search_years = db.db_run_query(
        "SELECT DISTINCT SUBSTR(search_date, '____', 5) FROM search WHERE done = 1"
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
def route_insert_product() -> dict:
    """Rota de inserção de produtos no banco de dados."""

    product_name = request.args["product_name"]

    state.db_manager.db_save_product(
        product_name=product_name,
        keywords=request.args["keywords"],
    )

    return {
        "status": "success",
        "message": f"O produto {product_name} foi inserido com sucesso",
    }


@app.errorhandler(Exception)
def all_exception_handler(error):
    res = {"status": "error", "message": "Erro interno da aplicação"}
    return Response(status=200, mimetype="application/json", response=json.dumps(res))


@app.route("/remove_product")
def route_remove_product():
    """Rota de remoção de produtos no banco de dados."""

    product_name = request.args.get("product_name")
    state.db_manager.db_delete("product", "product_name", product_name)

    return {
        "success": True,
        "message": f"O produto {product_name} foi removido com sucesso",
    }


@app.route("/select_product")
def route_select_product():
    """Rota de seleção de produtos."""

    products = state.db_manager.db_get_product()
    return json.dumps(products)


@app.route("/select_search_data")
def route_select_search_data():
    """Rota de seleção de pesquisas no banco de dados."""

    search_id = request.args.get("search_id")
    city_name = request.args.get("city_name")

    search_data = state.db_manager.db_run_query(
        "SELECT * FROM search JOIN search_item ON search.id = search_item.search_id AND search.id = ? AND search.done = '1' ORDER BY search_item.product_name, search_item.price ASC",
        (search_id,),
    )

    return json.dumps(search_data)


@app.route("/select_search_info")
def route_select_search_info() -> dict:
    """Rota de seleção de informação das pesquisas no banco de dados."""

    db = state.db_manager

    month = request.args["month"]
    year = request.args.get("year")

    if year is None:
        month = "0" + month if int(month) < 10 else month
        search_data = db.db_run_query(
            "SELECT * FROM search WHERE done = 1 AND search_date LIKE ? ORDER BY city_name ASC",
            (f"%-{month}-%",),
        )
    else:
        search_data = db.db_run_query(
            "SELECT * FROM search WHERE done = 1 AND search_date LIKE ? ORDER BY city_name ASC",
            (f"{year}%",),
        )

    return {"status": "success", "data": search_data}


@app.route("/update_product")
def route_update_product() -> dict:
    """Rota de atualização de produtos no banco de dados."""

    product_name = request.args.get("product_name")
    keywords = request.args.get("keywords")
    primary_key = request.args.get("primary_key")

    state.db_manager.db_update_product(
        {
            "product_name": product_name,
            "keywords": keywords,
            "primary_key": primary_key,
        }
    )
    state.wait_reload = True
    return {
        "status": "success",
        "message": f"O produto {primary_key} foi atualizado com sucesso",
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
def route_remove_estab() -> dict:
    """Rota de remoção de estabelecimentos no banco de dados."""

    estab_name = request.args["estab_name"]

    state.db_manager.db_delete("estab", "estab_name", estab_name)
    return {
        "status": "success",
        "message": f"O estabelecimento {estab_name} foi removido com sucesso",
    }


@app.route("/update_estab")
def route_update_estab() -> dict:
    """Rota de atualização de estabelecimentos no banco de dados."""

    city_name = request.args["city_name"]
    estab_name = request.args["estab_name"]
    primary_key = request.args["primary_key"]
    web_name = request.args["web_name"]
    adress = request.args["adress"]

    state.db_manager.db_update_estab(
        {
            "primary_key": primary_key,
            "city_name": city_name,
            "estab_name": estab_name,
            "web_name": web_name,
            "adress": adress,
        }
    )

    return {
        "status": "success",
        "message": f"O estabelecimento {estab_name} foi atualizado com sucesso",
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
def route_update_city() -> dict:
    """Rota de atualização de cidades no banco de dados."""

    city_name = request.args["city_name"]
    primary_key = request.args["primary_key"]
    state.db_manager.db_update_city({"city_name": city_name, "primary_key": primary_key})
    state.wait_reload = True

    return {
        "status": "success",
        "message": f"A cidade {city_name} foi editada com sucesso",
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
def route_set_path() -> dict:
    global path

    directory = ask_user_directory()
    if directory is None:
        raise Exception("Nenhum diretório selecionado")

    path = directory
    Path(path).mkdir(exist_ok=True)

    return {
        "status": "success",
        "message": "Caminho configurado com sucesso.",
        "path": path,
    }


# Gerando Arquivos
@app.route("/delete_search")
def route_delete_search() -> dict:
    """Rota de deleção de pesquisa no banco de dados."""

    search_id = request.args["search_id"]

    state.db_manager.db_delete("search", "id", search_id)
    state.wait_reload = True
    return {"status": "success", "message": "Pesquisa deletada com sucesso."}


@app.route("/export_database")
def route_export_database() -> dict:
    """Rota responsável por exportar os dados do banco"""

    OUTPUT_FILENAME = "importar.sql"
    TABLES = ("city", "estab", "product")

    db = state.db_manager
    with open(OUTPUT_FILENAME, "w+") as f:
        for table in TABLES:
            for line in db.dump_table(table):
                f.write(f"{line}\n")

    return {
        "status": "success",
        "message": "Dados exportados com sucesso - agora é possível importá-lo em outro computador com o arquivo 'importar.sql'.",
    }

@app.route("/import_database", methods=["POST"])
def route_import_database() -> dict:
    """Rota responsável por importar os dados do banco"""

    file = request.files["file"]
    state.db_manager.import_database(file)

    state.wait_reload = True
    return {
        "status": "success",
        "message": "Dados importados com sucesso.",
    }


@app.route("/open_folder")
def route_open_folder() -> dict:
    path = request.args["path"]
    open_folder(Path(path))
    return {"status": "success"}


@app.route("/clean_search")
def route_clean_search():
    """Rota que deleta todas as pesquisas e ou gera coleção de deletar as mesmas."""

    global path
    db = state.db_manager

    generate = request.args.get("generate") == "true"

    response = {"status": "success"}

    if generate:
        limpeza_path = Path(path) / "Limpeza"

        for city_name, *_ in db.db_get_city():
            estab_data = db.db_run_query(
                "SELECT * FROM estab WHERE city_name = ?", (city_name,)
            )
            search_info = db.db_run_query(
                "SELECT DISTINCT id,search_date FROM search WHERE done = 1"
            )

            for search_id, search_date in search_info:
                output_folder = limpeza_path / search_date
                output_folder.mkdir(parents=True, exist_ok=True)

                for _, name, adress, web_name in estab_data:
                    output_path = output_folder / f"{name}.xlsx"

                    export_to_xlsx(
                        db=db,
                        search_id=search_id,
                        filter_by_address=False,
                        output_path=output_path,
                        web_name=web_name,
                        adress=adress,
                    )

        response["message"] = (
            f"Pesquisas deletadas com sucesso. Conteúdo gerado disponível em {limpeza_path}."
        )
        response["path"] = str(limpeza_path)
    else:
        response["message"] = "Pesquisas deletadas com sucesso."

    db.db_run_query("DELETE FROM search_item")
    db.db_run_query("DELETE FROM search")

    return response


@app.route("/generate_file")
def route_generate_file() -> dict:
    """Gera arquivo(s) excel com os dados das pesquisas."""

    db = state.db_manager
    global path

    format_type = request.args.get("format")
    city = request.args.get("city_name")
    search_id = request.args.get("search_id")

    if format_type == "all":
        output_folder = db_to_xlsx_all(city, search_id, db, path)
        return {"status": "success", "path": str(output_folder)}

    names = request.args.get("names")
    assert names is not None

    estab_names = json.loads(names)
    estabs = db.db_get_estab()
    product = db.db_get_product()

    estab_data = [e for e in estabs if e[0] == city and e[1] in estab_names]

    output_folder = db_to_xlsx(db, search_id, estab_data, city, path)
    return {"status": "success", "path": str(output_folder)}


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
def on_cancel() -> dict:
    """Rota responsável por pausar a pesquisa"""

    state.wait_reload = True
    state.db_manager.db_run_query("DELETE FROM search WHERE id = ?", (state.search_id,))

    return response_ok()


def response_ok() -> dict:
    return {"status": "success"}


@socketio.on("connect")
def on_connect():
    """Quando algum cliente conecta"""
    global watchdog

    state.connected_count += 1
    log(f"Nova conexão; total: {state.connected_count}")

    with watchdog_lock:
        if watchdog is not None:
            log(f"Cancelando timeout para fechar o programa")
            watchdog.cancel()
            watchdog = None


@socketio.on("disconnect")
def on_disconnect():
    """Rota contas os clientes desconectados."""
    global watchdog

    state.connected_count -= 1
    log(f"Conexão fechada; total: {state.connected_count}")

    WATCHDOG_TIMEOUT = 8

    def timeout_exit() -> None:
        log(f"Ninguém mais se conectou - fechando o programa")
        os._exit(0)  # forçar a fechar o programa

    if state.connected_count <= 0:
        if state.wait_reload:
            state.wait_reload = False
        else:
            log(
                f"Todos os clientes desconectaram; esperando uma nova conexão por {WATCHDOG_TIMEOUT} segundos..."
            )
            with watchdog_lock:
                watchdog = Timer(8, timeout_exit)
                watchdog.start()


@socketio.on("set_path")
def on_set_path(config_path):
    # TODO: should this be here? and should it emit set_path back? it's confusing
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
        "SELECT id FROM search WHERE done = 0 AND search_date = ? ORDER BY city_name ASC",
        (str(date.today()),),
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
            scrap = Scraper(opts, state)

    else:
        if search_info["backup"] == 1 and len(backup_info) != 0:
            db.db_run_query("DELETE FROM search WHERE id = ?", (search_id,))
        search_id = db.db_save_search(0, search_info["city"], 0)
        active = "0.0"
        city = search_info["city"]
        estab_names = json.loads(search_info["names"])
        estabs = db.db_get_estab()
        product = db.db_get_product()

        estab_data = [e for e in estabs if e[0] == city and e[1] in estab_names]

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
            db_to_xlsx(db, search_id, estab_data, city, path)

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
        except Exception:
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


def main() -> None:
    """Inicia o programa com as configurações da plataforma atual, Windows ou Linux."""

    SERVER_URL = "http://127.0.0.1:5000"

    is_in_bundle = getattr(sys, "frozen", False)
    debug_enabled = bool(__file__) and not is_in_bundle
    if debug_enabled:
        os.environ["WDM_LOCAL"] = "1"
    else:
        os.environ["WDM_LOG_LEVEL"] = "0"

    # TODO: configurar o arquivo de log

    webbrowser.open(SERVER_URL)
    if not is_port_in_use(5000):
        socketio.run(app, debug=debug_enabled, use_reloader=False)

if __name__ == "__main__":
    # log = logging.getLogger("werkzeug")
    # log.disabled = True

    # cli = sys.modules["flask.cli"]
    # def noop(*_): pass
    # cli.show_server_banner = noop

    main()
