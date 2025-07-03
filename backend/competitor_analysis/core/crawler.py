from typing import List
import time, re
from urllib.parse import quote
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from utils.logger import get_logger

logger = get_logger(__name__)


# =========================
# 드라이버 초기화
# =========================
def init_safe_driver():
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
    options.add_argument("--window-size=1920,1080")
    driver = uc.Chrome(options=options)

    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            window.chrome = { runtime: {} };
        """
    })

    return driver


# =========================
# 리뷰 수집 (2점 이하 필터링)
# =========================
def crawl_reviews_by_link(driver, url: str, max_reviews: int = 30) -> List[str]:
    logger.debug(f"🛠️ 상품 페이지 접속 시도: {url}")
    reviews = []

    try:
        driver.get(url)
        time.sleep(3)

        # 리뷰 탭 클릭
        try:
            review_tab = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "li.sdp-review__article-tab-item[data-tab-name='REVIEW']"))
            )
            review_tab.click()
            logger.info("✅ 리뷰 탭 클릭 완료")
            time.sleep(2)
        except Exception as e:
            logger.error(f"❌ 리뷰 탭 클릭 실패: {e}")
            return []

        # 별점 낮은 순 정렬
        try:
            sort_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.sdp-review__article__order__selected"))
            )
            sort_btn.click()
            time.sleep(1)

            low_rating_option = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "ul.sdp-review__article__order__list li[data-option-value='scoreAsc']"))
            )
            low_rating_option.click()
            logger.info("✅ 별점 낮은 순 정렬 완료")
            time.sleep(2)
        except Exception as e:
            logger.warning(f"⚠️ 별점 정렬 옵션 클릭 실패 (기본 정렬 유지): {e}")

        # 스크롤 & 더보기 반복
        for _ in range(10):
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
            time.sleep(1.5)
            try:
                more_btn = driver.find_element(By.CSS_SELECTOR, "button.sdp-review__article__order__option__more")
                more_btn.click()
                time.sleep(1.5)
            except:
                break

        # 리뷰 파싱 + 2점 이하만 필터링
        soup = BeautifulSoup(driver.page_source, "html.parser")
        review_elements = soup.select("article.sdp-review__article__list__review")
        logger.debug(f"🛠️ 전체 리뷰 엘리먼트 수: {len(review_elements)}")

        for el in review_elements:
            rating_tag = el.select_one("span.rating-star")
            rating = None
            if rating_tag:
                aria = rating_tag.get("aria-label", "")
                match = re.search(r"별점\s*(\d)", aria)
                if match:
                    rating = int(match.group(1))

            if rating is not None and rating > 2:
                continue  # 2점 이하만

            text = el.get_text(strip=True)
            text = re.sub(r"[^\w\s가-힣.,!?]", "", text)
            if text:
                reviews.append(text)

            if len(reviews) >= max_reviews:
                break

        logger.info(f"✅ 별점 2점 이하 리뷰 {len(reviews)}개 수집 완료")
        return reviews

    except Exception as e:
        logger.error(f"❌ 리뷰 크롤링 실패: {e}")
        return []


# =========================
# 카테고리 검색 → 별점 낮은 제품 리뷰 수집
# =========================
def crawl_reviews_by_category(category: str, exclude_name: str = "", max_products: int = 3, max_reviews_per_product: int = 10) -> List[str]:
    logger.debug(f"🛠️ 카테고리 기반 검색 시작: {category}")
    driver = init_safe_driver()
    all_reviews = []

    try:
        base_url = f"https://www.coupang.com/np/search?q={quote(category)}&page=1"
        driver.get(base_url)
        time.sleep(4)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        items = soup.select("li.search-product")
        logger.debug(f"🛠️ 검색 결과 수: {len(items)}")

        product_infos = []
        for item in items:
            if item.select_one(".ad-badge-text"):
                continue  # 광고 제외

            title_tag = item.select_one("div.name")
            link_tag = item.select_one("a.search-product-link")
            rating_tag = item.select_one("em.rating")
            count_tag = item.select_one("span.rating-total-count")

            if not title_tag or not link_tag or not rating_tag or not count_tag:
                continue

            title = title_tag.get_text(strip=True)
            if exclude_name and exclude_name in title:
                continue

            try:
                rating = float(rating_tag.get_text(strip=True))
                rating_count = int(re.sub(r"[^\d]", "", count_tag.get_text()))
            except:
                continue

            link = "https://www.coupang.com" + link_tag["href"]
            product_infos.append((title, link, rating, rating_count))

        product_infos.sort(key=lambda x: x[2])  # 별점 낮은 순
        selected = product_infos[:max_products]
        logger.info(f"✅ 별점 낮은 제품 {len(selected)}개 선택됨")

        for title, link, rating, count in selected:
            logger.info(f"✅ [{title}] 리뷰 수집 중... (평균 {rating}점, 리뷰 수 {count})")
            reviews = crawl_reviews_by_link(driver, link, max_reviews=max_reviews_per_product)
            all_reviews.extend(reviews)
            time.sleep(2)

        logger.info(f"✅ 총 리뷰 수집 개수: {len(all_reviews)}")
        return all_reviews

    except Exception as e:
        logger.error(f"❌ 카테고리 검색 크롤링 실패: {e}")
        return []

    finally:
        driver.quit()
        logger.debug("🛠️ 드라이버 종료")