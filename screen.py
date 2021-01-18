import os
import tkinter as tk
from tkinter import messagebox
from tkinter.ttk import * 
from tkinter import ttk
import scrap as scrapper
from datetime import datetime
import threading

def start_search(city, button, progress_bar, text):

    text.set("Iniciando pesquisa ...")
    button["state"] = tk.DISABLED
    button.config(text="PESQUISA EM ANDAMENTO")
    
    if city.get() == 1:

        # ITABUNA
        CEP = ['45607100',
               '45600050']
        
        LOCALS = ['BARATEIRO',
                  'RONDELLI']
        
        threading.Thread(target=lambda:scrapper.scrap(CEP, LOCALS, button, tk, progress_bar, text, "Itabuna")).start()

    elif city.get() == 2:

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

        LOCALS = ['ITAO',
                'MEIRA',
                'SUPERMERCADO MANGOSTÃO',
                'GBARBOSA',
                'JACIANA SUPERMERCADO',
                'ALANA SUPERMERCADO',
                'MECARDINHO E FRUTARIA CLAUDINTE',
                'NENEM SUPERMERCADOS',
                'CESTÃO DA ECONOMIA',
                'ATACADAO']

        threading.Thread(target=lambda:scrapper.scrap(CEP, LOCALS, button, tk, progress_bar, text, "Ilheus")).start()

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
  
    start_button = tk.Button(window, text="INICIAR PESQUISA",relief=tk.FLAT, font='Times 10' , fg='black', bg='#ddd', command=lambda: start_search(var, start_button, progress_bar, text))
    start_button.pack()
        
    window.mainloop()
    top.mainloop()

main()
