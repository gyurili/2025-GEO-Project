from backend.competitor_analysis.core.crawler import crawl_reviews_by_category
from backend.competitor_analysis.core.differentiator import (
    summarize_competitor_reviews,
    generate_differentiators
)
from utils.logger import get_logger

logger = get_logger(__name__)

def test_competitor_analysis(product_input, openai_api_key):
    logger.debug("🛠️ 경쟁사 리뷰 크롤링 + 요약 + 차별점 생성 테스트 시작")

    # 1. 크롤러로 경쟁사 리뷰 수집
    reviews = crawl_reviews_by_category(
        category=product_input.get('category', ''),
        max_products=3,
        max_reviews_per_product=10
    )
    logger.info(f"✅ 최종 수집된 리뷰 개수: {len(reviews)}")
    for i, review in enumerate(reviews, 1):
        print(f"[{i}] {review}")

    if not reviews:
        logger.warning("⚠️ 리뷰가 없어 이후 과정 생략")
        return

    # 4. 경쟁사 리뷰 요약 (differentiator에서 불러옴)
    summary = summarize_competitor_reviews(reviews, openai_api_key)
    print("\n[경쟁사 리뷰 요약]\n", summary)

    # 5. 차별점 생성 (differentiator에서 불러옴)
    diff_dict = generate_differentiators(product_input, summary, openai_api_key)
    print("\n[차별점 딕셔너리]\n", diff_dict)

if __name__ == "__main__":
    product_input = {
        "name": "지오X1 블루투스 무선 이어폰",
        "category": "무선 이어폰",
        "price": 39900,
        "brand": "GEO",
        "features": "하이파이 음질, 8시간 연속 재생, IPX7 방수, 고감도 마이크, 터치 컨트롤",
        "image_path": "data/input/geo_x1.jpg",
        "product_link": "https://www.coupang.com/vp/products/example_id"
    }
    openai_api_key=""
    test_competitor_analysis(product_input, openai_api_key)