import threading
import time
from datetime import datetime
import pymysql

from backend.competitor_analysis.crawler import crawl_reviews_by_category
from backend.competitor_analysis.differentiator import summarize_competitor_reviews
from backend.competitor_analysis.competitor_db import insert_review_summary
from backend.competitor_analysis.crawl_signal_server import poll_and_process_signal
from utils.logger import get_logger

logger = get_logger(__name__)

def get_categories_with_last_time(host, user, password, db):
    """
    competitor_review_summary 테이블에서
    카테고리별로 최신 크롤링 시간을 조회합니다.

    Args:
        host (str): DB 호스트
        user (str): DB 사용자명
        password (str): DB 비밀번호
        db (str): DB 이름

    Returns:
        list of tuple: [(category(str), last_crawled_at(datetime)), ...]
    """
    logger.debug("🛠️ 카테고리별 최신 크롤링 시간 조회 시작")
    conn = pymysql.connect(
        host=host,
        user=user,
        password=password,
        db=db,
        port=3306,
        charset='utf8mb4'
    )
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT category, MAX(crawled_at) as last_crawled_at
                FROM competitor_review_summary
                GROUP BY category
            """
            cursor.execute(sql)
            results = cursor.fetchall()
            logger.debug(f"🛠️ 카테고리별 조회 결과: {results}")
            return results
    except Exception as e:
        logger.error(f"❌ 카테고리별 최신 크롤링 시간 조회 실패: {type(e).__name__}: {e!r}")
        return []
    finally:
        conn.close()
        logger.debug("🛠️ DB 연결 종료")

def auto_crawl_loop(
    db_config,
    openai_api_key,
    interval=1800
):
    """
    competitor_review_summary 테이블에 저장된
    모든 카테고리별로 주기적으로 크롤링/요약/DB 저장을 수행합니다.
    (카테고리별 마지막 저장 시점 이후 interval(초) 이상 경과한 경우만 처리)

    Args:
        db_config (dict): DB 연결 정보
        openai_api_key (str): OpenAI API 키
        interval (int): 카테고리별 최소 크롤링 간격(초)
    """
    logger.info(f"✅ 자동 크롤링 루프 시작 (카테고리별 최소 주기: {interval}s)")
    while True:
        logger.debug("🛠️ 전체 카테고리 조회 시도")
        categories_with_time = get_categories_with_last_time(
            db_config["host"], db_config["user"], db_config["password"], db_config["db"]
        )
        if not categories_with_time:
            logger.warning("⚠️ DB에 등록된 카테고리가 없습니다. 60초 후 재시도")
            time.sleep(60)
            continue

        for category, last_time in categories_with_time:
            logger.debug(f"🛠️ {category} - 마지막 저장 시각: {last_time}")
            now = datetime.now()
            # last_time이 str이라면 datetime으로 변환
            if last_time and isinstance(last_time, str):
                try:
                    last_time = datetime.strptime(last_time, "%Y-%m-%d %H:%M:%S")
                except Exception:
                    logger.warning(f"⚠️ {category} - last_time 파싱 실패, 무시하고 진행")
                    last_time = None

            if last_time is not None and (now - last_time).total_seconds() < interval:
                logger.info(f"⏩ {category} 스킵: 마지막 저장 {last_time}, interval 미도달")
                continue

            try:
                logger.debug(f"🛠️ {category} 크롤링 시도")
                reviews = crawl_reviews_by_category(
                    category,
                    max_products=3,
                    max_reviews_per_product=10
                )
                if not reviews:
                    logger.warning(f"⚠️ 리뷰 없음: {category}")
                    continue
                logger.debug(f"🛠️ {category} 리뷰 요약 시도")
                summary = summarize_competitor_reviews(reviews, openai_api_key)
                logger.debug(f"🛠️ {category} DB 저장 시도")
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
                logger.error(f"❌ 자동 크롤링/요약/저장 실패: {category}, {type(e).__name__}: {e!r}")
        logger.info(f"🛠️ 모든 카테고리 완료, 60초 대기")
        time.sleep(60)

def start_local_crawler(
    db_config,
    openai_api_key,
    auto_crawl_interval=1800,
    signal_poll_interval=10
):
    """
    자동 크롤링 루프 및 신호 polling/처리 루프를 각각 스레드로 실행합니다.

    Args:
        db_config (dict): DB 연결 정보
        openai_api_key (str): OpenAI API 키
        auto_crawl_interval (int): 카테고리별 자동 크롤링 간격(초)
        signal_poll_interval (int): 신호 polling 간격(초)
    """
    logger.debug("🛠️ 자동 크롤링 스레드 시작")
    t1 = threading.Thread(
        target=auto_crawl_loop,
        args=(db_config, openai_api_key, auto_crawl_interval),
        daemon=True
    )
    t1.start()

    logger.debug("🛠️ 신호 polling 스레드 시작")
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
    while True:
        time.sleep(3600)

if __name__ == "__main__":
    from utils.config import get_openai_api_key, get_db_config

    logger.debug("🛠️ main 진입 확인")

    # 1. 설정/키 불러오기 (utils 함수 그대로 활용)
    openai_api_key = get_openai_api_key()
    db_config = get_db_config()

    # 2. 크롤러 시작
    try:
        start_local_crawler(
            db_config=db_config,
            openai_api_key=openai_api_key,
            auto_crawl_interval=36000,   # 10시간마다 자동 저장
            signal_poll_interval=5       # 5초마다 polling
        )
        logger.info("✅ main 실행 성공")
    except Exception as e:
        logger.error(f"❌ main 진입/실행 실패: {type(e).__name__}: {e!r}")
        print("main 예외:", e)