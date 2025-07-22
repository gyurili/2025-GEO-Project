from pathlib import Path
from playwright.sync_api import sync_playwright
from utils.logger import get_logger

logger = get_logger(__name__)

def image_with_playwright(html_path: str, image_path: str):
    """
    Playwright를 사용해 HTML 파일을 렌더링하고, 전체 페이지 스크린샷을 저장합니다.

    Args:
        html_path (str): 렌더링할 로컬 HTML 파일의 경로
        image_path (str): 저장할 스크린샷 이미지 파일의 경로

    Returns:
        None
    """
    html_abs_path = Path(html_path).resolve()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f"file://{html_abs_path}")
        page.screenshot(path=image_path, full_page=True)
        browser.close()
