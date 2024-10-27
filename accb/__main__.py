from threading import Thread
from tkinter.messagebox import showwarning

if __name__ == "__main__":
    # mostrar essa mensagem antes de importar o resto do código para que ela apareça o mais rápido possível
    t = Thread(target=lambda: showwarning("ACCB", "Carregando. Por favor aguarde..."))
    t.start()

    from accb.server import main

    main()
