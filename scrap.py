import re
import time
import csv
import os
import threading
from tkinter import messagebox
from datetime import date
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
try:
    from win10toast import ToastNotifier
except ImportError:
    pass

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


def get_data(driver, local, writer, product, local_cep):

    found = True
    # info = []
    elements = []
    # Lista de Produtos
    elements = driver.find_elements_by_class_name("flex-item2")

    for element in elements:

        # * Processo de aquisição de dados

        # Nome do produto
        product_name = element.find_elements_by_tag_name("strong")[0]
        product_name = product_name.get_attribute('innerHTML')

        # Todas as tags com as informações do bloco do produto
        product_info = element.find_elements_by_tag_name("div")

        # Preço do produto
        flag = 0
        if len(element.find_elements_by_class_name("sobre-desconto")) == 0:
            product_price = product_info[1].get_attribute('innerHTML')
        else:
            product_price = product_info[2].get_attribute('innerHTML')
            flag = 1

        pattern = re.compile("(?<=>)\s\w..\d?(\d),\d\d")
        product_size = len(product_price)
        product_price = product_price.replace('\n', '')

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

        if local in str(product_adress):

            print('Preço : ' + str(product_price))
            print('Local : ' + str(product_adress))
            print('Produto : ' + str(product_name))
            # info.append(
            #     {'p': product_price, 'l': product_adress, 'n': product_name})
            found = False
            writer.writerow([str(product_name), str(
                product_adress), str(product), str(product_price)])

    if found:

        writer.writerow([str(product), str(local),
                         str(product), "N/A"])

    # return info


def pop_up():
    
    result = messagebox.askquestion("CAPTCHA", "Captcha foi ativado, resolva-o em seu navegador e aperte Sim para continuar", icon='warning')
    if result == 'yes':
        return True
    else:
        return False
        

def captcha():
    
    while True:

        if pop_up():
            
            break        


    
def scrap(CEP, LOCALS, BUTTON, TK, PROGRESS_VAR, TXT):

    result = '1'
    URL = 'https://precodahora.ba.gov.br/'
    times = 3
    today = date.today()
    day = today.strftime("%d-%m-%Y")

    chrome_options = Options()
    # chrome_options.add_argument('--headless')
    # chrome_options.add_argument('--no-sandbox')
    # chrome_options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(
        executable_path="chromedriver.exe", options=chrome_options)
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

    for n, number in enumerate(CEP):

        # Define endereço a ser visitado
        if n == 0:

            driver.get(URL)
            # * Processo de pesquisa de produto
            driver.find_element_by_id('fake-sbar').click()
            time.sleep(5*times)

        dic = 'Pesquisa [ ' + day + ' ]'
        if not os.path.exists(dic):

            os.makedirs(dic)

        with open(dic + '/' + LOCALS[n] + '.csv', 'w+', newline='') as file:

            writer = csv.writer(file, delimiter=';')
            writer.writerow(
                ["Produto", "Estabelecimento", "Keyword", "Preço"])
        
        TXT.set("Pesquisa iniciada - " + LOCALS[n])

        for index, product in enumerate(products):

            time.sleep(10*times)
    
            # Barra de pesquisa superior (produtos)
            try:

                WebDriverWait(driver, 2*times).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "sbar-input")))

            except:

                # print("Captcha foi ativado.")
                # while True:

                #     go = input('Digite S quando resolver o captcha')
                #     if go == 'S':

                captcha()
                driver.get('https://precodahora.ba.gov.br/produtos')
                time.sleep(2*times)

            finally:

                search = driver.find_element_by_id('top-sbar')

            # Insere o produto da iteração i
            for word in product:

                search.send_keys(word)
                time.sleep(0.25)

            # Realiza a pesquisa (pressiona enter)
            search.send_keys(Keys.ENTER)

            time.sleep(3*times)
            driver.page_source.encode('utf-8')

            # * Processo para definir a região desejada para ser realizada a pesquisa

            if index == 0:

                # Botão que abre o modal referente a localização
                try:

                    WebDriverWait(driver, 5*times).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "location-box")))

                except:

                    # while True:

                        # go = input(
                        #     'Captcha Ativado, resolva o Captcha e aperte S')
                        # if go == 'S':
                    captcha()
                    driver.back()
                    time.sleep(1)
                        
                finally:

                    driver.find_element_by_class_name('location-box').click()
                    time.sleep(5*times)

                # Botão que abre a opção de inserir o CEP
                try:

                    WebDriverWait(driver, 5*times).until(
                        EC.presence_of_element_located((By.ID, "add-address")))

                except:

                    # while True:

                    #     go = input(
                    #         'Captcha Ativado, resolva o Captcha e aperte S')
                    #     if go == 'S':
                    captcha()
                    driver.back()
                    time.sleep(1)
                            # break

                finally:

                    driver.find_element_by_id('add-address').click()
                    time.sleep(5*times)

                # Envia o CEP desejado para o input

                driver.find_element_by_id('my-zip').send_keys(number)

                # Preciona o botão que realiza a pesquisa por CEP
                driver.find_element_by_id('sel-cep').click()

                time.sleep(5*times)

            # Espera a página atualizar, ou seja, terminar a pesquisa. O proceso é reconhecido como terminado quando a classe flex-item2 está presente, que é a classe utilizada para estilizar os elementos listados
            try:

                WebDriverWait(driver, 5*times).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "flex-item2")))

            except:

                # print("CAPTCHA foi ativado ou erro de conexão.\n")
                # go = 'Y'
                # while go != 'S':

                #     go = input(
                #         "Digite 'S' para continuar após resolver o CAPTCHA.\n")
                captcha()
                driver.back()
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

                        if flag == 2:

                            print("2 paginas abertas.")
                            break

                    except:

                        print("Não teve mais resultados.")
                        break

                with open(dic + '/' + LOCALS[n] + '.csv', 'a+', newline='') as file:

                    writer = csv.writer(file, delimiter=';')
                    get_data(driver, LOCALS[n], writer, product, number)

            PROGRESS_VAR['value'] += 8.3333333
        
        PROGRESS_VAR['value'] = 0
        if os.name == 'nt':

            toaster = ToastNotifier()
            toaster.show_toast("Pesquisa encerrada para o estabelecimento " + LOCALS[n] + ", arquivo gerado com sucesso.")         
    
    BUTTON["state"] = TK.NORMAL
    BUTTON.config(text="INICIAR PESQUISA")
    if os.name == 'nt':

        toaster = ToastNotifier()
        toaster.show_toast("Pesquisa encerrada.")
        
    driver.close()
    driver.quit()
    # print(datetime.now() - time)


# scrap()
