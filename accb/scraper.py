"""Módulo de pesquisa via scraping."""

from __future__ import annotations

import re
import sys
import json
from time import sleep, time
import webbrowser
import traceback
import random
from typing import Any, Optional
from dataclasses import dataclass
from urllib.request import urlopen
from urllib.error import URLError

from bs4 import BeautifulSoup
from flask_socketio import emit
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import Chrome

from accb.web_driver import open_chrome_driver
from accb.utils import log, log_error, show_warning, get_time_hms
from accb.state import State
from accb.model import Backup
from accb.database import DatabaseManager

URL_PRECODAHORA = "https://precodahora.ba.gov.br/produtos"


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
    # TODO: renomear p/ search_id
    """ID da pesquisa atual."""

    # TODO: isso é usado? pelo jeito não. mas acho que seria bom usar...
    backup: Any
    """Se a pesquisa atual é ou não um backup."""

    duration: Any
    """A duração de execução da pesquisa atual (necessário para reinicialização através de backup)."""

    url: str = URL_PRECODAHORA
    """URL do site a ser pesquisado"""

    @staticmethod
    def from_backup_info(backup_info: tuple) -> ScraperOptions:
        (
            active,
            city,
            _done,
            estab_info,
            product_info,
            search_id,
            duration,
            _progress_value,
        ) = backup_info
        estab_info = json.loads(estab_info)
        estab_names = estab_info["names"]
        estab_data = estab_info["info"]
        product = json.loads(product_info)

        return ScraperOptions(
            active=active,
            city=city,
            locals=estab_data,
            locals_name=estab_names,
            product_info=product,
            id=search_id,
            backup=False,
            duration=duration,
        )

    def save_as_backup(self, db: DatabaseManager, is_done: bool) -> None:
        data = Backup(
            active=self.active,
            city=self.city,
            done=is_done,
            estab_info={"names": self.locals_name, "info": self.locals},
            product_info=self.product_info,
            search_id=self.id,
            duration=0,
            progress_value=-1,
        )
        db.save_backup(data)


class ScraperError(Exception):
    pass


class Scraper:
    """Realiza o scraping na página do Preço da Hora Bahia."""

    def __init__(self, options: ScraperOptions, state: State) -> None:
        self.options = options
        self.state = state
        self.db = self.state.db_manager

        self.index, self.index_k = [int(x) for x in options.active.split(".")]
        """Index dos produtos e palavras chaves (em caso de reinicialização através de backup)"""
        # TODO: verificar isso e documentar melhor

        self.driver: Optional[Chrome] = None
        """Instância do navegador do selenium."""
        # TODO: fazer isso não ser opcional

        self.stop = False
        """Variável de controle para parar a execução da pesquisa."""

        self.exit = False
        """Variável de controle para sair a execução da pesquisa."""

        self.cancel = False
        """Variável de controle para cancelar a execução da pesquisa."""

        self.start_time = time()
        """Valor do tempo no inicio da pesquisa."""

        self.time_coeff = 4
        """Valor usado no cálculo de tempo"""

    @staticmethod
    def is_connected(test_url: str = "https://www.example.org/") -> bool:
        """Confere a conexão com a URL_PRECODAHORA desejada."""

        try:
            with urlopen(test_url):
                return True

        except URLError:
            return False

    def pause(self, cancel: bool = False) -> None:
        """Seta as variáveis de controle do programa (parada, cancelar e saída)."""

        self.cancel = cancel
        self.exit = True
        self.stop = True

    def exit_thread(self, error: bool = False) -> None:
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

            assert self.driver is not None
            self.driver.close()
            self.driver.quit()

        elif self.cancel:
            emit(
                "search",
                {
                    "type": "cancel",
                    "message": "A pesquisa foi cancelada, todos os dados foram excluídos.",
                },
                broadcast=True,
            )

            assert self.driver is not None
            self.driver.close()
            self.driver.quit()

        elif self.exit:
            emit(
                "search",
                {
                    "type": "pause",
                    "message": "A pesquisa foi parada, todos os dados foram salvos no banco de dados local.",
                },
                broadcast=True,
            )

            assert self.driver is not None
            self.driver.close()
            self.driver.quit()

    def send_logs(self, *messages: str) -> None:
        log(f"[Scraper.send_logs]: {str.join('\n  ', messages)}")
        emit("search.log", list(messages), broadcast=True)

    def get_data(self, _product: str, keyword: str) -> None:
        """Filtra os dados da janela atual aberta do navegador e os salva no banco de dados."""
        # FIXME: tirar argumento `_product`? ele não é usado

        assert self.driver is not None
        elements = self.driver.page_source
        soup = BeautifulSoup(elements, "html.parser")
        logs = []

        irrelevant_patt = re.compile(r"[^A-Za-z0-9,]+")
        money_patt = re.compile(r" R\$ \d+(,\d{1,2})")

        def adjust_and_clean(x: str) -> str:
            return irrelevant_patt.sub(" ", x).lstrip()

        for item in soup.find_all(True, {"class": "flex-item2"}):
            product_name = adjust_and_clean(item.find("strong").text)
            product_address = adjust_and_clean(
                item.find(attrs={"data-original-title": "Endereço"}).parent.text
            )
            product_local = adjust_and_clean(
                item.find(attrs={"data-original-title": "Estabelecimento"}).parent.text
            )
            product_price = item.find(text=money_patt).lstrip()

            if self.stop:
                return

            try:
                self.db.save_search_item(
                    {
                        "search_id": self.options.id,
                        "web_name": product_local,
                        "adress": product_address,
                        "product_name": product_name,
                        "price": product_price,
                        "keyword": keyword,
                    }
                )
            except Exception as exc:  # FIXME: parar de usar esse except?
                log_error(exc)
                return

            logs.append(
                f"Produto: '{product_name}' em '{product_local}' a {product_price} (palavra chave: {keyword}, endereço: {product_address})"
            )

        self.send_logs(*logs)

    def is_in_captcha(self) -> bool:
        """Confere se o usuário precisa resolver o captcha."""
        # FIXME: confirmar: ela retorna True se precisar, ou se não precisar?

        try:
            assert self.driver is not None
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "flash"))
            )
        except Exception:
            sleep(1)
            return False

        return True

    def open_captcha_and_warn(self) -> None:
        """Abre a URL de captcha, avisa e aguarda o aviso ser fechado."""

        assert self.driver is not None

        webbrowser.open(self.options.url)

        message = "O Captcha foi ativado. Foi aberta uma aba no seu navegador - resolva-o lá e depois pressione OK nesta mensagem."

        # FIXME: acho que não precisa mandar a mensagem para o front-end também...
        emit(
            "captcha",
            {
                "type": "captcha",
                "message": message,
            },
            broadcast=True,
        )

        show_warning(
            title="CAPTCHA",
            message=message,
        )

        self.driver.back()

    def smart_sleep(self, base: float) -> None:
        """Calcula um tempo aleatório próximo de `base`, e logo depois avisa e aguarda por tal tempo."""

        min_time = 0.2
        value = max(min_time, base * self.time_coeff + random.uniform(-1.0, 1.0))
        self.send_logs(f"Aguardando por {value:.2f}s...")
        sleep(value)

    def captcha_wait_loop(self) -> None:  # FIXME: rename
        """Abre o captcha e aguarda o usuário resolver o captcha."""

        # TODO: trocar nome da função

        if not self.is_connected():
            self.exit_thread(True)
            raise ScraperError("Sem conexão com a rede!")

        self.send_logs("Aguardando usuário resolver o captcha...")
        while self.is_in_captcha():
            self.open_captcha_and_warn()
        self.send_logs("Captcha resolvido!")

    def run(self) -> bool:
        """Realiza a pesquisa na plataforma do Preço da Hora Bahia. Retorna se a pesquisa funcionou."""
        # TODO: emitir um "search.began" ou algo assim, que aí marca a inicialização das outras coisas também
        emit("search.update_progress_bar", 0.0, broadcast=True)

        # FIXME: retornar exception caso a pesquisa tenha falhado, eu acho.

        # multiplicador para tempo de espera
        # TODO: parar de usar isso (em favor do self.smart_sleep)
        times = self.time_coeff

        # TODO: usar isso em forma de Generator, que poderia ser feito cada vez que um sleep é usado, e um for loop em outro lugar poderia constantemente verificar se a pesquisa precisa ser pausada. E com isso talvez seja possível detectar captchas de maneira eficiente também!

        try:
            driver = self.driver = open_chrome_driver()
            driver.get(self.options.url)
        except Exception:
            return False

        try:
            # TODO: encontrar uma maneira de usar o self.smart_sleep para isso
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "informe-sefaz-error"))
            )
            driver.find_element(By.ID, "informe-sefaz-error").click()
        except Exception:
            pass

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
            self.captcha_wait_loop()
            sleep(1)
        finally:
            driver.find_element(By.CLASS_NAME, "location-box").click()
            self.smart_sleep(2)

        # Botão que abre a opção de inserir o CEP
        try:
            WebDriverWait(driver, 2 * times).until(
                EC.presence_of_element_located((By.ID, "add-center"))
            )
        except Exception:
            self.captcha_wait_loop()
            sleep(1)
        finally:
            driver.find_element(By.ID, "add-center").click()
            self.smart_sleep(2)

        # Envia o MUNICIPIO desejado para o input
        driver.find_element(By.CLASS_NAME, "sbar-municipio").send_keys(
            self.options.city
        )
        sleep(1)

        # Pressiona o botão que realiza a pesquisa por MUNICIPIO
        driver.find_element(By.CLASS_NAME, "set-mun").click()

        sleep(1)
        driver.find_element(By.ID, "aplicar").click()

        self.smart_sleep(2)
        product_count = len(self.options.product_info)

        for index, (product, keywords) in enumerate(
            self.options.product_info[self.index :]
        ):
            if self.stop:
                break

            progress_value = 100 * (self.index + index) / product_count

            self.send_logs(
                f"Começando pesquisa do produto {product} (progresso: {progress_value:.0f}%)"
            )
            emit("search.began_searching_product", product)
            emit("search.update_progress_bar", progress_value, broadcast=True)

            for index_k, keyword in enumerate(keywords.split(",")[self.index_k :]):
                if self.stop:
                    self.exit = True
                    self.exit_thread()
                    return True

                self.send_logs(f"Próxima palavra chave: {keyword}")

                active = "{}.{}".format(index + self.index, index_k + self.index_k)
                duration = (
                    get_time_hms(self.start_time)["minutes"] + self.options.duration
                )

                self.send_logs("Atualizando backup...")

                self.db.update_backup(
                    Backup(
                        active=active,
                        city=self.options.city,
                        done=False,
                        estab_info=self.make_estab_info(),
                        product_info=self.options.product_info,
                        search_id=self.options.id,
                        duration=duration,
                    )
                )

                self.smart_sleep(1.5)

                # Barra de pesquisa superior (produtos)
                try:
                    WebDriverWait(driver, 3 * times).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "sbar-input"))
                    )
                except Exception:
                    self.captcha_wait_loop()
                finally:
                    search = driver.find_element(By.ID, "top-sbar")

                self.send_logs("Digitando palavra chave...")
                for w in keyword:
                    search.send_keys(w)
                    sleep(0.25)
                search.send_keys(Keys.ENTER)

                self.smart_sleep(3)

                driver.page_source.encode("utf-8")

                if self.stop:
                    self.exit = True
                    self.exit_thread()

                    return True

                self.send_logs("Aguardando a pesquisa da palavra chave terminar...")
                # o processo é reconhecido como terminado quando a classe flex-item2 está presente, que é uma classe de estilo dos elementos listados.
                try:
                    WebDriverWait(driver, 4 * times).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "flex-item2"))
                    )
                except Exception:
                    self.captcha_wait_loop()
                    self.smart_sleep(1)

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
                        self.smart_sleep(2)
                        driver.find_element(By.ID, "updateResults").click()
                        flag += 1

                        if flag == 3:
                            break
                        log("~~ 5.4")  # FIXME: remove(breakpoint)
                    except Exception:
                        if not self.is_in_captcha():
                            break
                        self.captcha_wait_loop()

                if self.stop:
                    self.exit = True
                    self.exit_thread()
                    return True

                self.get_data(product, keyword)

                log("~~ 6")  # FIXME: remove(breakpoint)

            log("~~ 6.1")  # FIXME: remove(breakpoint)

        log("~~ 7")  # FIXME: remove(breakpoint)

        if self.stop:
            self.exit = True
            self.exit_thread()
            return True

        log("~~ 8")  # FIXME: remove(breakpoint)

        duration = get_time_hms(self.start_time)
        self.db.update_search(
            {
                "id": self.options.id,
                "done": 1,
                "duration": duration["minutes"] + self.options.duration,
            }
        )

        self.send_logs("Atualizando backup...")

        self.db.update_backup(
            Backup(
                active="0.0",
                city=self.options.city,
                done=True,
                estab_info=self.make_estab_info(),
                product_info=self.options.product_info,
                search_id=self.options.id,
                duration=duration["minutes"] + self.options.duration,
            )
        )

        driver.close()
        driver.quit()

        return True

    def make_estab_info(self) -> dict:
        # FIXME: parar de usar isso (não parece ser usado)
        return {
            "names": self.options.locals_name,
            "info": self.options.locals,
        }
