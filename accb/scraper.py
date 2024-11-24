"""Módulo de pesquisa via scraping."""

from __future__ import annotations

import re
from time import sleep, time
import webbrowser
import random
from typing import Literal, assert_never
from urllib.request import urlopen
from urllib.error import URLError
from datetime import datetime

from bs4 import BeautifulSoup
from flask_socketio import emit
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import Chrome
from selenium.webdriver.remote.webelement import WebElement

from accb.utils import log, show_warning, enumerate_skip, Defer
from accb.state import State
from accb.model import OngoingSearch, SearchItem


class ScraperError(Exception):
    """Erro genérico do Scraper"""


class ScraperInterrupt(Exception):
    """Avisa que o scraper foi interrompido."""


class ScraperRestart(Exception):
    """Avisa que o scraper foi interrompido e precisa ser reiniciado."""


ScraperMode = Literal["default", "errored", "cancelled", "paused"]


class Scraper:
    """Realiza o scraping na página do Preço da Hora Bahia."""

    def __init__(self, ongoing: OngoingSearch, state: State, driver: Chrome) -> None:
        self.ongoing = ongoing
        self.state = state
        self.driver = driver
        self.db = self.state.db_manager

        self.mode: ScraperMode = "default"

        self.start_time_secs = time()
        """Valor do tempo no inicio da pesquisa."""

        self.time_coeff = 4.0
        """Valor usado no cálculo de tempo"""

        self.sleep_step = 1.0
        """Unidade de tempo quando aguardando algo. Geralmente são feitas verificações a cada unidade."""

        self.url = "https://precodahora.ba.gov.br/produtos"
        """URL onde ocorrem as pesquisas"""

    def pause(self) -> None:
        self.mode = "paused"

    def cancel(self) -> None:
        self.mode = "cancelled"

    @staticmethod
    def _is_connected(test_url: str = "https://www.example.org/") -> bool:
        """Confere a conexão com a URL desejada."""

        try:
            with urlopen(test_url):
                return True

        except URLError:
            return False

    def _delete_related_search(self) -> None:
        db = self.state.db_manager
        id_ = self.ongoing.search_id
        db.delete_ongoing_search_by_id(id_)
        db.delete_search_by_id(id_)

    def finalize_search(self) -> None:
        match self.mode:
            case "default":
                pass

            case "errored":
                pass

            case "cancelled":
                self._delete_related_search()

            case "paused":
                pass

            case _ as unreachable:
                assert_never(unreachable)

    def send_logs(self, *messages: str) -> None:
        if len(messages) == 0:
            return

        if len(messages) == 1:
            final = messages[0]
        else:
            final = "\n" + str.join("\n", [f"  {msg}" for msg in messages])

        log(f"[Scraper.send_logs]: {final}")
        emit("search.log", list(messages), broadcast=True)

    def _send_warning(self, warning: str) -> None:
        now = datetime.now()

        self.send_logs(f"AVISO: {warning}")

        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        self.db.add_log(warning, timestamp, self.ongoing.search_id)

    def _extract_and_save_data(self, product: str, keyword: str) -> None:
        """Filtra os dados da janela atual aberta do navegador e os salva no banco de dados."""

        elements = self.driver.page_source
        soup = BeautifulSoup(elements, "html.parser")
        logs = []

        irrelevant_patt = re.compile(r"[^A-Za-z0-9,]+")
        money_patt = re.compile(r" R\$ \d+(,\d{1,2})")

        def adjust_and_clean(x: str) -> str:
            return irrelevant_patt.sub(" ", x).lstrip()

        all_elements = list(soup.find_all(True, {"class": "flex-item2"}))

        if len(all_elements) == 0:
            self._send_warning(
                f"Nenhum item encontrado com palavra-chave {keyword} (produto {product})"
            )

        for item in all_elements:
            product_name = adjust_and_clean(item.find("strong").text)
            product_address = adjust_and_clean(
                item.find(attrs={"data-original-title": "Endereço"}).parent.text
            )
            product_local = adjust_and_clean(
                item.find(attrs={"data-original-title": "Estabelecimento"}).parent.text
            )
            product_price = item.find(text=money_patt).lstrip()

            self.db.save_search_item(
                SearchItem(
                    search_id=self.ongoing.search_id,
                    web_name=product_local,
                    address=product_address,
                    product_name=product_name,
                    price=product_price,
                    keyword=keyword,
                )
            )

            logs.append(
                f"Produto: {repr(product_name)} em {repr(product_local)} a {product_price} (palavra chave: {keyword}, endereço: {product_address})"
            )

        self.send_logs(*logs)

    def _sleep(self, base: float) -> None:
        """Calcula um tempo aleatório baseado em `base * self.time_coeff`, e logo depois avisa e aguarda por tal tempo.

        A cada `self.sleep_step` segundos, verifica se a pesquisa foi cancelada, e para se este for o caso.
        """

        min_time = 0.2
        sleep_time = max(min_time, base * self.time_coeff + random.uniform(-1.0, 1.0))

        emit("search.started_waiting", sleep_time, broadcast=True)

        start_time_secs = time()
        while True:
            slept_so_far = time() - start_time_secs
            remaining_time_secs = sleep_time - slept_so_far
            if remaining_time_secs <= 0.0:
                break

            to_sleep_now = min(remaining_time_secs, self.sleep_step)
            sleep(to_sleep_now)

            self._check_interrupt()

        emit("search.finished_waiting", broadcast=True)

    def _check_interrupt(self) -> None:
        if self.mode == "default":
            return

        if self.mode == "paused":
            raise ScraperInterrupt(
                "Pesquisa pausada com sucesso - progresso salvo no banco de dados."
            )

        if self.mode == "cancelled":
            raise ScraperInterrupt("Pesquisa cancelada com sucesso.")

        if self.mode == "errored":
            # XXX: acho que isso aqui nunca acontece (esse estado só ocorre quando o exception handler pega um Exception de qualquer modo), mas vai que.
            raise ScraperInterrupt("Pesquisa cancelada por erro.")

        raise ScraperInterrupt("Pesquisa interrompida por motivo desconhecido.")

    def _check_connection(self) -> None:
        if not self._is_connected():
            raise ScraperError("Sem conexão com a rede!")

    def _check_captcha(self) -> None:
        if self._is_in_captcha():
            # a página inicial redireciona automaticamente p/ a URL de captcha
            webbrowser.open(self.url)
            self.send_logs("Aguardando usuário resolver o captcha...")

            show_warning(
                title="CAPTCHA",
                message=(
                    "Um captcha foi detectado.\n"
                    "Foi aberta uma aba no seu navegador - resolva-o e depois pressione OK nesta mensagem.\n"
                    "Se a aba não tiver um captcha, pode fechá-la (foi um falso positivo)."
                ),
            )

            self.mode = "paused"
            raise ScraperRestart()

    def _is_in_captcha(self) -> bool:
        def check() -> bool:
            return self.driver.current_url == "https://precodahora.ba.gov.br/challenge/"

        if check():
            self.send_logs(
                "Parece que um captcha foi encontrado. Aguardando mais um pouco..."
            )
            self._sleep(1.0)
            return check()

        return False

    def _get_duration_mins_and_reset(self) -> float:
        """Retorna a duração desde o tempo iniciado e reseta o timer."""

        now_secs = time()
        elapsed_secs = now_secs - self.start_time_secs
        self.start_time_secs = now_secs

        return elapsed_secs / 60.0

    def _wait_for_element(
        self, by: str, value: str, timeout: float
    ) -> WebElement | None:
        def deinit(_) -> None:
            emit("search.finished_waiting", broadcast=True)

        emit("search.started_waiting", timeout, broadcast=True)

        with Defer(None, deinit=deinit):
            self._check_connection()

            start_time_secs = time()
            while True:
                self._check_interrupt()

                slept_so_far = time() - start_time_secs
                remaining_time_secs = timeout - slept_so_far
                if remaining_time_secs <= 0.0:
                    break
                to_sleep_now = min(remaining_time_secs, self.sleep_step)

                try:
                    ec = EC.presence_of_element_located((by, value))
                    WebDriverWait(self.driver, to_sleep_now).until(ec)
                    return self.driver.find_element(by, value)
                except TimeoutException:
                    pass

            self._check_interrupt()
            self._check_captcha()
            return None

    def _wait_for_element_or_captcha(
        self, by: str, value: str, timeout: float
    ) -> WebElement:
        elem = self._wait_for_element(by, value, timeout)
        return elem or self.driver.find_element(by, value)

    def begin_search(self) -> None:
        ongoing = self.ongoing
        driver = self.driver

        emit("search.began", broadcast=True)

        self.send_logs(f"Carregando página (URL: {self.url})...")

        driver.get(self.url)

        wait_for_element = self._wait_for_element
        wait_for_element_or_captcha = self._wait_for_element_or_captcha

        if elem := wait_for_element(By.ID, "informe-sefaz-valor", 2.5):
            elem.click()

        self.send_logs("Especificando localização...")

        # botão que abre o modal referente a localização
        wait_for_element_or_captcha(By.CLASS_NAME, "location-box", 12.0).click()
        self._sleep(0.5)

        # botão que abre a opção de inserir o CEP
        wait_for_element_or_captcha(By.ID, "add-center", 8.0).click()
        self._sleep(0.5)

        # envia o município desejado para a barra de pesquisa
        sbar_municipio = driver.find_element(By.CLASS_NAME, "sbar-municipio")
        for w in ongoing.city:
            sbar_municipio.send_keys(w)
            sleep(0.05)
        self._sleep(0.5)

        # seleciona o município na lista
        driver.find_element(By.CLASS_NAME, "set-mun").click()
        self._sleep(0.25)

        # confirma a escolha
        driver.find_element(By.ID, "aplicar").click()
        self._sleep(0.25)

        product_count = len(ongoing.products)

        ongoing.duration_mins += self._get_duration_mins_and_reset()
        self.db.update_ongoing_search(ongoing)

        for p_idx, p in enumerate_skip(ongoing.products, start=ongoing.current_product):
            progress_value = 100 * p_idx / product_count

            self.send_logs(
                f"Começando pesquisa do produto {p.name} (progresso: {progress_value:.0f}%)"
            )
            emit("search.began_searching_product", p.name)
            emit("search.update_progress_bar", progress_value, broadcast=True)

            for k_idx, keyword in enumerate_skip(
                p.keywords, start=ongoing.current_keyword
            ):
                if keyword == "CARNE BOVINA CHA DE DENTRO":
                    # FIXME: resolver isso. essa pesquisa em específico não está funcionando no price miner
                    continue

                self.send_logs(f"Próxima palavra chave: {keyword}")

                self.send_logs("Atualizando backup...")
                ongoing.duration_mins += self._get_duration_mins_and_reset()
                ongoing.current_product = p_idx
                ongoing.current_keyword = k_idx
                self.db.update_ongoing_search(ongoing)

                # barra de pesquisa superior (produtos)
                e_top_sbar = wait_for_element_or_captcha(By.ID, "top-sbar", 12.0)

                self.send_logs("Digitando palavra chave...")

                for w in keyword:
                    e_top_sbar.send_keys(w)
                    sleep(0.05)
                e_top_sbar.send_keys(Keys.ENTER)
                self._sleep(1)

                driver.page_source.encode("utf-8")

                # o processo é reconhecido como terminado quando a classe flex-item2 está presente, que é uma classe de estilo dos elementos listados.
                self.send_logs("Aguardando a pesquisa da palavra chave terminar...")
                _ = wait_for_element_or_captcha(By.CLASS_NAME, "flex-item2", 16.0)

                # apertar algumas vezes o botão de mostrar mais resultados na lista
                update_threshold = 3.0
                update_counter = 0.0
                while True:
                    if e_update_results := wait_for_element(
                        By.ID, "updateResults", 8.0
                    ):
                        e_update_results.click()
                        update_counter += 1
                    else:
                        # se falhou, aumentar menos, para dar mais chances de procurar mais vezes
                        update_counter += 0.5

                    self._sleep(0.2)

                    if update_counter >= update_threshold:
                        break

                self._extract_and_save_data(p.name, keyword)

            # voltar para o índice 0 de keyword (para não pular keywords do próximo produto)
            ongoing.current_keyword = 0

        for estab in ongoing.estabs:
            if (
                self.db.get_item_count_with(search_id=ongoing.search_id, estab=estab)
                == 0
            ):
                self._send_warning(
                    f"Nenhum produto foi encontrado para o estabelecimento {estab.name}"
                )

        search = self.db.get_search_by_id(ongoing.search_id)
        assert search is not None
        ongoing.duration_mins += self._get_duration_mins_and_reset()
        search.total_duration_mins = ongoing.duration_mins
        self.db.update_search(search)

        self.send_logs("Deletando backup...")
        self.db.delete_ongoing_search_by_id(ongoing.search_id)
