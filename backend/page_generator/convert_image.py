from pathlib import Path
from playwright.sync_api import sync_playwright
from utils.logger import get_logger

logger = get_logger(__name__)

def image_with_playwright(html_path: str, image_path: str):
    html_abs_path = Path(html_path).resolve()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f"file://{html_abs_path}")
        page.screenshot(path=image_path, full_page=True)
        browser.close()
