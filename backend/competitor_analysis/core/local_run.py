import threading
import time
from backend.competitor_analysis.core.crawler import crawl_reviews_by_category
from backend.competitor_analysis.core.differentiator import summarize_competitor_reviews
from backend.competitor_analysis.core.competitor_db import insert_review_summary
from backend.competitor_analysis.core.crawl_signal_server import poll_and_process_signal
from utils.logger import get_logger

logger = get_logger(__name__)

def auto_crawl_loop(
    db_config,
    openai_api_key,
    category_list,
    interval=1800  # 30분마다 (초 단위)
):
    """
    유명 카테고리 리스트를 주기적으로 자동 크롤링/요약/DB 저장
    """
    logger.info(f"✅ 자동 크롤링 루프 시작 (주기: {interval}s)")
    while True:
        for category in category_list:
            try:
                logger.info(f"✅ 자동 크롤링 시도: {category}")
                reviews = crawl_reviews_by_category(category, max_products=3, max_reviews_per_product=10)
                if not reviews:
                    logger.warning(f"⚠️ 리뷰 없음: {category}")
                    continue
                summary = summarize_competitor_reviews(reviews, openai_api_key)
                insert_review_summary(
                    host=db_config["host"],
                    user=db_config["user"],
                    password=db_config["password"],
                    db=db_config["db"],
                    category=category,
                    review_summary=summary,
                    num_reviews=len(reviews)
                )
                logger.info(f"✅ 자동 크롤링+요약+저장 완료: {category}")
            except Exception as e:
                logger.error(f"❌ 자동 크롤링/요약/저장 실패: {e}")
        logger.info(f"🛠️ 모든 카테고리 완료, {interval}초 대기")
        time.sleep(interval)

def start_local_crawler(
    db_config,
    openai_api_key,
    category_list,
    auto_crawl_interval=1800,
    signal_poll_interval=10
):
    """
    로컬에서 자동 크롤링 루프 + 신호 polling/처리 스레드를 동시에 실행
    """
    # 1. 자동 크롤링용 스레드
    t1 = threading.Thread(
        target=auto_crawl_loop,
        args=(db_config, openai_api_key, category_list, auto_crawl_interval),
        daemon=True
    )
    t1.start()

    # 2. 신호 polling/처리용 스레드 (신호 감지 시 → 카테고리 리뷰 크롤링/요약/저장)
    t2 = threading.Thread(
        target=poll_and_process_signal,
        args=(db_config["host"], db_config["user"], db_config["password"], db_config["db"], openai_api_key, signal_poll_interval),
        daemon=True
    )
    t2.start()

    logger.info("✅ 자동 크롤링/신호 polling 스레드 모두 시작")
    # 메인 스레드는 무한 대기
    while True:
        time.sleep(3600)