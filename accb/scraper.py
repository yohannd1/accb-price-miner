"""Módulo de pesquisa via scraping."""

from __future__ import annotations

import re
from time import sleep, time
import webbrowser
import random
from typing import Generator, Literal, assert_never
from dataclasses import dataclass
from urllib.request import urlopen
from urllib.error import URLError

from bs4 import BeautifulSoup
from flask_socketio import emit
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import Chrome

from accb.utils import log, show_warning, get_time_hms, enumerate_skip
from accb.state import State
from accb.model import OngoingSearch

URL_PRECODAHORA = "https://precodahora.ba.gov.br/produtos"


@dataclass
class ScraperOptions:
    """Armazena informações que instruem a pesquisa feita pelo Scraper."""

    ongoing: OngoingSearch

    duration_mins: float
    """Estimação da duração da pesquisa (em minutos)."""

    url: str = URL_PRECODAHORA
    """URL do site a ser pesquisado"""


class ScraperError(Exception):
    pass


class SearchResponse:
    @dataclass
    class Default:
        pass

    @dataclass
    class Error:
        message: str

    @dataclass
    class Sleep:
        duration: float

    All = Default | Sleep | Error


Mode = Literal["default", "errored", "cancelled", "paused"]


class Scraper:
    """Realiza o scraping na página do Preço da Hora Bahia."""

    def __init__(self, options: ScraperOptions, state: State, driver: Chrome) -> None:
        self.options = options
        self.state = state
        self.driver = driver
        self.db = self.state.db_manager

        self.mode: Mode = "default"

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

    def pause(self) -> None:
        self.mode = "paused"

    def cancel(self) -> None:
        self.mode = "cancelled"

    def _delete_related_search(self) -> None:
        db = self.state.db_manager
        id_ = self.options.ongoing.search_id
        db.delete_ongoing_search_by_id(id_)
        db.delete_search_by_id(id_)

    def finalize_search(self) -> None:
        match self.mode:
            case "default":
                pass

            case "errored":
                # FIXME: isso aqui faz com que a pesquisa seja cancelada e tenha que ser reiniciada. Talvez seja melhor tentar resumir ela por backup?
                self._delete_related_search()

                emit(
                    "search",
                    {
                        "type": "error",
                        "message": "Ocorreu um erro de rede durante a pesquisa.",
                    },
                    broadcast=True,
                )
            case "cancelled":
                self._delete_related_search()

                emit(
                    "search",
                    {
                        "type": "cancel",
                        "message": "A pesquisa foi cancelada, todos os dados foram excluídos.",
                    },
                    broadcast=True,
                )
            case "paused":
                emit(
                    "search",
                    {
                        "type": "pause",
                        "message": "A pesquisa foi parada, todos os dados foram salvos no banco de dados local.",
                    },
                    broadcast=True,
                )
            case _ as unreachable:
                assert_never(unreachable)

    def send_logs(self, *messages: str) -> None:
        if len(messages) == 0:
            return

        if len(messages) == 1:
            final = messages[0]
        else:
            final = str.join('\n', [f"  {msg}" for msg in messages])

        log(f"[Scraper.send_logs]: {final}")
        emit("search.log", list(messages), broadcast=True)

    def get_data(self, _product: str, keyword: str) -> None:
        """Filtra os dados da janela atual aberta do navegador e os salva no banco de dados."""
        # FIXME: tirar argumento `_product`? ele não é usado

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

            self.db.save_search_item(
                {
                    "search_id": self.options.ongoing.search_id,
                    "web_name": product_local,
                    "address": product_address,
                    "product_name": product_name,
                    "price": product_price,
                    "keyword": keyword,
                }
            )

            logs.append(
                f"Produto: '{product_name}' em '{product_local}' a {product_price} (palavra chave: {keyword}, endereço: {product_address})"
            )

        self.send_logs(*logs)

    def is_in_captcha(self) -> bool:
        """Confere se o usuário precisa resolver o captcha."""
        # FIXME: confirmar: ela retorna True se precisar, ou se não precisar?

        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "flash"))
            )
        except Exception:
            sleep(1)
            return False

        return True

    def open_captcha_and_warn(self) -> None:
        """Abre a URL de captcha, avisa e aguarda o aviso ser fechado."""

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
        self.send_logs(
            f"Aguardando por {value:.2f}s..."
        )  # TODO: ao invés de enviar um log, enviar um sinal específico que mostra quando está aguardando algo. Tipo, emit("search.sleeping_for", value), e depois emit("search.finished_sleep")
        sleep(value)

    def captcha_wait_loop(self) -> None:  # FIXME: rename
        """Abre o captcha e aguarda o usuário resolver o captcha."""

        if not self.is_connected():
            raise ScraperError("Sem conexão com a rede!")

        self.send_logs("Aguardando usuário resolver o captcha...")
        while self.is_in_captcha():
            # TODO: isso aqui só roda uma vez
            self.open_captcha_and_warn()

    def run(self) -> None:
        for response in self.begin_search():
            # TODO: método eficiente para detectar captchas

            if self.mode != "default":
                break

            match response:
                case SearchResponse.Error(message=message):
                    raise ScraperError(message)
                case SearchResponse.Sleep(duration=duration):
                    # TODO: talvez, ao invés de um sleep grande, fazer sleeps de 0.5s para poder periodicamente verificar se self.stop é verdadeiro.
                    self.smart_sleep(duration)
                case SearchResponse.Default():
                    pass
                case _ as unreachable:
                    assert_never(unreachable)

    def begin_search(self) -> Generator[SearchResponse.All, None, None]:
        Sleep = SearchResponse.Sleep
        Default = SearchResponse.Default
        Error = SearchResponse.Error

        times = self.time_coeff  # TODO: parar de usar isso (em favor do smart_sleep)
        ongoing = self.options.ongoing
        driver = self.driver

        emit("search.began", broadcast=True)

        try:
            driver.get(self.options.url)
        except Exception:
            yield Error("não foi possível abrir o ChromeDriver")

        try:
            # TODO: encontrar uma maneira de usar o self.smart_sleep para isso
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "informe-sefaz-error"))
            )
            driver.find_element(By.ID, "informe-sefaz-error").click()
        except TimeoutException:
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
        except TimeoutException:
            self.captcha_wait_loop()
        finally:
            driver.find_element(By.CLASS_NAME, "location-box").click()
        yield Sleep(0.25)

        # TODO: algo assim:
        # def elem_with_id(id_: str):
        #     return EC.presence_of_element_located((By.ID, id_))
        # def elem_with_class(class_: str):
        #     return EC.presence_of_element_located((By.CLASS_NAME, class_))
        # if elem := self.wd_wait_until(2.0, elem_with_id("add-center")):

        # Botão que abre a opção de inserir o CEP
        try:
            WebDriverWait(driver, 2 * times).until(
                EC.presence_of_element_located((By.ID, "add-center"))
            )
        except TimeoutException:
            self.captcha_wait_loop()
            yield Sleep(0.25)
        finally:
            driver.find_element(By.ID, "add-center").click()
            yield Sleep(0.5)

        # Envia o MUNICIPIO desejado para o input
        driver.find_element(By.CLASS_NAME, "sbar-municipio").send_keys(ongoing.city)
        yield Sleep(0.6)

        # Pressiona o botão que realiza a pesquisa por MUNICIPIO
        driver.find_element(By.CLASS_NAME, "set-mun").click()
        yield Sleep(0.25)

        driver.find_element(By.ID, "aplicar").click()
        yield Sleep(0.25)

        product_count = len(ongoing.products)

        for p_idx, p in enumerate_skip(ongoing.products, start=ongoing.current_product):
            yield Default()

            product = p.name
            keywords = p.keywords

            progress_value = 100 * p_idx / product_count

            self.send_logs(
                f"Começando pesquisa do produto {product} (progresso: {progress_value:.0f}%)"
            )
            emit("search.began_searching_product", product)
            emit("search.update_progress_bar", progress_value, broadcast=True)

            for k_idx, keyword in enumerate_skip(
                keywords, start=ongoing.current_keyword
            ):
                yield Default()

                self.send_logs(f"Próxima palavra chave: {keyword}")

                duration = (
                    get_time_hms(self.start_time)["minutes"]
                    + self.options.duration_mins
                )

                self.send_logs("Atualizando backup...")
                ongoing.current_product = p_idx
                ongoing.current_keyword = k_idx
                self.db.update_ongoing_search(ongoing)

                yield Sleep(1)

                # Barra de pesquisa superior (produtos)
                try:
                    WebDriverWait(driver, 3 * times).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "sbar-input"))
                    )
                except Exception:
                    self.captcha_wait_loop()
                finally:
                    search_bar = driver.find_element(By.ID, "top-sbar")

                self.send_logs("Digitando palavra chave...")
                for w in keyword:
                    search_bar.send_keys(w)
                    sleep(0.25)
                search_bar.send_keys(Keys.ENTER)

                yield Sleep(2)

                driver.page_source.encode("utf-8")

                self.send_logs("Aguardando a pesquisa da palavra chave terminar...")
                # o processo é reconhecido como terminado quando a classe flex-item2 está presente, que é uma classe de estilo dos elementos listados.
                try:
                    WebDriverWait(driver, 4 * times).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "flex-item2"))
                    )
                except Exception:
                    self.captcha_wait_loop()
                    yield Sleep(1)

                flag = 0
                while True:
                    yield Default()

                    try:
                        WebDriverWait(driver, 2 * times).until(
                            EC.presence_of_element_located((By.ID, "updateResults"))
                        )
                        yield Sleep(2)

                        driver.find_element(By.ID, "updateResults").click()
                        flag += 1

                        if flag == 3:
                            break
                    except Exception:
                        if not self.is_in_captcha():
                            break
                        self.captcha_wait_loop()

                yield Default()

                self.get_data(product, keyword)

        yield Default()

        duration = get_time_hms(self.start_time)

        search = self.db.get_search_by_id(ongoing.search_id)
        assert search is not None
        search._done = True
        search.total_duration_mins = duration["minutes"] + self.options.duration_mins
        self.db.update_search(search)

        self.send_logs("Deletando backup...")
        self.db.delete_ongoing_search_by_id(ongoing.search_id)
