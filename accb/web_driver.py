import sys
from functools import lru_cache
import traceback

from selenium.webdriver.chrome.options import Options
from selenium import webdriver

from accb.utils import log_error


@lru_cache(maxsize=1)
def is_chrome_installed() -> bool:
    """Verifica se o Chrome está instalado."""

    try:
        driver = open_chrome_driver()
        driver.close()
        driver.quit()
        return bool(driver)
    except Exception as exc:
        log_error(exc)
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
