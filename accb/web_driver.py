from functools import lru_cache

from selenium.webdriver.chrome.options import Options
from selenium import webdriver

def is_windows() -> bool:
    return os.name == "nt"

@lru_cache(maxsize=1)
def is_chrome_installed() -> bool:
    """Verifica se o Chrome está instalado."""

    try:
        driver = open_chrome_driver()
        driver.close()
        driver.quit()
        return bool(driver)

    except Exception:
        exc_type, exc_value, exc_tb = sys.exc_info()
        log_error(traceback.format_exception(exc_type, exc_value, exc_tb))

        return False

def open_chrome_driver() -> webdriver.Chrome:
    """Abre uma sessão do WebDriver do Chrome."""

    args = (
        "--headless",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--disable-features=NetworkService",
        "--window-size=1920x1080",
        "--disable-features=VizDisplayCompositor",
    )

    opts = Options()
    for a in args:
        opts.add_argument(a)

    return webdriver.Chrome(options=opts)
