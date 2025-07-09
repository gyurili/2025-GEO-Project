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
    여러 유명 카테고리를 대상으로 주기적으로 크롤링/요약/DB 저장을 자동 수행하는 루프.

    Args:
        db_config (dict): DB 연결정보 (host, user, password, db)
        openai_api_key (str): OpenAI API 키
        category_list (list): 크롤링 대상 카테고리 리스트
        interval (int): 반복 주기(초) - 기본 1800초(30분)
    """
    logger.info(f"✅ 자동 크롤링 루프 시작 (주기: {interval}s)")
    while True:
        for category in category_list:
            try:
                logger.info(f"✅ 자동 크롤링 시도: {category}")
                reviews = crawl_reviews_by_category(
                    category,
                    max_products=3,
                    max_reviews_per_product=10
                )
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
                logger.info(f"✅ 자동 크롤링+요약+DB저장 완료: {category}")
            except Exception as e:
                logger.error(f"❌ 자동 크롤링/요약/저장 실패: {type(e).__name__}: {e!r}")
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
    로컬 크롤러를 시작:
    - 1) 유명 카테고리 자동 크롤링/요약/저장 루프
    - 2) GCP 등에서 신호가 오면 polling 후 해당 카테고리 즉시 크롤링/저장
    를 동시에 병렬(스레드)로 실행

    Args:
        db_config (dict): DB 연결정보 (host, user, password, db)
        openai_api_key (str): OpenAI API 키
        category_list (list): 크롤링 대상 카테고리 리스트
        auto_crawl_interval (int): 자동 크롤링 루프 주기(초)
        signal_poll_interval (int): 신호 polling 주기(초)
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
        args=(
            db_config["host"],
            db_config["user"],
            db_config["password"],
            db_config["db"],
            openai_api_key,
            signal_poll_interval
        ),
        daemon=True
    )
    t2.start()

    logger.info("✅ 자동 크롤링/신호 polling 스레드 모두 시작")
    # 메인 스레드는 무한 대기
    while True:
        time.sleep(3600)