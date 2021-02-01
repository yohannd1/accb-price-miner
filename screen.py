import os
import json
import tkinter as tk
from tkinter import *
from tkinter import messagebox
from tkinter.ttk import * 
from tkinter import ttk
import scrap as scrapper
from datetime import datetime
import threading
try:
    from win10toast import ToastNotifier
except ImportError:
    pass

class Lstbox:
    
    def __init__(self, root, local, start_button):
        self.root = root
        self.start_button = start_button
        self.listbox = Listbox(self.root, selectmode=MULTIPLE, 
                                activestyle = 'dotbox',  
                                font = "Times 11", 
                                relief=tk.FLAT,
                                borderwidth=0, 
                                highlightthickness=0,
                                bg="#f0f0f0")
        
        self.listbox.pack(expand=1, fill="both")
        self.listbox.bind("<<ListboxSelect>>", self.callback)
        for index, place in enumerate(local):
           
            self.listbox.insert(END, place)
        
        self.selection = self.listbox.curselection()
        
        self.start_button["state"] = tk.DISABLED        
        threading.Thread(target=lambda:self.root.mainloop())
        
    def callback(self, a):
        
        if len(self.listbox.curselection()) == 2:
            
            self.start_button["state"] = tk.NORMAL
            
        elif len(self.listbox.curselection()) < 2:
            
            self.start_button["state"] = tk.DISABLED
            
        if len(self.listbox.curselection()) > 2:
            for i in self.listbox.curselection():
                if i not in self.selection:
                    self.listbox.selection_clear(i)
        self.selection = self.listbox.curselection()
    
    def get_selected(self):
        
        return self.selection
    
    def destroy(self):
        
        self.root.destroy()

def pop_up():
    
    result = messagebox.askquestion("Backup","Uma pesquisa foi interrompida, deseja retornar ?", icon='warning')
    if result == 'yes':
        return True
    else:
        return False

def start(LOCALS, button, tk, progress_bar, text, city, selected, LOCALS_NAME):
    
    local = []
    local_name = []
    index_1 , index_2 = selected.get_selected()
    local.append(LOCALS[index_1])
    local.append(LOCALS[index_2])
    local_name.append(LOCALS_NAME[index_1])
    local_name.append(LOCALS_NAME[index_2])
    text.set("Iniciando pesquisa ...")
    button["state"] = tk.DISABLED
    button.config(text="PESQUISA EM ANDAMENTO")
    selected.destroy()
    threading.Thread(target=lambda:scrapper.scrap(local, button, tk, progress_bar, text, city, local_name)).start()

def start_search(city, button, progress_bar, text, backup, city_backup, estab, place):

    selected = 0
    product_1 = 0
    product_2 = 0
    
    LOCALS_NAME_ITN = ['Supermercado Itao',
                'Supermercado Carisma',
                'Supermercado HiperBompreco',		
                'Supermercado Meira',	
                'Mercado Mattos',		
                'Supermercado Barateiro',		
                'Híper Itao',		
                'Atacadao Rondelli',		
                'Mercado Dois Imaos',		
                'Maxx Atacado',		
                'Padaria Le & Gi',		
                'Supermercado Compre Bem',
    ]
        
    LOCALS_ITN = ['ITAO',		
                'CARISMA',		
                'BOMRPRECO',	
                'DALNORDE',		
                'MATTOS',		
                'SUPERMERCADO BARATEIRO',		
                'HIPER ITAO',		
                'RONDELLI',		
                'IRMAOS',		
                'MAXXI',	
                'NOVO BARATEIRO',	
                'COMPRE BEM']
    
    LOCALS_NAME_IOS = [ 'Itao Supermercado',		
                        'Supermercado Meira',		
                        'Supermercado Mangostao',		
                        'Gbarbosa', 		
                        'Jaciana Supermercado', 		
                        'Alana Supermercado',		
                        'Mercadinho e Frutaria Claudinete',		
                        'Nenem Supermercados',   		
                        'Cestao da Economia',		
                        'Atacadao',
    ]

    LOCALS_IOS = ['ITAO',
            'SUPERMERCADO DALNORDE',
            'SUPERMERCADO MANGOSTÃO',
            'GBARBOSA',
            'JACIANA SUPERMERCADO',
            'ALANA SUPERMERCADO',
            'MECARDINHO E FRUTARIA CLAUDINTE',
            'NENEM SUPERMERCADOS',
            'SEM NOME',
            'ATACADAO']
    
    if backup:
        
        print("Backup")
        text.set("Iniciando pesquisa ...")
        button.config(text="PESQUISA EM ANDAMENTO")
            
            
        if city_backup == 'Itabuna':
            
            threading.Thread(target=lambda:scrapper.scrap(place, button, tk, progress_bar, text, city_backup, estab)).start()
            
        elif city_backup == 'Ilhéus':

            threading.Thread(target=lambda:scrapper.scrap(place, button, tk, progress_bar, text, city_backup, estab)).start()
    
    else:
            
        print("Normal")
        top = tk.Toplevel()
        top.title('Seleção de Estabelecimentos')
        top.resizable(height=False, width=False)
        top.config(padx=15,pady=15)
        if os.name == 'nt':
            top.iconbitmap('logo.ico')

        width = 300
        heigth = 300

        x = (top.winfo_screenwidth() // 2) - (width // 2)
        y = (top.winfo_screenheight() // 2) - (heigth // 2)
        top.geometry('{}x{}+{}+{}'.format(width, heigth, x + width, y))
        
        if city.get() == 1:

            
            start_button = tk.Button(top, text="INICIAR PESQUISA",relief=tk.FLAT, font='Times 10' , fg='black', bg='#ddd', pady=7, padx=7, command= lambda: start(LOCALS_ITN, button, tk, progress_bar, text, 'Itabuna', selected, LOCALS_NAME_ITN))
        
            # ITABUNA
            
            selected = Lstbox(top, LOCALS_NAME_ITN, start_button)
            start_button.pack()
            # threading.Thread(target=lambda:scrapper.scrap(LOCALS, button, tk, progress_bar, text, "Itabuna")).start()

        elif city.get() == 2:

            start_button = tk.Button(top, text="INICIAR PESQUISA",relief=tk.FLAT, font='Times 10' , fg='black', bg='#ddd', command= lambda: start(LOCAL_IOS, button, tk, progress_bar, text, 'Ilhéus', selected, LOCALS_NAME_IOS))

            # ILHEUS
            CEP = ['45662000',
                    '45652570',
                    '45657000',
                    '45651310',
                    '45654000',
                    '45654380',
                    '45653400',
                    '45662000',
                    '45658350',
                    '45656000']
            
            

            selected = Lstbox(top, LOCALS_NAME_IOS, start_button)
            start_button.pack()
            # threading.Thread(target=lambda:scrapper.scrap(CEP, LOCALS, button, tk, progress_bar, text, "Ilheus")).start()
                
# Backup
def backup_check(city, button, progress_bar, text):

    today = datetime.today()
    day = today.strftime("%d-%m-%Y")
    
    try:
    
        finish = 0
        date = 0
        estab_1 = 0
        place_1 = 0
        place_2 = 0
        estab_2 = 0
        city_backup = 0
        
        with open('backup.json') as json_file:

            data = json.load(json_file)
            for backup in data['backup']:
                
                date = backup['date']    
                finish = backup['done']
                estab_1 = backup['estab_1']
                estab_2 = backup['estab_2']
                place_1 = backup['place_1']
                place_2 = backup['place_2']
                city_backup = backup['city']
                
    except:
        
        start_search(city, button, progress_bar, text, False, None, None, None)
        return
    
    # Pesquisa do estabelecimento nao acabou
    if finish == 0:
        
        if pop_up():
            
            start_search(city, button, progress_bar, text, True, city_backup, [estab_1, estab_2], [place_1, place_2])
            return

        else:
            
            start_search(city, button, progress_bar, text, False, None, None, None)
            return
        
    
    if day != date:
    
        start_search(city, button, progress_bar, text, False, None, None, None)
        return

def main():

    # Window
    
        
    window = tk.Tk()
    window.title('ACCB - Auto Search')
    window.resizable(height=False, width=False)
    if os.name == 'nt':
        window.iconbitmap('logo.ico')

    width = 280
    heigth = 120

    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (heigth // 2)
    window.geometry('{}x{}+{}+{}'.format(width, heigth, x, y))

    # Frame

    frame = tk.Frame(window)
    frame.pack(fill=tk.BOTH, pady=10)

    # RadioButton

    var = tk.IntVar()
    radio_1 = tk.Radiobutton(frame, text="Itabuna", variable=var,value=1)
    radio_1.pack()

    radio_2 = tk.Radiobutton(frame, text="Ilhéus", variable=var, value=2)
    radio_2.pack()
    
    top = tk.Toplevel()
    
    # Label
    text = tk.StringVar()
    text.set("Aguardando inicio de pesquisa ...")
    label = tk.Label(top, textvariable = text, font='Times 10' , fg='black')
    label.pack(pady=5)
    
    # Progress Bar
    progress_bar = ttk.Progressbar(top, orient=tk.HORIZONTAL, length=220, mode='determinate')
    progress_bar.pack(pady=5)
    
    # Top Level
    
    top.title('Search Progress')
    top.resizable(height=False, width=False)
    if os.name == 'nt':
        top.iconbitmap('logo.ico')
  
    width = 320
    heigth = 80

    x = (top.winfo_screenwidth() // 2) - (width // 2)
    y = (top.winfo_screenheight() // 2) - (heigth // 2)
    top.geometry('{}x{}+{}+{}'.format(width, heigth, x - width, y))
    
    # Button
  
    start_button = tk.Button(window, text="INICIAR PESQUISA",relief=tk.FLAT, font='Times 10' , fg='black', bg='#ddd', command=lambda: backup_check(var, start_button, progress_bar, text))
    start_button.pack()
    
  
    window.mainloop()
    top.mainloop()
    
main()
