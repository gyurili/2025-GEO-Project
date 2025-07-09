from typing import List
import time
import re
from urllib.parse import quote
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from utils.logger import get_logger

logger = get_logger(__name__)

def clean_coupang_url(url: str) -> str:
    """
    쿠팡 상품 상세 URL을 정제해 표준 형태로 반환한다.

    Args:
        url (str): 원본 쿠팡 상품 링크.

    Returns:
        str: 정제된 상품 상세페이지 URL.
    """
    logger.debug(f"🛠️ 쿠팡 상품 링크 정제: {url}")
    match = re.search(r"(https://www\.coupang\.com/vp/products/\d+)", url)
    result = match.group(1) if match else url
    logger.debug(f"🛠️ 정제된 링크: {result}")
    return result

def init_safe_driver():
    """
    셀레니움 undetected_chromedriver를 크롬 옵션과 함께 초기화하여 드라이버 객체를 반환한다.

    Returns:
        uc.Chrome: 초기화된 Selenium 크롬 드라이버 객체.
    """
    logger.debug("🛠️ 드라이버 초기화 시작")
    ua = UserAgent()
    user_agent = ua.chrome

    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"user-agent={user_agent}")
    options.binary_location = "C:/Program Files/Google/Chrome/Application/chrome.exe"
    driver = uc.Chrome(options=options)
    logger.info("✅ 드라이버 실행 성공")
    return driver

def click_review_filter(driver, label: str) -> bool:
    """
    리뷰 필터 드롭다운에서 지정된 라벨의 항목을 클릭한다.

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
        found = False

        for item in items:
            try:
                wrapper = item.find_element(By.CLASS_NAME, "review-star-search-item")
                desc_el = wrapper.find_element(By.CLASS_NAME, "review-star-search-item-desc")
                if desc_el.text.strip() == label:
                    item.click()
                    logger.debug(f"🛠️ 필터 클릭 성공: {label}")
                    time.sleep(2)
                    found = True
                    return True
            except Exception as e:
                logger.warning(f"⚠️ 필터 항목 탐색 실패(계속 진행): {type(e).__name__}: {e!r}")
                continue

        if not found:
            logger.warning(f"⚠️ 필터 '{label}' 클릭 실패 - 해당 요소 없음")

    except Exception as e:
        logger.error(f"❌ 필터 클릭 예외 발생: {type(e).__name__}: {e!r}")

    return False

def crawl_bad_reviews(driver, max_reviews: int) -> List[str]:
    """
    현재 상품 상세페이지에서 부정 리뷰(나쁨/별로)를 최대 max_reviews개까지 크롤링한다.

    Args:
        driver: Selenium 드라이버 객체.
        max_reviews (int): 최대 수집 리뷰 개수.

    Returns:
        List[str]: 리뷰 본문 텍스트 리스트.
    """
    logger.debug("🛠️ 부정 리뷰 크롤링 시작")
    reviews = []
    page = 1
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
            page += 1
            time.sleep(1.5)
        except Exception as e:
            logger.debug("🛠️ 더 이상 다음 페이지 없음")
            break
    if len(reviews) == 0:
        logger.warning("⚠️ 부정 리뷰를 하나도 찾지 못함")
    else:
        logger.info(f"✅ 부정 리뷰 {len(reviews)}개 크롤링 완료")
    return reviews

def crawl_reviews_by_link(driver, url: str, max_reviews: int = 30) -> List[str]:
    """
    상품 상세페이지 URL에서 부정 리뷰만 최대 max_reviews개까지 크롤링한다.

    Args:
        driver: Selenium 드라이버 객체.
        url (str): 상품 상세페이지 URL.
        max_reviews (int): 최대 수집 리뷰 개수.

    Returns:
        List[str]: 리뷰 본문 텍스트 리스트.
    """
    url = clean_coupang_url(url)
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
        if len(reviews) == 0:
            logger.warning(f"⚠️ 해당 상품에서 수집된 부정 리뷰가 없습니다: {url}")
        else:
            logger.info(f"✅ 수집된 부정 리뷰 수: {len(reviews)}")
        return reviews
    except Exception as e:
        logger.error(f"❌ 리뷰 수집 실패: {type(e).__name__}: {e!r}")
        return []

def crawl_reviews_by_category(
    category: str, max_products: int = 3, max_reviews_per_product: int = 10
) -> List[str]:
    """
    쿠팡에서 특정 카테고리 검색 결과 상위 N개 상품에 대해
    부정 리뷰를 각각 최대 M개까지 수집 후, 전체 리스트로 반환한다.

    Args:
        category (str): 검색 키워드(카테고리).
        max_products (int): 최대 크롤링할 상품 개수.
        max_reviews_per_product (int): 상품별 최대 리뷰 수.

    Returns:
        List[str]: 모든 상품에서 크롤링된 부정 리뷰 리스트.
    """
    logger.debug(f"🛠️ 카테고리 '{category}'로 리뷰 크롤링 시작")
    all_reviews = []
    driver = init_safe_driver()
    try:
        base_url = f"https://www.coupang.com/np/search?q={quote(category)}&sorter=scoreDesc"
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
                raw_url = "https://www.coupang.com" + a_tag["href"]
                clean_url = clean_coupang_url(raw_url)
                product_links.append(clean_url)
                logger.debug(f"🛠️ 상품 링크 수집: {clean_url}")
            if len(product_links) >= max_products:
                break
        if len(product_links) == 0:
            logger.warning("⚠️ 검색 결과에서 상품을 찾지 못했습니다.")
        else:
            logger.info(f"✅ 총 상품 수집 개수: {len(product_links)}")
        for link in product_links:
            logger.debug(f"🛠️ 상품별 리뷰 수집 시작: {link}")
            reviews = crawl_reviews_by_link(driver, link, max_reviews=max_reviews_per_product)
            all_reviews.extend(reviews)
            time.sleep(1)
        if len(all_reviews) == 0:
            logger.warning("⚠️ 총 수집된 리뷰가 없습니다.")
        else:
            logger.info(f"✅ 총 수집된 리뷰 수: {len(all_reviews)}")
        return all_reviews
    except Exception as e:
        logger.error(f"❌ 카테고리 리뷰 수집 실패: {type(e).__name__}: {e!r}")
        return []
    finally:
        driver.quit()
        logger.debug("🛠️ 드라이버 종료")