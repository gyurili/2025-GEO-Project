from typing import List
import time
import re
import os
from urllib.parse import quote
import selenium.webdriver as webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from utils.logger import get_logger

logger = get_logger(__name__)

def clean_product_url(url: str, pattern: str = r"https://.+?/vp/products/\d+") -> str:
    """
    상품 상세 URL을 정제해 표준 형태로 반환합니다.

    Args:
        url (str): 원본 상품 링크.
        pattern (str): 추출 정규표현식 (기본: 제품 상세 링크 형식).

    Returns:
        str: 정제된 상품 상세페이지 URL.
    """
    match = re.search(pattern, url)
    result = match.group(0) if match else url
    logger.debug(f"🛠️ 정제된 링크: {result}")
    return result

def init_safe_driver():
    """
    Selenium 크롬 드라이버를 초기화하여 반환합니다.

    Returns:
        webdriver.Chrome: 초기화된 드라이버 객체.
    """
    logger.debug("🛠️ 드라이버 초기화 시작")
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    logger.info("✅ 드라이버 실행 성공")
    return driver

def click_review_filter(driver, label: str) -> bool:
    """
    리뷰 필터 드롭다운에서 지정된 라벨의 항목을 클릭합니다.

    Args:
        driver: Selenium 드라이버 객체.
        label (str): 클릭할 필터 라벨명(예: "나쁨", "별로").

    Returns:
        bool: 클릭 성공 여부.
    """
    logger.debug(f"🛠️ 리뷰 필터 클릭 시도: {label}")
    try:
        dropdown_trigger = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div.review-star-search-current-selection"))
        )
        dropdown_trigger.click()
        time.sleep(1)

        WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "review-star-search-selector"))
        )

        filter_box = driver.find_element(By.CLASS_NAME, "review-star-search-selector")
        items = filter_box.find_elements(By.CSS_SELECTOR, "li")

        for item in items:
            try:
                wrapper = item.find_element(By.CLASS_NAME, "review-star-search-item")
                desc_el = wrapper.find_element(By.CLASS_NAME, "review-star-search-item-desc")
                if desc_el.text.strip() == label:
                    item.click()
                    time.sleep(2)
                    return True
            except Exception:
                continue

    except Exception as e:
        logger.error(f"❌ 필터 클릭 예외 발생: {type(e).__name__}: {e!r}")

    return False

def crawl_bad_reviews(driver, max_reviews: int) -> List[str]:
    """
    현재 상품 상세페이지에서 부정 리뷰(나쁨/별로)를 최대 max_reviews개까지 크롤링합니다.

    Args:
        driver: Selenium 드라이버 객체.
        max_reviews (int): 최대 수집 리뷰 개수.

    Returns:
        List[str]: 리뷰 본문 텍스트 리스트.
    """
    logger.debug("🛠️ 부정 리뷰 크롤링 시작")
    reviews = []
    while len(reviews) < max_reviews:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        review_list = soup.select("div.js_reviewArticleListContainer article")
        for article in review_list:
            content_tag = article.select_one("div.sdp-review__article__list__review__content span")
            if content_tag:
                text = content_tag.get_text(strip=True)
                text = re.sub(r"[^\w\s가-힣.,!?]", "", text)
                if text:
                    reviews.append(text)
            if len(reviews) >= max_reviews:
                break
        try:
            next_btn = driver.find_element(By.CSS_SELECTOR, "button.sdp-review__article__page__button--next")
            if "disabled" in next_btn.get_attribute("class"):
                break
            next_btn.click()
            time.sleep(1.5)
        except Exception:
            break
    return reviews

def crawl_reviews_by_link(driver, url: str, max_reviews: int = 30) -> List[str]:
    """
    주어진 상품 상세페이지 URL에서 부정 리뷰를 수집합니다.

    Args:
        driver: Selenium 드라이버 객체.
        url (str): 상품 상세페이지 URL.
        max_reviews (int): 최대 수집 리뷰 수.

    Returns:
        List[str]: 수집된 리뷰 리스트.
    """
    url = clean_product_url(url)
    logger.debug(f"🛠️ 리뷰 수집 시작: {url}")
    try:
        driver.get(url)
        time.sleep(2)
        reviews = []
        if click_review_filter(driver, "나쁨"):
            reviews = crawl_bad_reviews(driver, max_reviews)
        if len(reviews) < max_reviews and click_review_filter(driver, "별로"):
            additional = crawl_bad_reviews(driver, max_reviews - len(reviews))
            reviews.extend(additional)
        return reviews
    except Exception as e:
        logger.error(f"❌ 리뷰 수집 실패: {type(e).__name__}: {e!r}")
        return []

def crawl_reviews_by_category(
    category: str, max_products: int = 3, max_reviews_per_product: int = 10
) -> List[str]:
    """
    특정 카테고리 검색 결과에서 다수 상품에 대해 부정 리뷰를 수집합니다.

    Args:
        category (str): 검색 키워드.
        max_products (int): 최대 상품 개수.
        max_reviews_per_product (int): 상품별 최대 리뷰 수.

    Returns:
        List[str]: 전체 수집된 리뷰 리스트.
    """
    logger.debug(f"🛠️ 카테고리 '{category}'로 리뷰 크롤링 시작")
    all_reviews = []
    driver = init_safe_driver()
    try:
        base_search_url = os.environ.get("BASE_SEARCH_URL", "https://example.com/np/search")
        base_url = f"{base_search_url}?q={quote(category)}&sorter=scoreDesc"
        driver.get(base_url)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, 'ul#product-list li[class^="ProductUnit_productUnit__"]')
            )
        )
        soup = BeautifulSoup(driver.page_source, "html.parser")
        product_links = []
        for li in soup.select('ul#product-list li[class^="ProductUnit_productUnit__"]'):
            a_tag = li.select_one('a[href^="/vp/products/"]')
            if a_tag:
                raw_url = base_search_url.split("/np/")[0] + a_tag["href"]
                clean_url = clean_product_url(raw_url)
                product_links.append(clean_url)
            if len(product_links) >= max_products:
                break
        for link in product_links:
            reviews = crawl_reviews_by_link(driver, link, max_reviews=max_reviews_per_product)
            all_reviews.extend(reviews)
            time.sleep(1)
        return all_reviews
    except Exception as e:
        logger.error(f"❌ 카테고리 리뷰 수집 실패: {type(e).__name__}: {e!r}")
        return []
    finally:
        driver.quit()
        logger.debug("🛠️ 드라이버 종료")