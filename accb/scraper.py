"""Módulo de pesquisa via scraping."""

import re
import time
import os, sys
import json
import urllib.request
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import Any, Optional
import time
import webbrowser
import traceback

from flask_socketio import SocketIO, send, emit

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import Chrome

from accb.web_driver import open_chrome_driver
from accb.utils import log, log_error, show_warning, get_time_hms
from accb.state import State
from accb.database import DatabaseManager


@dataclass
class ScraperOptions:
    """Armazena informações que instruem a pesquisa feita pelo Scraper."""

    # TODO: colocar tipos para os campos aqui

    # TODO: renomear isso
    locals: Any
    """Estabelecimentos onde a pesquisa será realizada."""

    city: Any
    """Nome da cidade onde a pesquisa será realizada."""

    # TODO: qual a diferença entre isso e locals?
    locals_name: Any
    """Nomes dos estabelecimentos onde a pesquisa será realizada."""

    product_info: Any
    """Produtos a serem pesquisados."""

    active: Any
    """Valor decimal de indexes ativos 1.1, onde 1. é o index do produto e .1 é o index da palavra chave."""

    id: Any
    """ID da pesquisa atual."""

    # TODO: isso é usado? pelo jeito não. mas acho que seria bom usar...
    backup: Any
    """Se a pesquisa atual é ou não um backup."""

    duration: Any
    """A duração de execução da pesquisa atual (necessário para reinicialização através de backup)."""

    progress_value: Any
    """Valor de soma da barra de pesquisa, caso seja adicionado um novo produto é necessário manter os dados da pesquisa anterior."""
    # TODO: essa descrição tá estranha


class ScraperError(Exception): ...


class Scraper:
    """Realiza o scraping na página do Preço da Hora Bahia."""

    def __init__(self, options: ScraperOptions, state: State) -> None:
        self.options = options
        self.state = state
        self.db = self.state.db_manager

        self.index, self.index_k = [int(x) for x in options.active.split(".")]
        """Index dos produtos e palavras chaves (em caso de reinicialização através de backup);"""
        # TODO: verificar isso e documentar melhor

        self.driver: Optional[Chrome] = None
        """Instância do navegador do selenium."""

        self.url: Optional[str] = None

        self.stop = False
        """Variável de controle para parar a execução da pesquisa."""

        self.exit = False
        """Variável de controle para sair a execução da pesquisa."""

        self.cancel = False
        """Variável de controle para cancelar a execução da pesquisa."""

        self.start_time = time.time()
        """Valor do tempo no inicio da pesquisa."""

    def check_connection(self, url: str = "https://www.example.org/") -> bool:
        """Confere a conexão com a URL desejada."""

        try:
            urllib.request.urlopen(url)
            return True
        except urllib.error.URLError:
            return False

    def pause(self, cancel=False):
        """Seta as varáveis de controle do programa (parada, cancelar e saída)."""

        self.cancel = cancel
        self.exit = True
        self.stop = True

    # CHECK

    def exit_thread(self, error=False):
        """Pausa a pesquisa caso aconteça um erro de rede ou o usuário pause-a ou cancele manualmente."""
        if error:

            emit(
                "search",
                {
                    "type": "error",
                    "message": "Ocorreu um erro de rede durante a pesquisa e não foi possível reinicia-la automaticamente, inicie a pesquisa manualmente !",
                },
                broadcast=True,
            )

            self.driver.close()
            self.driver.quit()
            return

        elif self.cancel:

            emit(
                "search",
                {
                    "type": "cancel",
                    "message": "A pesquisa foi cancelada, todos os dados foram excluídos.",
                },
                broadcast=True,
            )
            self.driver.close()
            self.driver.quit()
            return

        elif self.exit:

            emit(
                "search",
                {
                    "type": "pause",
                    "message": "A pesquisa foi parada, todos os dados foram salvos no banco de dados local.",
                },
                broadcast=True,
            )
            self.driver.close()
            self.driver.quit()
            return

    def get_data(self, product: str, keyword: str):
        """Filtra os dados da janela atual aberta do navegador e os salva no banco de dados."""

        assert self.driver is not None
        elements = self.driver.page_source
        soup = BeautifulSoup(elements, "html.parser")
        arr = []

        patt = re.compile(r"[^A-Za-z0-9,]+")

        def adjust_and_clean(input: str) -> str:
            return patt.sub(" ", input).lstrip()

        # search_item["search_id"], search_item["city_name"], search_item["estab_name"], search_item["web_name"], search_item["adress"], search_item["price"])
        for item in soup.findAll(True, {"class": "flex-item2"}):
            product_name = adjust_and_clean(item.find("strong").text)
            product_address = adjust_and_clean(
                item.find(attrs={"data-original-title": "Endereço"}).parent.text
            )
            product_local = adjust_and_clean(
                item.find(attrs={"data-original-title": "Estabelecimento"}).parent.text
            )
            product_price = item.find(text=re.compile(r" R\$ \d+(,\d{1,2})")).lstrip()

            log(
                f"Produto encontrado - endereço: {product_address}; estab.: {product_local}; preço: {product_price}; nome: {product_name};"
            )

            try:
                if not self.stop:
                    self.db.db_save_search_item(
                        {
                            "search_id": self.options.id,
                            "web_name": product_local,
                            "adress": product_address,
                            "product_name": product_name,
                            "price": product_price,
                            "keyword": keyword,
                        }
                    )
                    arr.append(
                        [
                            str(product_name),
                            str(product_local),
                            str(keyword),
                            str(product_address),
                            str(product_price),
                        ]
                    )
            except Exception:
                exc_type, exc_value, exc_tb = sys.exc_info()
                log_error(traceback.format_exception(exc_type, exc_value, exc_tb))

                # TODO: handle exception
                pass
        if not self.stop:
            emit(
                "captcha",
                {
                    "type": "log",
                    "data": json.dumps(arr),
                },
                broadcast=True,
            )

    def check_captcha(self, request: int = 0) -> bool:
        """Função que confere se o captcha foi resolvido com sucesso pelo usuário."""

        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "flash"))
            )
        except Exception:
            time.sleep(1)
            return False

        return True

    # REDO
    def pop_up(self):
        """Mostra uma mensagem em pop up para o usuário."""

        emit(
            "captcha",
            {
                "type": "captcha",
                "message": "Captcha foi ativado, foi aberto uma aba no seu navegador, resolva-o e pressione okay.",
            },
            broadcast=True,
        )

        show_warning(
            title="CAPTCHA",
            message="Captcha foi ativado, foi aberto uma aba no seu navegador, resolva-o e pressione okay",
        )

        self.driver.back()

    def captcha(self):
        """Trata por erro de rede e inicia um loop para conferir se o usuário resolveu o captcha."""

        # Se eu tenho conexão o captcha foi ativado, se não, é erro de rede.

        log("~~ CAPTCHA")  # FIXME: remove(breakpoint)

        if self.check_connection():
            while True:
                if self.check_captcha(1):
                    webbrowser.open(self.url)
                    self.pop_up()
                else:
                    # log("CAPTCHA FALSE")
                    return
        else:
            self.exit_thread(True)
            raise ScraperError("Sem conexão com a rede!")

    def run(self):
        """Realiza a pesquisa na plataforma do Preço da Hora Bahia."""

        URL = "https://precodahora.ba.gov.br/produtos"

        self.url = URL
        times = 4
        try:
            driver = self.driver = open_chrome_driver()
            driver.get(URL)
        except Exception:
            return False

        emit(
            "captcha",
            {"type": "notification", "message": "Iniciando pesquisa ..."},
            broadcast=True,
        )

        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "informe-sefaz-error"))
            )
            driver.find_element(By.ID, "informe-sefaz-error").click()
        except Exception:
            # log("Pop Up Error")
            pass

        # * Processo de pesquisa de produto

        # time.sleep(times)

        # * Processo para definir a região desejada para ser realizada a pesquisa

        # emit(
        #     "captcha",
        #     {
        #         "type": "notification",
        #         "message": "Pesquisando Localização",
        #     },
        #     broadcast=True,
        # )

        # Botão que abre o modal referente a localização
        try:
            WebDriverWait(driver, 4 * times).until(
                EC.presence_of_element_located((By.CLASS_NAME, "location-box"))
            )
        except Exception:
            self.captcha()
            time.sleep(1)
        finally:
            driver.find_element(By.CLASS_NAME, "location-box").click()
            time.sleep(2 * times)

        # Botão que abre a opção de inserir o CEP
        try:
            WebDriverWait(driver, 2 * times).until(
                EC.presence_of_element_located((By.ID, "add-center"))
            )
        except Exception:
            self.captcha()
            time.sleep(1)
        finally:
            driver.find_element(By.ID, "add-center").click()
            time.sleep(2 * times)

        # Envia o MUNICIPIO desejado para o input

        driver.find_element(By.CLASS_NAME, "sbar-municipio").send_keys(
            self.options.city
        )
        time.sleep(1)

        # Pressiona o botão que realiza a pesquisa por MUNICIPIO
        driver.find_element(By.CLASS_NAME, "set-mun").click()

        time.sleep(1)
        driver.find_element(By.ID, "aplicar").click()

        time.sleep(2 * times)
        for index, (product, keywords) in enumerate(
            self.options.product_info[self.index :]
        ):
            log(f"Começando pesquisa do produto {product}")

            if not self.stop:
                emit(
                    "captcha",
                    {
                        "type": "progress",
                        "product": product,
                        "value": 0,
                    },
                    broadcast=True,
                )

            for index_k, keyword in enumerate(keywords.split(",")[self.index_k :]):
                if self.stop:
                    self.exit = True
                    self.exit_thread()
                    return True

                log(f"Pesquisando keyword {keyword}")

                active = "{}.{}".format(index + self.index, index_k + self.index_k)
                duration = (
                    get_time_hms(self.start_time)["minutes"] + self.options.duration
                )

                log("~~ BEFORE BACKUP")  # FIXME: remove(breakpoint)

                self.db.db_update_backup(
                    {
                        "active": active,
                        "city": self.options.city,
                        "done": 0,
                        "estab_info": json.dumps(
                            {
                                "names": self.options.locals_name,
                                "info": self.options.locals,
                            }
                        ),
                        "product_info": json.dumps(self.options.product_info),
                        "search_id": self.options.id,
                        "duration": duration,
                    }
                )

                log("~~ AFTER BACKUP")  # FIXME: remove(breakpoint)

                time.sleep(1.5 * times)

                log("~~ WILL GET PRODUCT BAR")  # FIXME: remove(breakpoint)

                # Barra de pesquisa superior (produtos)
                try:
                    WebDriverWait(driver, 3 * times).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "sbar-input"))
                    )
                except:
                    self.captcha()
                finally:
                    search = driver.find_element(By.ID, "top-sbar")

                log("~~ 1")  # FIXME: remove(breakpoint)

                for w in keyword:
                    search.send_keys(w)
                    time.sleep(0.25)

                log("~~ 2")  # FIXME: remove(breakpoint)

                # Realiza a pesquisa (pressiona enter)
                search.send_keys(Keys.ENTER)

                log("~~ 3")  # FIXME: remove(breakpoint)

                time.sleep(3 * times)
                driver.page_source.encode("utf-8")

                log("~~ 4")  # FIXME: remove(breakpoint)

                if self.stop:
                    self.exit = True
                    self.exit_thread()

                    return True

                # Espera a página atualizar, ou seja, terminar a pesquisa. O proceso é reconhecido como terminado quando a classe flex-item2 está presente, que é a classe utilizada para estilizar os elementos listados

                log("~~ 5")  # FIXME: remove(breakpoint)

                try:
                    WebDriverWait(driver, 4 * times).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "flex-item2"))
                    )
                except Exception:
                    self.captcha()
                    time.sleep(times)

                finally:
                    log("~~ 5.1")  # FIXME: remove(breakpoint)
                    flag = 0
                    while True:
                        if self.stop:
                            self.exit = True
                            self.exit_thread()
                            return True

                        try:
                            log("~~ 5.2")  # FIXME: remove(breakpoint)
                            WebDriverWait(driver, 2 * times).until(
                                EC.presence_of_element_located((By.ID, "updateResults"))
                            )
                            time.sleep(2 * times)
                            driver.find_element(By.ID, "updateResults").click()
                            flag = flag + 1

                            if flag == 3:
                                break
                            log("~~ 5.4")  # FIXME: remove(breakpoint)
                        except Exception:
                            if not self.check_captcha(0):
                                # log("Quantidade máxima de paginas abertas.")
                                break
                            else:
                                self.captcha()

                    if self.stop:
                        self.exit = True
                        self.exit_thread()
                        return True

                    self.get_data(product, keyword)

                log("~~ 6")  # FIXME: remove(breakpoint)

            if not self.stop:
                log(f"Progress: {self.options.progress_value}")
                emit(
                    "captcha",
                    {
                        "type": "progress",
                        "product": product,
                        "value": self.options.progress_value,
                    },
                    broadcast=True,
                )

            log("~~ 7")  # FIXME: remove(breakpoint)

        if self.stop:
            self.exit = True
            self.exit_thread()
            return

        log("~~ 8")  # FIXME: remove(breakpoint)

        duration = get_time_hms(self.start_time)
        self.db.db_update_search(
            {
                "id": self.options.id,
                "done": 1,
                "duration": duration["minutes"] + self.options.duration,
            }
        )

        log("~~ 9")  # FIXME: remove(breakpoint)

        self.db.db_update_backup(
            {
                "active": "0.0",
                "city": self.options.city,
                "done": 1,
                "estab_info": json.dumps(
                    {"names": self.options.locals_name, "info": self.options.locals}
                ),
                "product_info": json.dumps(self.options.product_info),
                "search_id": self.options.id,
                "duration": duration["minutes"] + self.options.duration,
            }
        )

        driver.close()
        driver.quit()

        return True
