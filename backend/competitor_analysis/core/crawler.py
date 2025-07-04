from typing import List
import time, re
from urllib.parse import quote
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from utils.logger import get_logger

logger = get_logger(__name__)

# ✅ 쿠팡 상품 링크 정제 함수
def clean_coupang_url(url: str) -> str:
    match = re.search(r"(https://www\.coupang\.com/vp/products/\d+)", url)
    return match.group(1) if match else url

# ✅ 드라이버 초기화
def init_safe_driver():
    ua = UserAgent()
    user_agent = ua.chrome

    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    # options.add_argument("--headless=new")  # 필요 시 해제
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"user-agent={user_agent}")
    options.binary_location = "/usr/bin/google-chrome"
    return uc.Chrome(options=options)

# ✅ 필터 클릭
def click_review_filter(driver, label: str):
    try:
        filter_box = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "review-star-search-selector"))
        )
        items = filter_box.find_elements(By.CSS_SELECTOR, "li")
        for item in items:
            try:
                wrapper = item.find_element(By.CLASS_NAME, "review-star-search-item")
                desc_el = wrapper.find_element(By.CLASS_NAME, "review-star-search-item-desc")
                if desc_el.text.strip() == label:
                    item.click()
                    logger.debug(f"⭐ 필터 클릭 성공: {label}")
                    time.sleep(2)
                    return True
            except Exception as e:
                logger.warning(f"⚠️ 필터 항목 탐색 실패 (건너뜀): {e}")
                continue
        logger.warning(f"🚫 필터 '{label}' 클릭 실패 - 요소 없음")
    except Exception as e:
        logger.error(f"❌ 필터 클릭 예외 발생: {e}")
    return False

# ✅ 부정 리뷰 크롤링
def crawl_bad_reviews(driver, max_reviews: int) -> List[str]:
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
        except:
            break
    return reviews

# ✅ 단일 상품 상세 페이지에서 리뷰 수집
def crawl_reviews_by_link(driver, url: str, max_reviews: int = 30) -> List[str]:
    url = clean_coupang_url(url)
    logger.debug(f"🔀️ 리뷰 수집 시작: {url}")
    try:
        driver.get(url)
        time.sleep(2)

        reviews = []
        if click_review_filter(driver, "나쁨"):
            reviews = crawl_bad_reviews(driver, max_reviews)

        if len(reviews) < max_reviews and click_review_filter(driver, "별로"):
            additional = crawl_bad_reviews(driver, max_reviews - len(reviews))
            reviews.extend(additional)

        logger.info(f"✅ 수집된 부정 리뷰 수: {len(reviews)}")
        return reviews
    except Exception as e:
        logger.error(f"❌ 리뷰 수집 실패: {e}")
        return []

# ✅ 카테고리 검색 결과에서 N개 상품에 대해 리뷰 수집
def crawl_reviews_by_category(category: str, max_products: int = 3, max_reviews_per_product: int = 10) -> List[str]:
    logger.debug(f"🔍 쿠팡 검색 시작: {category}")
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
                logger.debug(f"✅ 상품 링크: {clean_url}")
            if len(product_links) >= max_products:
                break

        logger.info(f"✅ 총 상품 수: {len(product_links)}")

        for link in product_links:
            logger.info(f"📦 리뷰 수집 중: {link}")
            reviews = crawl_reviews_by_link(driver, link, max_reviews=max_reviews_per_product)
            all_reviews.extend(reviews)
            time.sleep(1)

        logger.info(f"🎯 총 수집된 리뷰 수: {len(all_reviews)}")
        return all_reviews

    except Exception as e:
        logger.error(f"❌ 카테고리 리뷰 수집 실패: {e}")
        return []

    finally:
        driver.quit()
        logger.debug("🛠️ 드라이버 종료")