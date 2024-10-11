import sys, os
from time import strftime, asctime
from typing import Iterable
import traceback

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
