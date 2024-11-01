import sys
import os
from time import strftime, asctime, time
from typing import Iterable, Optional
from datetime import datetime
from tkinter import filedialog, messagebox, Tk
from subprocess import Popen
from pathlib import Path
import traceback

_log_file = sys.stderr


def _curtime_str() -> str:
    return strftime("%Y-%m-%d %H:%M:%S")


def set_log_file(f) -> None:
    _log_file = f


def log(message: str) -> None:
    """Faz um log de uma mensagem."""
    prefix = _curtime_str()
    print(f"[{prefix}] {message}", file=_log_file)


def log_multiline(messages: Iterable[str]) -> None:
    """Faz um log de uma mensagem."""
    prefix = _curtime_str()
    print(f"[{prefix}]:", file=_log_file)
    for m in messages:
        print(f"  {m}", file=_log_file)


def log_error(exc: Exception) -> None:
    ls = ["Ocorreu um erro:"] + [l[:-1] for l in traceback.format_exception(exc)]
    log_multiline(ls)


def is_windows() -> bool:
    return sys.platform == "win32"


def is_linux() -> bool:
    return sys.platform.startswith("linux")


def is_macos() -> bool:
    return sys.platform == "darwin"


def show_warning(title: str, message: str) -> None:
    root = Tk()
    root.attributes("-topmost", True)
    root.withdraw()
    messagebox.showwarning(title, message, icon="warning", parent=root)
    root.destroy()


def ask_user_directory() -> Optional[Path]:
    root = Tk()
    root.attributes("-topmost", True)
    root.withdraw()
    result = filedialog.askdirectory()
    root.destroy()

    if result == () or (is_windows() and result == "."):
        return None
    else:
        return Path(result)


def get_time_hms(start_time_sec: float) -> dict:
    """Calcula o tempo passado desde `start_time_sec`, retornando-o em horas, minutos e segundos."""
    end = time()
    temp = end - start_time_sec

    hours = temp // 3600
    temp = temp % 3600

    minutes = temp // 60
    seconds = temp % 60

    return {"minutes": minutes, "seconds": seconds, "hours": hours}


def get_time_filename() -> str:
    return datetime.now().strftime("[%d-%m] [%Hh %Mm]")


def open_folder(path: Path) -> None:
    if is_windows():
        # https://docs.python.org/3.6/library/os.html#os.startfile
        os.startfile(str(path))  # type: ignore
    elif is_linux():
        # https://commandmasters.com/commands/xdg-open-linux/
        Popen(["xdg-open", str(path)])
    elif is_macos():
        # https://scriptingosx.com/2017/02/the-macos-open-command/
        Popen(["open", str(path)])
    else:
        raise NotImplementedError("unsupported operating system")
