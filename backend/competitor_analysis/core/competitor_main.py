from backend.competitor_analysis.core.crawler import crawl_reviews_by_category
from utils.logger import get_logger

logger = get_logger(__name__)

def test_crawling():
    logger.debug("🛠️ 경쟁사 리뷰 크롤링 테스트 시작")

    # 테스트 카테고리 예: 블라우스
    category = "블라우스"

    reviews = crawl_reviews_by_category(
        category=category,
        max_products=3,
        max_reviews_per_product=10
    )

    logger.info(f"✅ 최종 수집된 리뷰 개수: {len(reviews)}")
    for i, review in enumerate(reviews, 1):
        print(f"[{i}] {review}")

if __name__ == "__main__":
    test_crawling()