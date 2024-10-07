import sys
from time import strftime, asctime
from typing import Iterable
from functools import lru_cache
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

@lru_cache(maxsize=1)
def is_chrome_installed() -> bool:
    """Verifica se o Chrome está instalado."""

    # from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium import webdriver

    try:
        opts = Options()
        opts.add_argument("--headless")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--disable-features=NetworkService")
        opts.add_argument("--window-size=1920x1080")
        opts.add_argument("--disable-features=VizDisplayCompositor")

        # driver_cache_manager = DriverCacheManager(root_dir="testing")
        # service = Service(ChromeDriverManager(cache_manager=driver_cache_manager).install(), log_path='Nul')
        driver = webdriver.Chrome(options=opts)

        driver.close()
        driver.quit()

        return bool(driver)

    except Exception:
        exc_type, exc_value, exc_tb = sys.exc_info()
        log_error(traceback.format_exception(exc_type, exc_value, exc_tb))

        return False

