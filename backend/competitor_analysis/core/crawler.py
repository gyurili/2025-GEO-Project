from typing import List
import time, re
from urllib.parse import quote
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from utils.logger import get_logger
from fake_useragent import UserAgent

logger = get_logger(__name__)


# =========================
# 셀레니움 안전 실행 드라이버 초기화
# =========================
def init_safe_driver():
    ua = UserAgent()
    user_agent = ua.chrome

    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"user-agent={user_agent}")
    options.binary_location = "/usr/bin/google-chrome"
    driver = uc.Chrome(options=options)
    return driver


# =========================
# 쿠팡 상품 리뷰 수집 (별점 2점 이하만 필터링)
# =========================
def crawl_reviews_by_link(driver, url: str, max_reviews: int = 30) -> List[str]:
    logger.debug(f"🔀️ 쿠팡 상품 리뷰 페이지 요청: {url}")
    reviews = []

    try:
        # 리뷰 탭 URL은 상품 링크 뒤에 /reviews 추가
        review_url = url + "/reviews"
        driver.get(review_url)
        time.sleep(3)

        # 페이지 탐색 및 리뷰 수집
        while len(reviews) < max_reviews:
            soup = BeautifulSoup(driver.page_source, "html.parser")
            review_elements = soup.select("div.sdp-review__article__list__review__content")

            for el in review_elements:
                # 별점 추출 (별점은 width 퍼센트로 표현됨)
                rating_tag = el.find_previous("div", class_="sdp-review__article__list__info__product-info__star-orange")
                rating = None
                if rating_tag:
                    match = re.search(r"width:\s*(\d+)%", str(rating_tag))
                    if match:
                        percentage = int(match.group(1))
                        rating = round(percentage / 20, 1)

                # 2점 이하만 수집
                if rating is not None and rating > 2:
                    continue

                text = el.get_text(strip=True)
                text = re.sub(r"[^\w\s가-힣.,!?]", "", text)
                if text:
                    reviews.append(text)

                if len(reviews) >= max_reviews:
                    break

            # 다음 페이지 버튼 클릭 (없으면 종료)
            try:
                next_btn = driver.find_element(By.CSS_SELECTOR, "button.sdp-review__article__page__button--next")
                if "disabled" in next_btn.get_attribute("class"):
                    break
                next_btn.click()
                time.sleep(2)
            except:
                break

        logger.info(f"✅ 별점 2점 이하 리뷰 {len(reviews)}개 수집 완료")
        return reviews

    except Exception as e:
        logger.error(f"❌ 리뷰 크롤링 예외 발생: {e}")
        return []


# =========================
# 쿠팡 카테고리 검색 → 상품 목록에서 리뷰 수집
# =========================
def crawl_reviews_by_category(category: str, max_products: int = 3, max_reviews_per_product: int = 10) -> List[str]:
    logger.debug(f"🔀️ 쿠팡 검색 시작: {category}")
    all_reviews = []
    driver = init_safe_driver()

    try:
        # 쿠팡 검색 URL 구성 (리뷰순 정렬)
        base_url = f"https://www.coupang.com/np/search?q={quote(category)}&sorter=scoreDesc"
        driver.get(base_url)

        # 렌더링 유도: 스크롤 두 번
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        # 상품 리스트 요소 로딩 대기
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, 'ul#product-list li[class^="ProductUnit_productUnit__"]')
                )
            )
            time.sleep(2)
        except Exception as e:
            logger.error(f"⏰ 상품 리스트 로딩 실패 (Timeout): {e}")
            return []

        # 상품 링크 수집
        soup = BeautifulSoup(driver.page_source, "html.parser")
        product_links = []

        product_tags = soup.select('ul#product-list li[class^="ProductUnit_productUnit__"]')
        logger.debug(f"🔍 상품 엘리먼트 개수: {len(product_tags)}")

        for idx, li in enumerate(product_tags):
            a_tag = li.select_one('a[href^="/vp/products/"]')
            if not a_tag:
                continue

            href = a_tag.get("href")
            full_url = "https://www.coupang.com" + href
            product_links.append(full_url)
            logger.debug(f"✅ 상품 {idx + 1}: {full_url}")

            if len(product_links) >= max_products:
                break

        logger.info(f"✅ 리뷰 수집 대상 상품 수: {len(product_links)}")

        # 각 상품별 리뷰 수집
        for link in product_links:
            logger.info(f"✅ 리뷰 수집 중: {link}")
            reviews = crawl_reviews_by_link(driver, link, max_reviews=max_reviews_per_product)
            all_reviews.extend(reviews)
            time.sleep(2)

        logger.info(f"✅ 총 수집 리뷰 수: {len(all_reviews)}")
        return all_reviews

    except Exception as e:
        logger.error(f"❌ 쿠팡 크롤링 실패: {e}")
        return []

    finally:
        driver.quit()
        logger.debug("🛠️ 드라이버 종료")