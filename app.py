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

import json
import sys
import os
from datetime import date
import traceback
import webbrowser
from pathlib import Path
import socket

from flask import Flask, render_template, request, g, Response
from flask_material import Material
from flask_socketio import SocketIO, emit

# from webdriver_manager.chrome import ChromeDriverManager
# from webdriver_manager.core.driver_cache import DriverCacheManager

from accb.scraper import Scraper, ScraperOptions
from accb.utils import (
    log,
    log_error,
    ask_user_directory,
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

state = State(db_manager=DatabaseManager())

watchdog_lock = Lock()
watchdog = None


def is_port_in_use(port) -> bool:
    """Confere se uma dada porta port está em uso pelo sistema."""

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


@app.route("/")
def route_home() -> str:
    """Rota inicial do programa, realiza os tratamentos de backup e passa as informações básicas para o estado inicial da aplicação"""

    db = state.db_manager

    product_names = db.run_query("SELECT product_name FROM product")
    search = False
    active = "0.0"

    search_id = db.get_incomplete_search_id()
    backup_info = db.get_backup(search_id)
    if backup_info is None:
        search = False
    else:
        (_, _, done, *_) = backup_info
        search = done == 0

    day = str(date.today()).split("-")[1]
    args = db.run_query(
        "SELECT * FROM search WHERE done = 1 AND search_date LIKE ?",
        (f"%%-{day}-%%",),
    )

    search_years = db.run_query(
        "SELECT DISTINCT SUBSTR(search_date, '____', 5) FROM search WHERE done = 1"
    )

    city = db.get_city()
    estab_names = db.get_estab()
    product = db.get_product()

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
        month=MONTHS_PT_BR,
        active_month=day,
        active_year=str(date.today()).split("-", maxsplit=1)[0],
        chrome_installed=str(is_chrome_installed()),
        years=search_years,
    )


@app.route("/insert_product")
def route_insert_product() -> dict:
    """Rota de inserção de produtos no banco de dados."""

    product_name = request.args["product_name"]

    state.db_manager.save_product(
        product_name=product_name,
        keywords=request.args["keywords"],
    )

    return {
        "status": "success",
        "message": f"O produto {product_name} foi inserido com sucesso",
    }


@app.errorhandler(Exception)
def all_exception_handler(_exc: Exception) -> Response:
    res = {"status": "error", "message": "Erro interno da aplicação"}
    return Response(status=200, mimetype="application/json", response=json.dumps(res))


@app.route("/remove_product")
def route_remove_product() -> dict:
    """Rota de remoção de produtos no banco de dados."""

    product_name = request.args.get("product_name")
    state.db_manager.delete("product", "product_name", product_name)

    return {
        "status": "success",
        "message": f"O produto {product_name} foi removido com sucesso",
    }


@app.route("/select_product")
def route_select_product() -> str:
    """Rota de seleção de produtos."""

    products = state.db_manager.get_product()
    return json.dumps(products)


@app.route("/select_search_data")
def route_select_search_data() -> str:
    """Rota de seleção de pesquisas no banco de dados."""

    search_id = request.args["search_id"]

    search_data = state.db_manager.run_query(
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
        search_data = db.run_query(
            "SELECT * FROM search WHERE done = 1 AND search_date LIKE ? ORDER BY city_name ASC",
            (f"%-{month}-%",),
        )
    else:
        search_data = db.run_query(
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

    state.db_manager.update_product(
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
def route_select_estab() -> str:
    """Rota de seleção de estabelecimentos no banco de dados."""

    db = state.db_manager
    city = request.args.get("city")
    g.estab = db.get_estab()
    g.estab_list = [estab for estab in g.estab if estab[0] == city]
    return json.dumps(g.estab_list)


@app.route("/remove_estab")
def route_remove_estab() -> dict:
    """Rota de remoção de estabelecimentos no banco de dados."""

    estab_name = request.args["estab_name"]

    state.db_manager.delete("estab", "estab_name", estab_name)
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

    state.db_manager.update_estab(
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
def route_insert_estab() -> dict:
    """Rota de inserção de estabelecimentos no banco de dados."""

    db = state.db_manager
    city_name = request.args["city_name"]
    estab_name = request.args["estab_name"]
    web_name = request.args["web_name"]
    adress = request.args["adress"]

    db.save_estab(
        {
            "city_name": city_name,
            "estab_name": estab_name,
            "web_name": web_name,
            "adress": adress,
        }
    )

    return {
        "status": "success",
        "message": f"O estabelecimento {estab_name} foi adicionado com sucesso",
    }


@app.route("/select_city")
def route_select_city() -> str:
    """Rota de seleção de cidades no banco de dados."""

    db = state.db_manager
    g.cities = db.get_city()
    return json.dumps(g.cities)


@app.route("/insert_city")
def route_insert_city() -> dict:
    """Rota de inserção de cidades no banco de dados."""
    db = state.db_manager
    city_name = request.args.get("city_name")

    db.save_city(city_name)
    state.wait_reload = True
    return {
        "status": "success",
        "message": f"A cidade {city_name} foi adicionada com sucesso",
    }


@app.route("/update_city")
def route_update_city() -> dict:
    """Rota de atualização de cidades no banco de dados."""

    city_name = request.args["city_name"]
    primary_key = request.args["primary_key"]
    state.db_manager.update_city({"city_name": city_name, "primary_key": primary_key})
    state.wait_reload = True

    return {
        "status": "success",
        "message": f"A cidade {city_name} foi editada com sucesso",
    }


@app.route("/delete_city")
def route_delete_city() -> dict:
    """Rota de deleção de cidades no banco de dados."""

    db = state.db_manager
    city_name = request.args["city_name"]

    db.delete("city", "city_name", city_name)
    state.wait_reload = True
    return {
        "status": "success",
        "message": f"A cidade {city_name} foi deletada com sucesso",
    }


@app.route("/ask_output_path")
def route_ask_output_path() -> dict:
    state.output_path = ask_user_directory()
    if state.output_path is None:
        raise Exception("Nenhum diretório selecionado")

    state.output_path.mkdir(exist_ok=True)

    return {
        "status": "success",
        "message": "Caminho configurado com sucesso.",
        "path": str(state.output_path),
    }


# Gerando Arquivos
@app.route("/delete_search")
def route_delete_search() -> dict:
    """Rota de deleção de pesquisa no banco de dados."""

    search_id = request.args["search_id"]

    state.db_manager.delete("search", "id", search_id)
    state.wait_reload = True
    return {"status": "success", "message": "Pesquisa deletada com sucesso."}


@app.route("/export_database")
def route_export_database() -> dict:
    """Rota responsável por exportar os dados do banco"""

    OUTPUT_FILENAME = "importar.sql"
    TABLES = ("city", "estab", "product")
    ENCODING = "utf-8"

    db = state.db_manager
    with open(OUTPUT_FILENAME, "w+", encoding=ENCODING) as f:
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
    open_folder(Path(request.args["path"]))
    return {"status": "success"}


@app.route("/clean_search")
def route_clean_search() -> dict:
    """Rota que deleta todas as pesquisas e ou gera coleção de deletar as mesmas."""

    assert state.output_path is not None

    db = state.db_manager

    generate = request.args.get("generate") == "true"

    response = {"status": "success"}

    if generate:
        limpeza_path = state.output_path / "Limpeza"

        for city_name, *_ in db.get_city():
            estab_data = db.run_query(
                "SELECT * FROM estab WHERE city_name = ?", (city_name,)
            )
            args = db.run_query(
                "SELECT DISTINCT id,search_date FROM search WHERE done = 1"
            )

            for search_id, search_date in args:
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

    db.run_query("DELETE FROM search_item")
    db.run_query("DELETE FROM search")

    return response


@app.route("/generate_file")
def route_generate_file() -> dict:
    """Gera arquivo(s) excel com os dados das pesquisas."""

    assert state.output_path is not None

    db = state.db_manager

    format_type = request.args.get("format")
    city = request.args.get("city_name")
    search_id = request.args.get("search_id")

    if format_type == "all":
        output_folder = db_to_xlsx_all(city, search_id, db, state.output_path)
        return {"status": "success", "path": str(output_folder)}

    names = request.args.get("names")
    assert names is not None

    estab_names = json.loads(names)
    estabs = db.get_estab()

    estab_data = [e for e in estabs if e[0] == city and e[1] in estab_names]

    output_folder = db_to_xlsx(db, search_id, estab_data, city, state.output_path)
    return {"status": "success", "path": str(output_folder)}


@socketio.on("pause")
def on_pause() -> dict:
    """Pausa a pesquisa atual, mantendo seu estado no banco de dados."""

    state.wait_reload = True

    state.pause = True
    state.cancel = False

    assert state.scraper is not None
    state.scraper.pause(cancel=False)

    return {"status": "success"}


@socketio.on("cancel")
def on_cancel() -> dict:
    """Cancela a pesquisa atual e deleta os dados dela no banco de dados."""

    state.wait_reload = True

    state.db_manager.run_query("DELETE FROM search WHERE id = ?", (state.search_id,))

    state.pause = False
    state.cancel = True

    assert state.scraper is not None
    state.scraper.pause(cancel=True)

    if state.search_id is None:
        return {"status": "error"}

    return {"status": "success"}


@socketio.on("connect")
def on_connect() -> None:
    """Quando algum cliente conecta"""
    global watchdog

    state.connected_count += 1
    log(f"Nova conexão; total: {state.connected_count}")

    with watchdog_lock:
        if watchdog is not None:
            log("Cancelando timeout para fechar o programa")
            watchdog.cancel()
            watchdog = None


@socketio.on("disconnect")
def on_disconnect() -> None:
    """Rota contas os clientes desconectados."""
    global watchdog

    state.connected_count -= 1
    log(f"Conexão fechada; total: {state.connected_count}")

    WATCHDOG_TIMEOUT = 8

    def timeout_exit() -> None:
        log("Ninguém mais se conectou - fechando o programa")
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


@socketio.on("output_path_from_cookies")
def on_path_from_cookies(args: dict) -> None:
    path = args.get("path")
    is_valid = path is not None and Path(path).exists()

    if not is_valid:
        emit("invalid_output_path", broadcast=True)

    # TODO: should this be here? and should it emit set_path back? it's confusing
    state.output_path = Path(args["path"])
    assert state.output_path is not None
    if not state.output_path.exists():
        emit("set_path", broadcast=True)


@socketio.on("exit")
def on_exit() -> None:
    os._exit(0)


def attempt_search(args: dict) -> None:
    """Inicia a pesquisa."""

    db = state.db_manager
    assert state.output_path is not None

    search_id = db.get_incomplete_search_id()

    is_backup = args["is_backup"]
    backup_info = db.get_backup(search_id) if is_backup else None

    if backup_info is not None:
        (_, _, done, *_) = backup_info
        if done == 1:
            emit("showNotification", "A pesquisa já estava finalizada.", broadcast=True)
            # TODO: salvar a pesquisa do backup?
            return

        emit("showNotification", "Retomando pesquisa...", broadcast=True)
        opts = ScraperOptions.from_backup_info(backup_info)
        scrap = Scraper(opts, state)

        estab_data = opts.locals
    else:
        city = args["city"]
        search_id = db.save_search(False, city, 0)
        active = "0.0"
        estab_names = json.loads(args["names"])
        estabs = db.get_estab()
        product = db.get_product()
        duration = 0

        estab_data = [
            (e_city, e_estab, *e_rest)
            for (e_city, e_estab, *e_rest) in estabs
            if e_city == city and e_estab in estab_names
        ]

        opts = ScraperOptions(
            locals=estab_data,
            city=city,
            locals_name=estab_names,
            product_info=product,
            active=active,
            id=search_id,
            backup=False,
            duration=duration,
        )
        opts.save_as_backup(db=db, is_done=False)
        scrap = Scraper(opts, state)

    state.scraper = scrap
    state.search_id = search_id
    state.cancel = False
    state.pause = False

    success = scrap.run()
    if not success:
        state.cancel = True
        state.pause = True

    if not state.cancel and not state.pause:
        emit("showNotification", "Pesquisa concluída.", broadcast=True)

        emit(
            "captcha",
            {"type": "progress", "done": 1},
            broadcast=True,
        )
        state.wait_reload = True

        # comentar o outro processo de aquisição de id para realizar a injeção de dados de pesquisa.
        db_to_xlsx(db, search_id, estab_data, city, state.output_path)


@socketio.on("search")
def on_search(args: dict) -> None:
    error_count = 0

    while True:
        try:
            attempt_search(args)
        except Exception:
            exc_type, exc_value, exc_tb = sys.exc_info()
            log_error(traceback.format_exception(exc_type, exc_value, exc_tb))

            error_count += 1

            if error_count >= 4:
                emit(
                    "captcha.error",
                    "Ocorreram muitos erros em sucessão. Para segurança do processo, a pesquisa será parada - inicie manualmente para tentar novamente.",
                    broadcast=True,
                )
                return

            emit(
                "showNotification",
                "Ocorreu um erro durante a pesquisa; ela será reiniciada, aguarde um instante.",
                broadcast=True,
            )


@app.context_processor
def utility_processor() -> dict:
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
    log(f"{is_in_bundle=}; {debug_enabled=}")

    if debug_enabled:
        os.environ["WDM_LOCAL"] = "1"
    else:
        os.environ["WDM_LOG_LEVEL"] = "0"

    # TODO: configurar o arquivo de log

    webbrowser.open(SERVER_URL)
    if not is_port_in_use(5000):
        socketio.run(app, debug=debug_enabled, use_reloader=False)


if __name__ == "__main__":
    # cli = sys.modules["flask.cli"]
    # def noop(*_): pass
    # cli.show_server_banner = noop

    main()
