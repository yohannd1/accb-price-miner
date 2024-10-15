import os
import subprocess
from tabulate import tabulate

try:
    from subprocess import DEVNULL
except ImportError:
    DEVNULL = os.open(os.devnull, os.O_RDWR)

def process_exists_win(name: str) -> bool:
    """Confere se um processo de nome `name` existe no sistema (windows)."""

    call = ("TASKLIST", "/FI", f"imagename eq {name}")
    # use buildin check_output right away
    output = subprocess.check_output(call, stdin=DEVNULL, stderr=DEVNULL).decode(
        "latin-1"
    )
    # check in last line for process name
    last_line = output.strip().split("\r\n")[-1]

    # because Fail message could be translated

    try:
        is_app_name = last_line.lower().startswith(name.lower())

        # número de processos com esse número. Um deles é o cleaner do pyinstaller; outro é o nosso programa; e o outro é a instancia do driver chamado para conferir se o driver está instalado ou quando o driver é executado.
        instances = int(last_line.strip().split()[3])

        return not (is_app_name and instances <= 3)

    except Exception:
        return False

def print_tab(df):
    """Printa um set de dados iteráveis de forma organizada e tabulada no console."""
    print(tabulate(df, headers="keys", tablefmt="psql"))
