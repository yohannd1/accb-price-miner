import sys, os
from time import strftime, asctime, time
from typing import Iterable, Optional
import traceback

import tkinter
from tkinter import filedialog, messagebox

LOG_FILE = sys.stderr
# LOG_FILE = open("error.log", "w+", encoding="latin-1")

def _curtime_str() -> str:
    return strftime("%Y-%m-%d %H:%M:%S")

def log(message: str) -> None:
    """Faz um log de uma mensagem."""
    prefix = _curtime_str()
    print(f"[{prefix}] {message}", file=LOG_FILE)

def log_multiline(messages: Iterable[str]) -> None:
    """Faz um log de uma mensagem."""
    prefix = _curtime_str()
    print(f"[{prefix}]:", file=LOG_FILE)
    for m in messages:
        print(f"  {m}", file=LOG_FILE)

def log_error(err):
    # FIXME: parar de usar isso - usar `log_multiline`
    with open("error.log", "w+", encoding="latin-1") as outfile:
        outfile.write(f"Date : {asctime()}\n")
        for error in err:
            outfile.write(str(error))

def is_windows() -> bool:
    return os.name == "nt"

def show_warning(title: str, message: str) -> None:
    root = tkinter.Tk()
    root.attributes("-topmost", True)
    root.withdraw()
    messagebox.showwarning(title, message, icon="warning", parent=root)
    root.destroy()

def ask_user_directory() -> Optional[str]:
    result = filedialog.askdirectory()
    return result if result != () else None

def get_time_hms(start_time_sec: float) -> dict:
    """Calcula o tempo passado desde `start_time_sec`, retornando-o em horas, minutos e segundos."""
    end = time()
    temp = end - start_time_sec

    hours = temp // 3600
    temp = temp % 3600

    minutes = temp // 60
    seconds = temp % 60

    return {"minutes": minutes, "seconds": seconds, "hours": hours}
