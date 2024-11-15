from functools import lru_cache

from selenium.webdriver.chrome.options import Options
from selenium import webdriver

from accb.utils import log_error


@lru_cache(maxsize=1)
def is_chrome_installed() -> bool:
    """Verifica se o Chrome está instalado."""

    try:
        driver = open_chrome_driver(is_headless=True)
        driver.close()
        driver.quit()
        return bool(driver)
    except Exception as exc:
        log_error(exc)
        return False


def open_chrome_driver(is_headless: bool = True) -> webdriver.Chrome:
    """Abre uma sessão do WebDriver do Chrome."""

    args = [
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--disable-features=NetworkService",
        "--window-size=1920x1080",
        "--disable-features=VizDisplayCompositor",
        "--user-agent=Mozilla/5.0 (Windows NT 4.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36",
    ]

    if is_headless:
        args.append("--headless")

    opts = Options()
    for a in args:
        opts.add_argument(a)

    return webdriver.Chrome(options=opts)
