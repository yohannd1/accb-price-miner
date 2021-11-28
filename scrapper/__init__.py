#!/usr/bin/python
# -*- coding: utf-8 -*-

""" Script responsável por realizar o scrapping na plataforma do Preço da Hora Bahia. """
import re
import time
import os
from bs4 import BeautifulSoup
import bs4
import json
import sys
import urllib.request
import database
from tkinter import messagebox
from tkinter import *
import tkinter as tk
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import webbrowser
from flask_socketio import SocketIO, send, emit
import time


class Scrap:
    """
    Classe responsável por realizar o scrapping na página do Preço da Hora Bahia.
    """

    def __init__(
        self,
        LOCALS,
        CITY,
        LOCALS_NAME,
        PRODUCT_INFO,
        ACTIVE,
        ID,
        BACKUP,
        DURATION,
        PROGRESS_VALUE,
    ):

        self.win = tk.Tk()
        self.win.withdraw()

        # OUT
        self.ID = ID
        """ ID da pesquisa atual."""
        self.ACTIVE = ACTIVE
        """Valor decimal de indexes ativos 1.1, onde 1. é o index do produto e .1 é o index da palavra chave."""
        self.LOCALS = LOCALS
        """Array de estabelecimentos que será relaizado a pesquisa."""
        self.CITY = CITY
        """Nome da cidade para realizar a pesquisa."""
        self.LOCALS_NAME = LOCALS_NAME
        """Array de nomes estabelecimentos que será relaizado a pesquisa."""
        self.BACKUP = BACKUP
        """Variavel booleana que indica se é um backup ou não."""
        self.duration = DURATION
        """Armazena a duração de tempo atual de execução da pesquisa (necessário para reinicialização através de backup)."""
        self.PRODUCT_INFO = PRODUCT_INFO
        """Array de produtos e para realizar a pesquisa."""
        self.db = database.Database()
        """Instância da classe Database, responsável pelas operações do banco de dados."""
        self.index, self.index_k = [int(x) for x in ACTIVE.split(".")]
        """Index dos produtos e palavras chaves (em caso de reinicialização através de backup);"""
        # IN
        self.progress_value = PROGRESS_VALUE
        """Valor de soma da barra de pesquisa, caso seja adicionado um novo produto é necessário manter os dados da pesquisa anterior."""
        self.driver = None
        """Instância do navegador do selenium."""
        self.stop = False
        """Variável de controle para parar a execução da pesquisa."""
        self.exit = False
        """Variável de controle para sair a execução da pesquisa."""
        self.cancel = False
        """Variável de controle para cancelar a execução da pesquisa."""
        self.start_time = time.time()
        """Valor do tempo no inicio da pesquisa."""

    def get_time(self, start):
        """Calcula o tempo de execução dado um tempo inicial e retorna o tempo em minutos horas e segundos."""

        end = time.time()
        temp = end - start
        # print(temp)
        hours = temp // 3600
        temp = temp - 3600 * hours
        minutes = temp // 60
        seconds = temp - 60 * minutes
        return {"minutes": minutes + (60 * hours), "seconds": seconds, "hours": hours}

    def log_progress(self, progress):

        """Função para debugar o processo de coleta, imprime no arquivo progress.log o progresso desejado da pesquisa."""
        with open("progress.log", "w+") as outfile:

            outfile.write("Date : {} \n".format(time.asctime()))
            for index, line in enumerate(progress):
                outfile.write("Index {} : {}\n".format(index, line))

        return

    def connect(self):
        """Confere a conexão com o host desejado."""
        host = "https://www.youtube.com"
        try:
            urllib.request.urlopen(host)
            return True
        except:
            return False

    def pause(self, cancel=False):

        """Seta as varáveis de controle do programa (parada, cancelar e saída)."""
        self.cancel = cancel
        self.exit = True
        self.stop = True

    # CHECK

    def exit_thread(self, error=False):
        """
        Pausa a pesquisa caso aconteça um erro de rede ou o usuário pause-a ou cancele manualmente.

        """
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
        """
        Filtra os dados da janela atual aberta do navegador e os salva no banco de dados.
        """

        elements = self.driver.page_source
        soup = bs4.BeautifulSoup(elements, "html.parser")
        arr = []
        # search_item["search_id"], search_item["city_name"], search_item["estab_name"], search_item["web_name"], search_item["adress"], search_item["price"])
        for item in soup.findAll(True, {"class": "flex-item2"}):

            print(
                "------------------------------------------------------------------------------------"
            )
            product_name = re.sub(
                "[^A-Za-z0-9,]+", " ", item.find("strong").text
            ).lstrip()
            product_adress = re.sub(
                "[^A-Za-z0-9,]+",
                " ",
                item.find(attrs={"data-original-title": "Endereço"}).parent.text,
            ).lstrip()
            product_local = re.sub(
                "[^A-Za-z0-9,]+",
                " ",
                item.find(attrs={"data-original-title": "Estabelecimento"}).parent.text,
            ).lstrip()
            product_price = item.find(text=re.compile(r" R\$ \d+(,\d{1,2})")).lstrip()

            print(
                "Endereço:{}\nEstabelecimento:{}\nPreço:{}\nNome:{}".format(
                    product_adress, product_local, product_price, product_name
                )
            )
            try:
                if not self.stop:
                    self.db.db_save_search_item(
                        {
                            "search_id": self.ID,
                            "web_name": product_local,
                            "adress": product_adress,
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
                            str(product_adress),
                            str(product_price),
                        ]
                    )
                    # self.log_progress(item)
            except:
                pass
            print(
                "------------------------------------------------------------------------------------"
            )
        if not self.stop:
            emit(
                "captcha",
                {
                    "type": "log",
                    "data": json.dumps(arr),
                },
                broadcast=True,
            )

    def check_captcha(self, request=0):
        """Função que confere se o captcha foi resolvido com sucesso pelo usuário."""
        excpt = True

        try:

            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "flash"))
            )

        except:

            # print("Captcha desativado.")
            time.sleep(1)
            excpt = False
            return False

        finally:

            if excpt:

                # print("Captcha ativado.")

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

        result = messagebox.showinfo(
            "CAPTCHA",
            "Captcha foi ativado, foi aberto uma aba no seu navegador, resolva-o e pressione okay",
            icon="warning",
        )

        if result:

            self.driver.back()

    def captcha(self):
        """Trata por erro de rede e inicia um loop para conferir se o usuário resolveu o captcha."""

        # Se eu tenho conexão o captcha foi ativado, se não, é erro de rede.

        if self.connect():

            while True:

                if self.check_captcha(1):

                    webbrowser.open(self.url)
                    self.pop_up()

                else:

                    # print("CAPTCHA FALSE")
                    return
        else:

            self.exit_thread(True)

    def run(self):
        """
        Realiza a pesquisa na plataforma do Preço da Hora Bahia.

        """

        URL = "https://precodahora.ba.gov.br/produtos"
        self.url = URL
        times = 4
        try:
            chrome_options = Options()
            # # DISABLES DEVTOOLS LISTENING ON
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-features=NetworkService")
            chrome_options.add_argument("--window-size=1920x1080")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            os.environ["WDM_LOCAL"] = "1"

            manager = ChromeDriverManager(log_level=0).install()
            service = Service(manager)
            driver = webdriver.Chrome(service=service, chrome_options=chrome_options)

            self.driver = driver

            os.system("cls" if os.name == "nt" else "clear")

            driver.get(URL)
        except:
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

            driver.find_element_by_id("informe-sefaz-error").click()

        except:

            # print("Pop Up Error")
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

        except:

            self.captcha()
            time.sleep(1)

        finally:

            driver.find_element_by_class_name("location-box").click()
            time.sleep(2 * times)

        # Botão que abre a opção de inserir o CEP
        try:

            WebDriverWait(driver, 2 * times).until(
                EC.presence_of_element_located((By.ID, "add-center"))
            )

        except:

            self.captcha()
            time.sleep(1)

        finally:

            driver.find_element_by_id("add-center").click()
            time.sleep(2 * times)

        # Envia o MUNICIPIO desejado para o input

        driver.find_element_by_class_name("sbar-municipio").send_keys(self.CITY)
        time.sleep(1)

        # Pressiona o botão que realiza a pesquisa por MUNICIPIO
        driver.find_element_by_class_name("set-mun").click()

        time.sleep(1)
        driver.find_element_by_id("aplicar").click()

        time.sleep(2 * times)

        for index, (product, keywords) in enumerate(self.PRODUCT_INFO[self.index :]):

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
                    return

                else:

                    active = "{}.{}".format(index + self.index, index_k + self.index_k)
                    duration = self.get_time(self.start_time)
                    duration = duration["minutes"] + self.duration

                    # self.log_progress(
                    #     [
                    #         active,
                    #         duration,
                    #         self.progress_value,
                    #         self.PRODUCT_INFO[self.index :],
                    #         product,
                    #         keywords,
                    #     ]
                    # )

                    self.db.db_update_backup(
                        {
                            "active": active,
                            "city": self.CITY,
                            "done": 0,
                            "estab_info": json.dumps(
                                {"names": self.LOCALS_NAME, "info": self.LOCALS}
                            ),
                            "product_info": json.dumps(self.PRODUCT_INFO),
                            "search_id": self.ID,
                            "duration": duration,
                        }
                    )

                time.sleep(1.5 * times)

                # Barra de pesquisa superior (produtos)
                try:

                    WebDriverWait(driver, 3 * times).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "sbar-input"))
                    )

                except:

                    self.captcha()

                finally:

                    search = driver.find_element_by_id("top-sbar")

                for w in keyword:

                    search.send_keys(w)
                    time.sleep(0.25)

                # Realiza a pesquisa (pressiona enter)
                search.send_keys(Keys.ENTER)

                time.sleep(3 * times)
                driver.page_source.encode("utf-8")

                if self.stop:

                    self.exit = True
                    self.exit_thread()

                    return
                # Espera a página atualizar, ou seja, terminar a pesquisa. O proceso é reconhecido como terminado quando a classe flex-item2 está presente, que é a classe utilizada para estilizar os elementos listados
                try:

                    WebDriverWait(driver, 4 * times).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "flex-item2"))
                    )

                except:

                    self.captcha()
                    time.sleep(times)

                finally:

                    flag = 0
                    while True:

                        if self.stop:

                            self.exit = True
                            self.exit_thread()

                            return

                        try:

                            WebDriverWait(driver, 2 * times).until(
                                EC.presence_of_element_located((By.ID, "updateResults"))
                            )
                            time.sleep(2 * times)
                            driver.find_element_by_id("updateResults").click()
                            flag = flag + 1

                            if flag == 3:

                                break

                        except:

                            if not self.check_captcha(0):

                                # print("Quantidade máxima de paginas abertas.")
                                break

                            else:

                                self.captcha()

                    if self.stop:

                        self.exit = True
                        self.exit_thread()
                        return

                    self.get_data(product, keyword)

            if not self.stop:
                print("PROGRESS : {}".format(self.progress_value))
                emit(
                    "captcha",
                    {
                        "type": "progress",
                        "product": product,
                        "value": self.progress_value,
                    },
                    broadcast=True,
                )

        if self.stop:

            self.exit = True
            self.exit_thread()
            return

        duration = self.get_time(self.start_time)
        self.db.db_update_search(
            {"id": self.ID, "done": 1, "duration": duration["minutes"] + self.duration}
        )

        self.db.db_update_backup(
            {
                "active": "0.0",
                "city": self.CITY,
                "done": 1,
                "estab_info": json.dumps(
                    {"names": self.LOCALS_NAME, "info": self.LOCALS}
                ),
                "product_info": json.dumps(self.PRODUCT_INFO),
                "search_id": self.ID,
                "duration": duration["minutes"] + self.duration,
            }
        )

        driver.close()
        driver.quit()
        return True
