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


def init_safe_driver():
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    # options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
    options.binary_location = "/usr/bin/google-chrome"
    driver = uc.Chrome(options=options)
    return driver


# =========================
# 리뷰 수집 (2점 이하 필터링)
# =========================
def crawl_reviews_by_link(driver, url: str, max_reviews: int = 30) -> List[str]:
    logger.debug(f"🔀️ 네이버 상품 리뷰 페이지 요청: {url}")
    reviews = []

    try:
        driver.get(url)
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        review_elements = soup.select(".reviewItems_review_content__0Q2Tg")
        logger.debug(f"🔀️ 전체 리뷰 엘리먼트 수: {len(review_elements)}")

        for el in review_elements:
            rating_tag = el.find_previous("span", class_="reviewItems_average__F6aF2")
            rating = None
            if rating_tag:
                match = re.search(r"[0-9.]+", rating_tag.get_text())
                if match:
                    rating = float(match.group(0))

            if rating is not None and rating > 2:
                continue  # 2점 이하만 수집

            text = el.get_text(strip=True)
            text = re.sub(r"[^\w\s가-힣.,!?]", "", text)
            if text:
                reviews.append(text)

            if len(reviews) >= max_reviews:
                break

        logger.info(f"✅ 별점 2점 이하 리뷰 {len(reviews)}개 수집 완료")
        return reviews

    except Exception as e:
        logger.error(f"❌ 리뷰 크롤링 시도 예외 발생: {e}")
        return []


# =========================
# 카테고리 검색 → 별점 낮은 제품 리뷰 수집
# =========================
def crawl_reviews_by_category(category: str, max_products: int = 3, max_reviews_per_product: int = 10) -> List[str]:
    logger.debug(f"🔀️ 네이버 쇼핑 카테고리 검색 시작: {category}")
    all_reviews = []
    driver = init_safe_driver()

    try:
        base_url = f"https://search.shopping.naver.com/search/all?query={quote(category)}&sort=review&rating=low"
        driver.get(base_url)
        time.sleep(4)
        
        screenshot_path = f"debug_naver_{category}.png"
        driver.save_screenshot(screenshot_path)
        logger.info(f"📸 네이버 검색 결과 스크린샷 저장 완료: {screenshot_path}")
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        items = soup.select("ul.compositeCardList_product_list__hj4JR > li.compositeCardContainer_composite_card_container__r8c8b")
        logger.debug(f"🔀️ 검색 결과 수: {len(items)}")

        product_infos = []
        for item in items:
            link_tag = item.select_one("a.basicProductCard_link__urzND")
            title_tag = item.select_one("strong.basicProductCard_title__VfX3c")
            rating_tag = item.select_one("span.basicProductCard_average__YGapX")

            if not link_tag or not title_tag or not rating_tag:
                continue

            try:
                rating = float(rating_tag.get_text(strip=True))
            except:
                continue

            link = link_tag["href"]
            if link.startswith("/"):
                link = "https://shopping.naver.com" + link

            title = title_tag.get_text(strip=True)
            product_infos.append((title, link, rating))

        product_infos.sort(key=lambda x: x[2])  # 별점 낮은 순
        selected = product_infos[:max_products]
        logger.info(f"✅ 별점 낮은 제품 {len(selected)}개 선택됨")

        for title, link, rating in selected:
            logger.info(f"✅ [{title}] 리뷰 수집 중... (평균 {rating}점)")
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