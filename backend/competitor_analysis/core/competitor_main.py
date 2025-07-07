from backend.competitor_analysis.core.crawler import (
    crawl_reviews_by_category,
    crawl_reviews_by_link,
    init_safe_driver
)
from backend.competitor_analysis.core.differentiator import (
    summarize_competitor_reviews,
    generate_differentiators
)
from utils.logger import get_logger

logger = get_logger(__name__)

def competitor_main(product_input, openai_api_key):
    """
    주어진 product_input 정보에 따라 경쟁사 리뷰 크롤링(카테고리 또는 링크),
    리뷰 요약, 차별점 리스트(differences)까지 자동 생성.

    Args:
        product_input (dict): 상품 정보 (name, category, features, product_link 등)
        openai_api_key (str): OpenAI API 키

    Returns:
        dict: {
            "reviews": [...],
            "review_summary": "경쟁사 리뷰 요약",
            "differences": [...]
        }
    """
    logger.debug("🛠️ competitor_main 시작")

    # 1. 크롤링 방식 선택
    reviews = []
    link = product_input.get('product_link', '').strip()
    if link == "":
        logger.info("✅ product_link가 없어 카테고리 기반 크롤링 진행")
        reviews = crawl_reviews_by_category(
            category=product_input.get('category', ''),
            max_products=3,
            max_reviews_per_product=10
        )
    else:
        logger.info("✅ product_link가 존재해 해당 링크 리뷰 크롤링 진행")
        driver = init_safe_driver()
        try:
            reviews = crawl_reviews_by_link(driver, link, max_reviews=30)
        finally:
            driver.quit()
            logger.debug("🛠️ 드라이버 종료")

    logger.info(f"✅ 최종 수집된 리뷰 개수: {len(reviews)}")
    if not reviews:
        logger.warning("⚠️ 리뷰가 없어 이후 과정 생략")
        return {
            "reviews": [],
            "review_summary": "",
            "differences": []
        }

    # 2. 리뷰 요약
    summary = summarize_competitor_reviews(reviews, openai_api_key)
    logger.info("✅ 경쟁사 리뷰 요약 완료")

    # 3. 차별점 생성
    diff_dict = generate_differentiators(product_input, summary, openai_api_key)
    differences = diff_dict.get("differences", [])

    logger.info("✅ 차별점 리스트 생성 완료")
    return {
        "reviews": reviews,
        "review_summary": summary,
        "differences": differences
    }

# 사용 예시 (테스트)
if __name__ == "__main__":
    product_input = {
        "name": "지오X1 블루투스 무선 이어폰",
        "category": "무선 이어폰",
        "price": 39900,
        "brand": "GEO",
        "features": "하이파이 음질, 8시간 연속 재생, IPX7 방수, 고감도 마이크, 터치 컨트롤",
        "image_path": "data/input/geo_x1.jpg",
        "product_link": ""  # 링크 있으면 해당 링크, 없으면 카테고리 기반
    }
    openai_api_key = ""  # 본인 키 입력

    result = competitor_main(product_input, openai_api_key)
    print("[경쟁사 부정 리뷰]")
    for i, review in enumerate(result["reviews"], 1):
        print(f"[{i}] {review}")
    print("\n[경쟁사 리뷰 요약]\n", result["review_summary"])
    print("\n[차별점 딕셔너리]\n", result["differences"])