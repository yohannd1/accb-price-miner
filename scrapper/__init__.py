""" Script responsável por realizar o scrapping na plataforma do Preço da Hora Bahia. """
import re
import time
import csv
import os
import threading
from bs4 import BeautifulSoup
import bs4
import json
import sys
import urllib.request
import database
from numpy import append, product
import pandas as pd
from xlsxwriter.workbook import Workbook
from tkinter import messagebox
from datetime import date
from tkinter import *
import tkinter as tk
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from openpyxl.styles import Border, Side, Alignment
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import webbrowser
from threading import Event

try:
    from win10toast import ToastNotifier
except ImportError:
    pass

from flask_socketio import SocketIO, send, emit


class Scrap:
    """
    Classe responsável por realizar o scrapping na página do Preço da Hora Bahia.

    Attributes:
            LOCALS (string): Array de estabelecimentos que será relaizado a pesquisa.
            LOCALS_NAME (string): Array de nomes dos estabelecimentos que será relaizado a pesquisa.
            BUTTON (tk.Button): Instância do botão da janela inicial da aplicação.
            PAUSE_BUTTON (tk.Button): Instância do botão da janela de pesquisa da aplicação.
            TK (tk.Window): Instância da janela principal da aplicação.
            TXT (tk.ProgressBar): Instância da barra de progresso.
            BACKUP (boolean): Indica se a pesquisa iniciada é um backup ou não.
            INTERFACE (Interface.self): Instância da classe Interface.
    """

    def __init__(self, LOCALS, CITY, LOCALS_NAME, PRODUCT_INFO, ACTIVE, ID, BACKUP):

        print(LOCALS)
        print("\n")
        print(LOCALS_NAME)
        print("\n")
        print(CITY)
        print("\n")
        print(PRODUCT_INFO)
        print("\n")
        print(BACKUP)
        print("\n")
        print(ACTIVE)
        print("\n")
        print(ID)

        self.win = tk.Tk()

        self.win.withdraw()

        # OUT
        self.ID = ID
        self.ACTIVE = ACTIVE
        self.LOCALS = LOCALS
        self.CITY = CITY
        self.LOCALS_NAME = LOCALS_NAME
        self.BACKUP = BACKUP
        self.PRODUCT_INFO = PRODUCT_INFO
        self.db = database.Database()
        self.index, self.index_k = [int(x) for x in ACTIVE.split(".")]
        # IN
        self.progress_value = 100 / len(PRODUCT_INFO[self.index :])
        self.csvfile = None
        self.all_file = None
        self.driver = None
        self.ico = None
        self.stop = False
        self.exit = False

    def filter_word(self, product_name, product):

        # Se o endereço não tiver sido cadastrado
        if product_name == "":
            return True

        words = product_name.split(" ")

        found_product = False

        for word in words:

            if word in product:

                found_product = True

            else:

                found_product = False

        return found_product

    def connect(self):
        """Confere a conexão com o host desejado."""
        host = "https://www.youtube.com"
        try:
            urllib.request.urlopen(host)
            return True
        except:
            return False

    def resource_path(self, relative_path):
        """Retorna o caminho relativo do ícone dentro da pasta de cache gerada pelo pyinstaller (Pacote usado para gerar o arquivo executável da aplicação)."""
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        self.ico = os.path.join(base_path, relative_path)

    # CHECK

    def exit_thread(self):
        """
        Pausa a pesquisa caso aconteça um erro de rede ou o usuário pause-a manualmente.

        Attributes:
                thread (Tread): Instância da classe Tread.
                change_frame (Interface.change_frame): Função responsável por mudar o frame renderizado atualmente.
                frame (tk.Frame): Instância da janela principal da aplicação.
                frame_bar (tk.Frame): Instância da janela de pesquisa da aplicação.
                show_message (Interface.show_message): Função que mostra uma mensagem x em pop up.

        """
        self.stop = True

        if self.exit:

            emit(
                "search",
                {
                    "type": "pause",
                    "message": "A pesquisa foi pausada, todos os dados foram salvos no banco de dados local.",
                },
                broadcast=True,
            )
            self.driver.close()
            self.driver.quit()
            return

        else:

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

    def remove_duplicates(self, file_name):
        """Remove entradas duplicadas do arquivo final xlsx."""
        file_df = pd.read_excel(file_name + ".xlsx", skiprows=0, index_col=0)

        # Mantem somente a primeira duplicata
        pd_first = file_df.drop_duplicates(
            subset=["PRODUTO", "ESTABELECIMENTO", "PRECO"], keep="first"
        )
        # pd_first = file_df.drop_duplicates(subset=["PRODUTO", "ESTABELECIMENTO", "ENDERECO", "PRECO"], keep="first")
        size = pd_first["PRODUTO"].count()
        writer = pd.ExcelWriter(file_name + ".xlsx", engine="xlsxwriter")
        pd_first = pd_first.to_excel(
            writer, sheet_name="Pesquisa", index=False, startrow=0, startcol=1
        )

        workbook = writer.book
        worksheet = writer.sheets["Pesquisa"]
        formats = workbook.add_format({"border": 2})

        worksheet.set_column(1, size, None, formats)
        worksheet.set_column(1, 1, 35)
        worksheet.set_column(2, 2, 60)
        worksheet.set_column(3, 3, 23)
        worksheet.set_column(4, 4, 60)
        worksheet.set_column(5, 5, 12)

        writer.save()

    # OUT
    def csv_to_xlsx(self, csvfile):
        """Converte um arquivo csv em um arquivo xlsx."""
        with pd.ExcelWriter(csvfile[:-4] + ".xlsx") as ew:
            pd.read_csv(csvfile[:-4] + ".csv").to_excel(ew, sheet_name="Pesquisa")

        # workbook = Workbook(csvfile[:-4] + '.xlsx')
        # worksheet = workbook.add_worksheet()
        # formats = workbook.add_format({'border': 2})

        # with open(csvfile, 'rt', encoding='latin-1') as f:
        # 	reader = csv.reader(f)
        # 	for r, row in enumerate(reader):
        # 		for c, col in enumerate(row):

        # 			if r == 3 and c == 3:

        # 				worksheet.set_column(r+1, c+1, 15)

        # 			else:

        # 				worksheet.set_column(r+1, c+1, 50)

        # 			worksheet.write(r+1, c+1, col, formats)

        # workbook.close()

    def set_viewport_size(self, width, height):
        """Muda o tamanho da janela do navegador."""
        window_size = self.driver.execute_script(
            """
			return [window.outerWidth - window.innerWidth + arguments[0],
			window.outerHeight - window.innerHeight + arguments[1]];
			""",
            width,
            height,
        )
        self.driver.set_window_size(*window_size)

    # CHECK FOR BUGS UTF8
    def get_data(self, product, keyword):
        """
        Filtra os dados da janela atual aberta do navegador e os salva no arquivo CSV.

        Attributes:
                writer (file): Instância de um 'escritor' de arquivo.
                product (string): Produto atual da pesquisa.
                keyword (string): Palavra chave atual sendo pesquisa.

        """

        elements = self.driver.page_source
        soup = bs4.BeautifulSoup(elements, "html.parser")
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

            self.db.db_save_search_item(
                {
                    "search_id": self.ID,
                    "city_name": self.CITY,
                    "web_name": product_local,
                    "adress": product_local,
                    "product_name": product_name,
                    "price": product_price,
                }
            )
            # writer.writerow([str(product_name), str(product_local), str(keyword),  str(product_adress), str(product_price)])
            print(
                "------------------------------------------------------------------------------------"
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

        # result = messagebox.showinfo(
        #     "CAPTCHA", "Captcha foi ativado, abra o site do preço da hora e resolva-o em seu navegador e pressione OK para continuar", icon='warning')

        emit(
            "captcha",
            {
                "type": "captcha",
                "message": "Captcha foi ativado, foi aberto uma aba no seu navegador, resolva-o e pressione okay.",
            },
            broadcast=True,
        )

        # print('emit - popup')
        # time.sleep(30)

        # query = "SELECT captcha FROM search WHERE id = '{}' ORDER BY id ASC".format(
        #     self.ID)
        # result = self.db.db_run_query(query)[0]

        result = messagebox.showinfo(
            "CAPTCHA",
            "Captcha foi ativado, abra o site do preço da hora e resolva-o em seu navegador e pressione OK para continuar",
            icon="warning",
        )

        if result:

            self.driver.back()

    def captcha(self):
        """Trata por erro de rede e inicia um loop para conferir se o usuário resolveu o captcha."""
        # Se eu tenho conexão o captcha foi ativado, se não, é erro de rede.

        webbrowser.open(self.url)

        if self.connect():

            while True:

                if self.check_captcha(1):

                    self.pop_up()

                else:

                    # print("CAPTCHA FALSE")
                    return
        else:

            self.exit_thread(None, None, None, None, None)

    # REDO
    def filter_xlsx(self, file_name, city_name, folder_name):

        df = pd.read_excel(file_name, skiprows=0, index_col=0)
        estab_list = self.LOCALS
        local = self.LOCALS_NAME
        keywords = self.KEYWORDS
        appended_data = []

        for index, (product, keyword) in enumerate(keywords):

            keyword = keyword.split(" ")
            appended_data.append(
                df[df.apply(lambda r: all([kw in r[0] for kw in keyword]), axis=1)]
            )

        df = pd.concat(appended_data)
        df = df.sort_values(by=["KEYWORD", "PRECO"], ascending=[True, True])
        df = df.reset_index(drop=True)

        for index, (new_file, adress, estab, date) in enumerate(estab_list):

            new_file = local[index]
            print(
                "Gerando Arquivo ... {}.xlsx , CIDADE : {}".format(new_file, city_name)
            )

            temp_df = df
            path = "{}\{}.xlsx".format(folder_name, new_file)
            print(estab.upper())
            temp_df = temp_df[temp_df.ESTABELECIMENTO.str.match(estab.upper())]
            # temp_df = temp_df[temp_df.ENDERECO.str.contains(adress.upper())]

            writer = pd.ExcelWriter(path, engine="openpyxl")

            temp_df = temp_df.to_excel(
                writer, sheet_name="Pesquisa", index=False, startrow=0, startcol=1
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
                column = col[0].column_letter  # Get the column name
                for cell in col:
                    try:  # Necessary to avoid error on empty cells
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = (max_length + 2) * 1.2
                worksheet.column_dimensions[column].width = adjusted_width

            writer.save()

    def run(self):
        """
        Realiza a pesquisa na plataforma do Preço da Hora Bahia.

        Attributes:
                csvfile (string): Caminho para o arquivo CSV.
                all_file (string): Caminho para o arquivo CSV Todos.
                driver (selenium.Driver): Instância do objeto responsável por realizar a automação do browser.
                start_prod (int): Indíce de inicio do produto caso seja uma pesquisa por backup.
                start_key (int): Indíce de inicio de palavra chave caso seja uma pesquisa por backup.

        """
        URL = "https://precodahora.ba.gov.br/produtos"
        self.url = URL
        times = 4
        start_prod = 0
        start_key = 0
        restart = True
        csvfile = ""

        self.resource_path("logo.ico")
        chrome_options = Options()
        # DISABLES DEVTOOLS LISTENING ON
        # chrome_options.add_argument("--headless")
        # chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-features=NetworkService")
        chrome_options.add_argument("--window-size=1920x1080")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        driver = webdriver.Chrome(
            executable_path=ChromeDriverManager().install(), options=chrome_options
        )
        self.driver = driver
        self.set_viewport_size(800, 600)

        os.system("cls" if os.name == "nt" else "clear")

        driver.get(URL)

        try:

            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "informe-sefaz-error"))
            )

            driver.find_element_by_id("informe-sefaz-error").click()

        except:

            # print("Pop Up Error")
            pass

        # # * Processo de pesquisa de produto

        # time.sleep(times)

        # * Processo para definir a região desejada para ser realizada a pesquisa

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

            # emit(
            #     "captcha",
            #     {
            #         "type": "notification",
            #         "message": "Pesquisando produto {}".format(product),
            #     },
            #     broadcast=True,
            # )

            emit(
                "captcha",
                {"type": "progress", "product": product, "value": ""},
                broadcast=True,
            )

            for index_k, keyword in enumerate(keywords.split(",")[self.index_k :]):

                # if not self.connect():

                # 	self.exit_thread(None, None, None, None, None)
                # 	return

                if self.stop:

                    self.exit = True
                    return

                # if not self.connect():

                # 	self.exit_thread(None, None, None, None, None)
                # 	return

                # self.backup_save(index + start_prod, day, 0,self.LOCALS_NAME, self.CITY,  self.LOCALS)
                active = "{}.{}".format(index + self.index, index_k + self.index_k)
                print("active = {}".format(active))
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
                        return

                    self.get_data(product, keyword)

            emit(
                "captcha",
                {"type": "progress", "product": product, "value": self.progress_value},
                broadcast=True,
            )

        if self.stop:

            self.exit = True
            return

        # self.csv_to_xlsx(all_file)
        # self.remove_duplicates(self.all_file_dir)
        # self.filter_xlsx(self.all_file_dir + ".xlsx", self.CITY, self.folder_name)
        # GERAR O XLSX BASEADO NO BANCO DE DADOS , SEARCH_ITEM COM JOIN EM SEARCH_ID = self.ID

        self.db.db_update_search({"id": self.ID, "done": 1})

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
            }
        )

        emit("captcha", {"type": "notification", "message": "Pesquisa concluida."})
        emit(
            "captcha",
            {"type": "progress", "product": product, "done": 1},
            broadcast=True,
        )

        driver.close()
        driver.quit()
