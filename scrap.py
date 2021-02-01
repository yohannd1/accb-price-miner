import re
import time
import csv
import os
import threading
import json
from xlsxwriter.workbook import Workbook
from tkinter import messagebox
from datetime import date
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
try:
    from win10toast import ToastNotifier
except ImportError:
    pass

def csv_to_xlsx(csvfile):
    
    workbook = Workbook(csvfile[:-4] + '.xlsx')
    worksheet = workbook.add_worksheet()
    formats = workbook.add_format({'border': 2})

    with open(csvfile, 'rt', encoding='latin-1') as f:
        reader = csv.reader(f)
        for r, row in enumerate(reader):
            for c, col in enumerate(row):
                
                if r == 3 and c == 3:
                     
                    worksheet.set_column(r+1, c+1, 15)
                
                else:

                    worksheet.set_column(r+1, c+1, 33)
                
                worksheet.write(r+1, c+1, col, formats)
                
    workbook.close()

def set_viewport_size(driver, width, height):

    window_size = driver.execute_script("""
        return [window.outerWidth - window.innerWidth + arguments[0],
          window.outerHeight - window.innerHeight + arguments[1]];
        """, width, height)
    driver.set_window_size(*window_size)
    # driver.get('chrome://settings/clearBrowserData')
    # time.sleep(3)
    # driver.find_element_by_ID('//settings-ui').click()
    # time.sleep(35)

def get_data(driver, local, writer, product, keyword, all_file):

    found = True
    found_2 = True
    # info = []
    elements = []
    # Lista de Produtos
    time.sleep(2)
    try:
        
        elements = driver.find_elements_by_class_name("flex-item2")

    except:
        
        captcha(driver)
        
    elements = driver.find_elements_by_class_name("flex-item2")
    
    for element in elements:

        # * Processo de aquisição de dados

        try:
            
            # Nome do produto
            product_name = element.find_elements_by_tag_name("strong")[0]
            product_name = product_name.get_attribute('innerHTML')

            # Todas as tags com as informações do bloco do produto
            product_info = element.find_elements_by_tag_name("div")

        except:
            
            captcha(driver)
            
            
        try:
            
            # Nome do produto
            product_name = element.find_elements_by_tag_name("strong")[0]
            product_name = product_name.get_attribute('innerHTML')

            # Todas as tags com as informações do bloco do produto
            product_info = element.find_elements_by_tag_name("div")
        
        except:
            
            captcha(driver)
            
        # Preço do produto
        flag = 0
        if len(element.find_elements_by_class_name("sobre-desconto")) == 0:
            product_price = product_info[1].get_attribute('innerHTML')
        else:
            product_price = product_info[2].get_attribute('innerHTML')
            flag = 1
        
        pattern = re.compile("(?<=>)\s\w..\d?(\d).\d\d")
        product_size = len(product_price)
        product_price = product_price.replace('\n', '')
        product_price = product_price.replace(',', '.')

        if product_size > 15:
            
            if  pattern.search(product_price) != None:
                
                product_price = pattern.search(product_price).group(0)


        # Endereço do produto
        size = len(product_info)

        if size == 9:
            index = 3
        elif size == 10:
            if flag == 1:
                index = 4
            else:
                index = 3
        elif size == 11:
            index = 4
        else:
            index = 3
            

        pattern = re.compile("(?<=>).\w.*\w")
        product_adress = product_info[index].get_attribute('innerHTML')
        product_adress = pattern.search(product_adress).group()
        product_adress = product_adress[1:len(product_adress)]

        # print("Size: " + str(size))
        # print(local)
        # print(product_adress)
        

        if local[0] in str(product_adress):

            if product in str(product_name):
                    
                print('Preço : ' + str(product_price))
                print('Local : ' + str(product_adress))
                print('Produto : ' + str(product_name))
                found = False
                writer.writerow([str(product_name), str(
                    product_adress), str(keyword), str(product_price)])
            
        if local[1] in str(product_adress):

            if product in str(product_name):
                
                print('Preço : ' + str(product_price))
                print('Local : ' + str(product_adress))
                print('Produto : ' + str(product_name))
                found_2 = False
                writer.writerow([str(product_name), str(
                    product_adress), str(keyword), str(product_price)])
            
        if product in str(product_name):
            
            print('Todos ----------------------------')
            print('Preço : ' + str(product_price))
            print('Local : ' + str(product_adress))
            print('Produto : ' + str(product_name))
            print('Todos ----------------------------')
            
            with open(all_file, 'a+', newline='') as file:

                writer_2 = csv.writer(file, delimiter=',')
                writer_2.writerow([str(product_name), str(
                product_adress), str(keyword), str(product_price)])

            csv_to_xlsx(all_file)
            

    if found:
        
        writer.writerow([str(product), str(local[0]),
                         str(keyword), "N/A"])
    
    if found_2:

        writer.writerow([str(product), str(local[1]),
                        str(keyword), "N/A"])

# Captcha
def check_captcha(driver, request):
    
    excpt = True
    if request == 1:
        
        driver.back()
    
    time.sleep(1)
    try:

        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "flash")))

    except:

        # print("Captcha desativado.")
        time.sleep(1)
        excpt = False
        return True

    finally:

        if excpt:
            
            # print("Captcha ativado.")
            return False
    
def pop_up(driver):
    
    result = messagebox.askquestion("CAPTCHA", "Captcha foi ativado, resolva-o em seu navegador e aperte Sim para continuar", icon='warning')
    if result == 'yes' and check_captcha(driver, 1):
        return True
    else:
        return False

def captcha(driver):
    
    while True:

        if pop_up(driver):
            
            break        
# Captcha

# Backup
def backup_check(t_date, estab):

    try:
    
        product = 0
        place = 0
        finish = 0
        keyword = 0
        date = 0
        estab_1 = 0
        estab_2 = 0
        
        with open('backup.json') as json_file:

            data = json.load(json_file)
            for backup in data['backup']:
                
                product = backup['prod']
                date = backup['date']    
                keyword = backup['keyword']
                finish = backup['done']
                estab_1 = backup['estab_1']
                estab_2 = backup['estab_2']
                
        if estab_1 != estab[0] and estab_2 != estab[1]:
            
            return(0,0)

        if t_date != date:
        
            return (0,0)
        
        # Pesquisa acabou
        if finish == -1:
            
            return (0,0)

        # Pesquisa do estabelecimento nao acabou
        if finish == 0:
            
            return (abs(product), abs(keyword))

        # Pesquisa do estebelcimento acabou
        if finish == 1:
            
            return (abs(product), abs(keyword))

    except:
        
        return(0,0)

def backup_save(prod, date, keyword, done, estab, city, place):
    
    
    data = {}
    data['backup'] = []
    data['backup'].append({"prod": prod, "date": date, "keyword" : keyword, "done": done, "estab_1": estab[0], "estab_2": estab[1], "city": city, 'place_1': place[0], 'place_2': place[1]})
    with open('backup.json', 'w+') as outfile:
    
        json.dump(data, outfile)
# Backup

def get_keywords():
    
    keywords = []
    keywords.append(['ACUCAR CRISTAL', 'ACUCAR CRISTAL 1KG'])
    keywords.append(['ARROZ PARBOILIZADO', 'ARROZ PARBOILIZADO 1KG'])
    keywords.append(['BANANA DA PRATA', 'BANANA PRATA', 'BANANA KG'])
    keywords.append(['CAFE 250G', 'CAFE MOIDO'])
    keywords.append(['CHA DE DENTRO', 'COXAO MOLE', 'CARNE BOVINA CHA DE DENTRO'])
    keywords.append(['FARINHA DE MANDIOCA', 'FARINHA MAND', 'FARINHA MANDIOCA'])
    keywords.append(['FEIJAO CARIOCA'])
    keywords.append(['LEITE LIQUIDO'])
    keywords.append(['MANTEIGA 500G', 'MANTEIGA'])
    keywords.append(['OLEO DE SOJA', 'OLEO 900ML', 'OLEO'])
    keywords.append(['PAO FRANCES', 'PAO KG', 'PAO FRANCES KG'])
    keywords.append(['TOMATE KG'])
    
    return keywords

# Scrapper
def scrap(LOCALS, BUTTON, TK, PROGRESS_BAR, TXT, CITY, LOCALS_NAME):

    first  = 0
    URL = 'https://precodahora.ba.gov.br/'
    times = 5
    today = date.today()
    day = today.strftime("%d-%m-%Y")
    start_prod = 0
    start_key = 0
    restart = True
    csvfile = ''
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-features=NetworkService")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")

    driver = webdriver.Chrome(
        executable_path=ChromeDriverManager().install(), options=chrome_options)
    set_viewport_size(driver, 800, 600)

    products =  ['ACUCAR CRISTAL',
                'ARROZ PARBOILIZADO',
                'BANANA DA PRATA',
                'CAFE MOIDO',
                'CHA DE DENTRO',
                'FARINHA DE MANDIOCA',
                'FEIJAO CARIOCA',
                'LEITE LIQUIDO',
                'MANTEIGA 500G',
                'OLEO DE SOJA',
                'PAO FRANCES',
                'TOMATE KG']


    # Requer polimento do algoritmo para garantir a validade das informações
    # Teste da ferramenta Selenium com chromedriver

    start_prod, start_key = backup_check(day, [LOCALS_NAME[0], LOCALS_NAME[1]])
    keywords = get_keywords()
    
    products_backup = products
    
    if start_prod > 0 or start_key > 0:
    
        TXT.set("Retomando pesquisa anterior ...")

    # Define endereço a ser visitado
    driver.get(URL)
    # * Processo de pesquisa de produto
    driver.find_element_by_id('fake-sbar').click()
    time.sleep(1*times)

    TXT.set("Pesquisa iniciada ...")
    
    if os.name == 'nt':

        toaster = ToastNotifier()
        toaster.show_toast("Pesquisa iniciada.",
                    " ",
                    icon_path="logo.ico",
                    duration = 10)
    
    TXT.set("Iniciando arquivos ...")
    # Cria a pasta de pesquisa
    dic = CITY + ' [ ' + day + ' ]'
    if not os.path.exists(dic):

        os.makedirs(dic)

    csvfile = dic + '/' + LOCALS_NAME[0] + ' ' + LOCALS_NAME[1] + '.csv' 
    all_file = dic + '/' + 'TODOS.csv'
    
    # Se arquivo já existe, não preciso inicia-lo
    if start_prod != 0 and restart:
        
        print("restart")
        PROGRESS_BAR['value'] = (start_prod) * (100/len(products_backup))
        products = products[start_prod:]
        keywords = keywords[start_prod:]
        restart = False
        
    else: 
        
        products = products_backup
        # Inicia o arquivo csv com as colunas principais
        with open(csvfile, 'w+', newline='') as file:

            writer = csv.writer(file, delimiter=',')
            writer.writerow(
                ["PRODUTO", "ESTABELECIMENTO", "KEYWORD", "PREÇO"])

        with open(all_file, 'w+', newline='') as file:

            writer = csv.writer(file, delimiter=',')
            writer.writerow(
                ["PRODUTO", "ESTABELECIMENTO", "KEYWORD", "PREÇO"])
        
    for index, product in enumerate(products):
        
        keyword = keywords[index]
        if index == 0 and start_key > 0:
            
            keyword = keyword[start_key:]
        
        TXT.set("Pesquisando Produto : " +'[ '+ product + ' ]' )
        
        
        for key, word in enumerate(keyword):
            
            backup_save(index + start_prod, day, key + start_key, 0, [LOCALS_NAME[0], LOCALS_NAME[1]], CITY, [LOCALS[0], LOCALS[1]])
            
            time.sleep(3*times)
            
            # Barra de pesquisa superior (produtos)
            try:

                WebDriverWait(driver, 2*times).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "sbar-input")))

            except:

                captcha(driver)
                driver.get('https://precodahora.ba.gov.br/produtos')
                time.sleep(2*times)

            finally:

                search = driver.find_element_by_id('top-sbar')

            for w in word:

                search.send_keys(w)
                time.sleep(0.25)

            # Realiza a pesquisa (pressiona enter)
            search.send_keys(Keys.ENTER)

            time.sleep(3*times)
            driver.page_source.encode('utf-8')

            # * Processo para definir a região desejada para ser realizada a pesquisa

            if index == 0:
                
                # Botão que abre o modal referente a localização
                try:

                    WebDriverWait(driver, 2*times).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "location-box")))

                except:

                    captcha(driver)
                    time.sleep(1)
                        
                finally:

                    driver.find_element_by_class_name('location-box').click()
                    time.sleep(2*times)

                # Botão que abre a opção de inserir o CEP
                try:

                    WebDriverWait(driver, 2*times).until(
                        EC.presence_of_element_located((By.ID, "add-center")))

                except:

                    captcha(driver)
                    time.sleep(1)

                finally:

                    driver.find_element_by_id('add-center').click()
                    time.sleep(2*times)

                # Envia o MUNICIPIO desejado para o input

                driver.find_element_by_class_name('sbar-municipio').send_keys(CITY)
                time.sleep(1)

                # Pressiona o botão que realiza a pesquisa por MUNICIPIO
                driver.find_element_by_class_name('set-mun').click()
                
                time.sleep(1)
                driver.find_element_by_id('aplicar').click()

                time.sleep(3*times)
            

            # Espera a página atualizar, ou seja, terminar a pesquisa. O proceso é reconhecido como terminado quando a classe flex-item2 está presente, que é a classe utilizada para estilizar os elementos listados
            try:

                WebDriverWait(driver, 5*times).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "flex-item2")))

            except:

                captcha(driver)
                time.sleep(2*times)

            finally:

                flag = 0
                while True:

                    try:

                        WebDriverWait(driver, 5*times).until(
                            EC.presence_of_element_located((By.ID, "updateResults")))
                        time.sleep(2*times)
                        driver.find_element_by_id('updateResults').click()
                        flag = flag + 1

                        if flag == 3:

                            break

                    except:

                        if check_captcha(driver, 0):
                            
                            print("Quantidade máxima de paginas abertas.")
                            time.sleep(1)
                            break
                            
                        else:
                                    
                            captcha(driver)

                with open(csvfile, 'a+', newline='') as file:

                    writer = csv.writer(file, delimiter=',')
                    get_data(driver, LOCALS, writer, product, word, all_file)
                
                csv_to_xlsx(csvfile)

        max_val = PROGRESS_BAR['value'] + (100/len(products_backup)) + 1
        for x in range(int(PROGRESS_BAR['value']), int(max_val)):
        
            PROGRESS_BAR['value'] = x
            time.sleep(0.01)
            
        if os.name == 'nt' and index == len(products)/2:

            toaster = ToastNotifier()
            toaster.show_toast("Pesquisa na metade ...",
                        " ",
                        icon_path="logo.ico",
                        duration = 10)
    
    time.sleep(1)
    for x in range(100,-1,-1):
        
        PROGRESS_BAR['value'] = x
        time.sleep(0.01)
    
    backup_save(0, day, 0, 1, [LOCALS_NAME[0], LOCALS_NAME[1]], CITY, [LOCALS[0], LOCALS[1]])
    start_prod = 0
        
    csv_to_xlsx(csvfile)
    BUTTON.config(text="INICIAR PESQUISA")
    BUTTON["state"] = TK.NORMAL
    TXT.set("Aguardando inicio de pesquisa ...")
    
    if os.name == 'nt':

        toaster = ToastNotifier()
        toaster.show_toast("Pesquisa encerrada.",
                   " ",
                   icon_path="logo.ico",
                   duration = 10)
        
    driver.close()
    driver.quit()
    # print(datetime.now() - time)
