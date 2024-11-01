import json
import sys
import os
from datetime import date
import traceback
import webbrowser
from pathlib import Path
import socket
from threading import Timer
from queue import Queue
from typing import Any

from flask import Flask, render_template, request, g, Response
from flask_material import Material
from flask_socketio import SocketIO, emit

from accb.scraper import Scraper, ScraperOptions
from accb.utils import (
    log,
    log_error,
    ask_user_directory,
    open_folder,
)
from accb.restartable_timer import RestartableTimer
from accb.locked_var import LockedVar
from accb.state import State
from accb.consts import MONTHS_PT_BR
from accb.web_driver import is_chrome_installed
from accb.database import DatabaseManager
from accb.bi_queue import BiQueue

app = Flask(__name__)
Material(app)
socketio = SocketIO(app, manage_session=False, async_mode="threading")

state = State(db_manager=DatabaseManager())

SERVER_URL = "http://127.0.0.1"
PORT = 5000
ENCODING = "utf-8"
WATCHDOG_TIMEOUT = 8


def timeout_exit() -> None:
    log("Ninguém mais se conectou - fechando o programa")
    os._exit(0)  # forçar a fechar o programa


watchdog = LockedVar(RestartableTimer(WATCHDOG_TIMEOUT, timeout_exit))


def export_thread(recv: Queue, send: Queue) -> None:
    from accb.excel import db_to_xlsx, db_to_xlsx_all, export_to_xlsx

    shutdown = False
    while not shutdown:
        result: Any
        match recv.get():
            case ("db_to_xlsx", args, kwargs):
                result = db_to_xlsx(*args, **kwargs)
            case ("db_to_xlsx_all", args, kwargs):
                result = db_to_xlsx_all(*args, **kwargs)
            case ("export_to_xlsx", args, kwargs):
                export_to_xlsx(*args, **kwargs)
                result = None
            case "shutdown":
                shutdown = True
                result = None
            case _:
                result = None
        send.put(result)


export_bq = BiQueue(export_thread)


def db_to_xlsx(*args, **kwargs):
    return export_bq.exchange(("db_to_xlsx", args, kwargs))


def db_to_xlsx_all(*args, **kwargs):
    return export_bq.exchange(("db_to_xlsx_all", args, kwargs))


def export_to_xlsx(*args, **kwargs):
    return export_bq.exchange(("export_to_xlsx", args, kwargs))


def is_port_in_use(port) -> bool:
    """Confere se uma dada porta port está em uso pelo sistema."""

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


@app.errorhandler(Exception)
def exception_handler(exc: Exception) -> Response:
    # TODO: encontrar uma maneira de usar isso ao invés do debugger padrão

    fmt = "".join(traceback.format_exception(exc))
    log(f"Erro interno: {exc} -- {fmt}")
    res = {"status": "error", "message": "Erro interno da aplicação"}
    return Response(status=200, mimetype="application/json", response=json.dumps(res))


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
        has_backup = False
    else:
        (_, _, done, *_) = backup_info
        has_backup = done == 0

    day = str(date.today()).split("-")[1]
    search_info = db.run_query(
        "SELECT * FROM search WHERE done = 1 AND search_date LIKE ?",
        (f"%%-{day}-%%",),
    )

    search_years = db.run_query(
        "SELECT DISTINCT SUBSTR(search_date, '____', 5) FROM search WHERE done = 1"
    )

    city_names = [c.name for c in db.get_cities()]

    # Se tiver mais que uma pagina aberta, renderiza o notallowed.html. Por
    # algum motivo o flask com socketio chama a função de conexão 2x, e então
    # acaba ficando 0 ou 2 já que 0 + 1 + 1 = 2
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
        has_backup=has_backup,
        city_names=city_names,
        active=active,
        search_info=search_info,
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

    products = state.db_manager.get_products()

    # TODO: parar de usar assim (ver dataclass.asdict ou alguma conversão semi-automática p/ tupla)
    retroencoded = [(p.name, str.join(",", p.keywords)) for p in products]

    return json.dumps(retroencoded)


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


@app.route("/db/get_cities")
def route_db_get_cities() -> str:
    """Rota de seleção de cidades no banco de dados."""

    db = state.db_manager
    return json.dumps([c.name for c in db.get_cities()])


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
    path = ask_user_directory()
    print(path)
    if path is None:
        raise ValueError("Nenhum diretório selecionado")

    path.mkdir(exist_ok=True)
    state.output_path = path

    return {
        "status": "success",
        "message": "Caminho configurado com sucesso.",
        "path": str(path),
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

    output_filename = "importar.sql"
    tables = ("city", "estab", "product")

    db = state.db_manager
    with open(output_filename, "w+", encoding=ENCODING) as f:
        for table in tables:
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

        for city in db.get_cities():
            estab_data = db.run_query(
                "SELECT * FROM estab WHERE city_name = ?", (city.name,)
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

    state.connected_count += 1
    log(f"Nova conexão; total: {state.connected_count}")

    log("Cancelando timeout para fechar o programa...")
    with watchdog as w_timer:
        w_timer.cancel()


@socketio.on("disconnect")
def on_disconnect() -> None:
    """Rota contas os clientes desconectados."""

    state.connected_count -= 1
    log(f"Conexão fechada; total: {state.connected_count}")

    if state.connected_count <= 0:
        if state.wait_reload:
            state.wait_reload = False
        else:
            log(
                f"Todos os clientes desconectaram; esperando uma nova conexão por {WATCHDOG_TIMEOUT} segundos..."
            )
            with watchdog as w_timer:
                w_timer.start()


@socketio.on("output_path_from_cookies")
def on_path_from_cookies(args: dict) -> None:
    path = args.get("path")
    is_valid = path is not None and Path(path).exists()

    if not is_valid:
        emit("invalid_output_path", broadcast=True)
        return

    assert path is not None
    state.output_path = Path(path)


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
            emit(
                "show_notification", "A pesquisa já estava finalizada.", broadcast=True
            )
            # TODO: salvar a pesquisa do backup?
            return

        emit("show_notification", "Retomando pesquisa...", broadcast=True)
        opts = ScraperOptions.from_backup_info(backup_info)
        scrap = Scraper(opts, state)

        estab_data = opts.locals
    else:
        city = args["city"]
        search_id = db.save_search(False, city, 0)
        active = "0.0"
        estab_names = json.loads(args["names"])
        estabs = db.get_estab()

        # TODO: parar de usar isso
        product_info = [(p.name, str.join(",", p.keywords)) for p in db.get_products()]

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
            product_info=product_info,
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
        emit("show_notification", "Pesquisa concluída.", broadcast=True)

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
            break
        except Exception as exc:
            log_error(exc)

            error_count += 1

            if error_count >= 4:
                emit(
                    "search.error",
                    "Ocorreram muitos erros em sucessão. Para segurança do processo, a pesquisa será parada - inicie manualmente para tentar novamente.",
                    broadcast=True,
                )
                return

            emit(
                "show_notification",
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
    log(f"Iniciando o servidor...")

    force_debug = os.environ.get("ACCB_FORCE_DEBUG") is not None

    is_in_bundle = getattr(sys, "frozen", False)
    debug_enabled = force_debug or bool(__file__) and not is_in_bundle
    log(f"{is_in_bundle=}; {debug_enabled=}")

    if debug_enabled:
        os.environ["WDM_LOCAL"] = "1"
    else:
        os.environ["WDM_LOG_LEVEL"] = "0"

    # TODO: configurar o arquivo de log

    # TODO: rodar isso quando o servidor tiver carregado, ao invés de usar um timer...
    def callback() -> None:
        webbrowser.open(f"{SERVER_URL}:{PORT}")

    Timer(1, callback).start()

    if is_port_in_use(PORT):
        log(f"Porta {PORT} já em uso - o programa já está rodando?")
        return

    try:
        socketio.run(
            app,
            debug=debug_enabled,
            use_reloader=False,
            port=PORT,
            allow_unsafe_werkzeug=True,
        )
    finally:
        export_bq.exchange("shutdown")
