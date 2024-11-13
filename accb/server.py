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
from typing import Any, Optional
from time import sleep

from flask import Flask, render_template, request, Response
from flask_material import Material
from flask_socketio import SocketIO, emit

from selenium.webdriver import Chrome

from accb.scraper import Scraper, ScraperOptions, ScraperError, ScraperRestart
from accb.utils import log, log_error, ask_user_directory, open_folder, Defer
from accb.restartable_timer import RestartableTimer
from accb.locked_var import LockedVar
from accb.state import State
from accb.consts import MONTHS_PT_BR
from accb.model import Estab, OngoingSearch, Search
from accb.web_driver import is_chrome_installed, open_chrome_driver
from accb.database import table_dump
from accb.bi_queue import BiQueue

RequestDict = dict[str, Any]
"""Tipo usado para requests (e respostas delas)."""

app = Flask(__name__)
Material(app)
socketio = SocketIO(app, manage_session=False, async_mode="threading")
state = State()

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


def is_port_in_use(port: int) -> bool:
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

    if db.get_option("show_search_window") is None:
        db.set_option("show_search_window", False)

    if db.get_option("show_search_extras") is None:
        db.set_option("show_search_extras", True)

    product_names = db.run_query("SELECT product_name FROM product")

    ongoing_searches_pairs = [
        (o, db.get_search_by_id(o.search_id)) for o in db.get_ongoing_searches()
    ]

    day = str(date.today()).split("-")[1]

    searches_r = db.run_query(
        "SELECT * FROM search WHERE done = 1 AND search_date LIKE ?",
        (f"%%-{day}-%%",),
    )

    searches = [
        (id_, city_name, search_date)
        for (id_, _done, city_name, search_date, *_) in searches_r
    ]

    search_years = db.run_query(
        "SELECT DISTINCT SUBSTR(search_date, '____', 5) FROM search WHERE done = 1"
    )

    city_names = [c.name for c in db.get_cities()]

    # Se tiver mais que uma pagina aberta, renderiza o notallowed.html. Por
    # algum motivo o flask com socketio chama a função de conexão 2x, e então
    # acaba ficando 0 ou 2 já que 0 + 1 + 1 = 2
    template = "home.html" if 0 >= state.connected_count <= 2 else "notallowed.html"

    return render_template(
        template,
        city_names=city_names,
        ongoing_searches_pairs=ongoing_searches_pairs,
        searches=searches,
        product_len=len(product_names),
        months=MONTHS_PT_BR,
        active_month=day,
        is_chrome_installed=is_chrome_installed(),
        years=search_years,
    )


@app.route("/insert_product")
def route_insert_product() -> RequestDict:
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
def route_remove_product() -> RequestDict:
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
def route_select_search_info() -> RequestDict:
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
def route_update_product() -> RequestDict:
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
def route_select_estab() -> RequestDict:
    """Rota de seleção de estabelecimentos no banco de dados."""

    db = state.db_manager
    city = request.args.get("city")
    estabs = [e for e in db.get_estab_old() if e[0] == city]
    return {"status": "success", "estabs": estabs}


@app.route("/remove_estab")
def route_remove_estab() -> RequestDict:
    """Rota de remoção de estabelecimentos no banco de dados."""

    estab_name = request.args["estab_name"]

    state.db_manager.delete("estab", "estab_name", estab_name)
    return {
        "status": "success",
        "message": f"O estabelecimento {estab_name} foi removido com sucesso",
    }


@app.route("/update_estab")
def route_update_estab() -> RequestDict:
    """Rota de atualização de estabelecimentos no banco de dados."""

    city_name = request.args["city_name"]
    estab_name = request.args["estab_name"]
    primary_key = request.args["primary_key"]
    web_name = request.args["web_name"]
    address = request.args["address"]

    state.db_manager.update_estab(
        {
            "primary_key": primary_key,
            "city_name": city_name,
            "estab_name": estab_name,
            "web_name": web_name,
            "address": address,
        }
    )

    return {
        "status": "success",
        "message": f"O estabelecimento {estab_name} foi atualizado com sucesso",
    }


@app.route("/insert_estab")
def route_insert_estab() -> RequestDict:
    """Rota de inserção de estabelecimentos no banco de dados."""

    db = state.db_manager
    city_name = request.args["city_name"]
    estab_name = request.args["estab_name"]
    web_name = request.args["web_name"]
    address = request.args["address"]

    estab = Estab(
        name=estab_name,
        address=address,
        city=city_name,
        web_name=web_name,
    )
    db.save_estab(estab)

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
def route_insert_city() -> RequestDict:
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
def route_update_city() -> RequestDict:
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
def route_delete_city() -> RequestDict:
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
def route_ask_output_path() -> RequestDict:
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
def route_delete_search() -> RequestDict:
    """Rota de deleção de pesquisa no banco de dados."""

    search_id = request.args["search_id"]

    state.db_manager.delete("search", "id", search_id)
    state.wait_reload = True
    return {"status": "success", "message": "Pesquisa deletada com sucesso."}


@app.route("/export_database")
def route_export_database() -> RequestDict:
    """Rota responsável por exportar os dados do banco"""

    assert state.output_path is not None
    output_filename = state.output_path / "importar.sql"

    tables_to_dump = ("city", "estab", "product")

    with (
        output_filename.open("w+", encoding=ENCODING) as f,
        state.db_manager.db_connection() as conn,
    ):
        for table in tables_to_dump:
            for line in table_dump(conn, table):
                f.write(f"{line}\n")

    return {
        "status": "success",
        "message": "Dados exportados com sucesso - agora é possível importá-lo em outro computador com o arquivo 'importar.sql'.",
    }


@app.route("/import_database", methods=["POST"])
def route_import_database() -> RequestDict:
    """Rota responsável por importar os dados do banco"""

    script = request.files["file"].read().decode(ENCODING)
    state.db_manager.import_database_from_script(script)

    state.wait_reload = True
    return {
        "status": "success",
        "message": "Dados importados com sucesso.",
    }


@app.route("/open_folder")
def route_open_folder() -> RequestDict:
    open_folder(Path(request.args["path"]))
    return {"status": "success"}


@app.route("/clean_search")
def route_clean_search() -> RequestDict:
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
                "SELECT DISTINCT id, search_date FROM search WHERE done = 1"
            )

            for search_id, search_date in args:
                output_folder = limpeza_path / search_date
                output_folder.mkdir(parents=True, exist_ok=True)

                for _, name, address, web_name in estab_data:
                    output_path = output_folder / f"{name}.xlsx"

                    export_to_xlsx(
                        db=db,
                        search_id=search_id,
                        filter_by_address=False,
                        output_path=output_path,
                        web_name=web_name,
                        address=address,
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


@app.route("/get_option")
def route_get_option() -> RequestDict:
    key = request.args["key"]
    return {"status": "success", "value": state.db_manager.get_option(key)}


@app.route("/set_option")
def route_set_option() -> RequestDict:
    key = request.args["key"]
    value = request.args["value"]
    state.db_manager.set_option(key, json.loads(value))
    return {"status": "success"}


@app.route("/generate_file")
def route_generate_file() -> RequestDict:
    """Gera arquivo(s) excel com os dados das pesquisas."""

    assert state.output_path is not None

    db = state.db_manager

    format_type = request.args.get("format")
    city = request.args["city_name"]
    search_id = request.args["search_id"]

    if format_type == "all":
        output_folder = db_to_xlsx_all(city, search_id, db, state.output_path)
        return {"status": "success", "path": str(output_folder)}

    names = request.args["names"]

    estab_names = json.loads(names)
    estabs = [e for e in db.get_estabs_for_city(city) if e.name in estab_names]

    output_folder = db_to_xlsx(db, search_id, estabs, city, state.output_path)
    return {"status": "success", "path": str(output_folder)}


@socketio.on("search.pause")
def on_pause() -> RequestDict:
    """Pausa a pesquisa atual, mantendo seu estado no banco de dados."""

    assert state.scraper is not None
    state.scraper.pause()

    state.wait_reload = True

    return {"status": "success"}


@socketio.on("search.cancel")
def on_cancel() -> RequestDict:
    """Cancela a pesquisa atual e deleta os dados dela no banco de dados."""

    state.wait_reload = True

    assert state.scraper is not None
    state.scraper.cancel()

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


@socketio.on("output_path_from_options")
def on_path_from_options(args: RequestDict) -> None:
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


@socketio.on("search.resume_ongoing")
def on_search_resume_ongoing(args: RequestDict) -> None:
    search_id = args["search_id"]
    assert isinstance(search_id, int)

    search(resume_id=search_id)


@socketio.on("search.begin")
def on_search_begin(args: RequestDict) -> None:
    db = state.db_manager

    city = args["city"]
    assert isinstance(city, str)

    estab_names = args["names"]
    assert isinstance(estab_names, list)

    search(city=city, estab_names=estab_names)


def search(
    resume_id: Optional[int] = None,
    city: Optional[str] = None,
    estab_names: Optional[list[str]] = None,
    max_error_count: int = 3,
) -> None:
    db = state.db_manager
    assert state.output_path is not None

    opts: ScraperOptions
    if resume_id is not None:
        search = db.get_search_by_id(resume_id)
        assert search is not None

        ongoing = db.get_ongoing_search_by_id(resume_id)
        assert ongoing is not None

        opts = ScraperOptions(
            ongoing=ongoing,
            duration_mins=search.total_duration_mins,
        )
    else:
        assert city is not None
        assert estab_names is not None

        search_id = db.create_search(city)

        ongoing = OngoingSearch(
            search_id=search_id,
            city=city,
            estabs=[e for e in db.get_estabs_for_city(city) if e.name in estab_names],
            products=list(db.get_products()),
            current_product=0,
            current_keyword=0,
        )
        db.create_ongoing_search(ongoing)

        opts = ScraperOptions(
            ongoing=ongoing,
            duration_mins=0.0,
        )

    error_count = 0

    def close_driver(driver: Chrome) -> None:
        driver.close()
        driver.quit()

    while True:
        try:
            is_headless = not db.get_option("show_search_window")

            with Defer(open_chrome_driver(is_headless=is_headless), deinit=close_driver) as driver:
                scraper = Scraper(opts, state, driver)
                state.scraper = scraper
                attempt_search(scraper)
            break

        except ScraperRestart as _exc:
            # não é tecnicamente um erro, então vamos só fingir que nada aconteceu e ele vai reiniciar automaticamente
            pass

        except Exception as exc:
            log_error(exc)

            error_count += 1

            if error_count > max_error_count:
                emit(
                    "search.finished_from_error",
                    "Ocorreram muitos erros em sucessão. A pesquisa será parada - inicie-a manualmente para tentar novamente.",
                    broadcast=True,
                )
                break

            emit(
                "show_notification",
                "Ocorreu um erro durante a pesquisa; ela será reiniciada, aguarde um instante.",
                broadcast=True,
            )

            sleep(1)

    state.scraper = None


def attempt_search(scraper: Scraper) -> None:
    """Inicia a pesquisa."""

    db = state.db_manager
    exc: Optional[Exception] = None

    try:
        scraper.run()

        if scraper.mode == "default":
            # FIXME: é pra exportar automaticamente mesmo?
            ongoing = scraper.options.ongoing
            db_to_xlsx(
                db, ongoing.search_id, ongoing.estabs, ongoing.city, state.output_path
            )

        state.wait_reload = True
        emit("search.finished", broadcast=True) # TODO: mover isso p/ self.finalize_search() eu acho

    except ScraperRestart as err:
        exc = err
        scraper.mode = "paused"

    except ScraperError as err:
        exc = err
        scraper.mode = "errored"

    finally:
        scraper.finalize_search()

    if exc is not None:
        raise exc


@app.context_processor
def utility_processor() -> RequestDict:
    """Insere a função para ser chamada em todos os templates a qualquer momento"""

    def decode(text: str) -> str:
        return text.encode("utf8").decode("utf8")

    def replace(text: str, char: str) -> str:
        return text.replace(char, "")

    def json_stringfy(var: Any) -> str:
        return json.dumps(var)

    def as_percentage(idx: int, total: int) -> str:
        perc = 100.0 * idx / total
        return f"{perc:.0f}%"

    return {
        "enumerate": enumerate,
        "decode": decode,
        "len": len,
        "replace": replace,
        "json_stringfy": json_stringfy,
        "as_percentage": as_percentage,
    }


def main() -> None:
    log("Iniciando o servidor...")

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
    Timer(1, lambda: webbrowser.open(f"{SERVER_URL}:{PORT}")).start()

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
