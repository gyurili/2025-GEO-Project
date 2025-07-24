import pymysql
import time
from datetime import datetime
from backend.competitor_analysis.crawler import crawl_reviews_by_category
from backend.competitor_analysis.differentiator import summarize_competitor_reviews
from backend.competitor_analysis.competitor_db import insert_review_summary
from utils.logger import get_logger

logger = get_logger(__name__)

def send_crawl_request_signal(host, user, password, db, category):
    """
    크롤러 실행 신호를 crawl_request_signal 테이블에 등록(요청)합니다.

    Args:
        host (str): DB 호스트 주소
        user (str): DB 사용자명
        password (str): DB 비밀번호
        db (str): 데이터베이스명
        category (str): 크롤링을 요청할 상품 카테고리

    Returns:
        None
    """
    logger.debug(f"🛠️ 크롤러 요청 신호 전송 시작: {category}")
    try:
        conn = pymysql.connect(
            host=host, user=user, password=password, db=db, port=3306, charset='utf8mb4'
        )
        with conn.cursor() as cur:
            sql = """
            INSERT INTO crawl_request_signal (category, status, requested_at)
            VALUES (%s, 'pending', %s)
            """
            cur.execute(sql, (category, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        logger.info(f"✅ 크롤러 요청 신호 전송 완료: {category}")
    except Exception as e:
        logger.error(f"❌ 신호 전송 실패: {type(e).__name__}: {e!r}")
    finally:
        try:
            conn.close()
            logger.debug("🛠️ DB 연결 종료")
        except Exception as e:
            logger.warning(f"⚠️ DB 연결 종료 중 예외 발생: {type(e).__name__}: {e!r}")

def poll_and_process_signal(host, user, password, db, openai_api_key, interval=10):
    """
    신호(pending) 감지 시 → 1. 카테고리 리뷰 크롤링 → 2. 요약 → 3. DB 저장까지 자동 수행.

    Args:
        host (str): DB 호스트 주소
        user (str): DB 사용자명
        password (str): DB 비밀번호
        db (str): 데이터베이스명
        openai_api_key (str): OpenAI API 키
        interval (int, optional): polling 주기(초), 기본값 10초

    Returns:
        None
    """
    logger.debug(f"🛠️ 신호 polling 루프 시작 (interval={interval}s)")
    while True:
        try:
            conn = pymysql.connect(
                host=host, user=user, password=password, db=db, port=3306, charset='utf8mb4'
            )
            with conn.cursor() as cur:
                # 가장 오래된 미처리 신호(카테고리) 조회
                cur.execute("""
                    SELECT id, category FROM crawl_request_signal
                    WHERE status='pending' ORDER BY requested_at ASC LIMIT 1
                """)
                row = cur.fetchone()
                if row:
                    signal_id, category = row
                    logger.info(f"✅ 신호 감지: '{category}' 크롤링 및 요약 시작")

                    # 1️경쟁사 리뷰 크롤링
                    reviews = crawl_reviews_by_category(
                        category=category,
                        max_products=3,
                        max_reviews_per_product=10
                    )
                    logger.info(f"✅ 크롤링 완료: {len(reviews)}개 리뷰")

                    if not reviews:
                        logger.warning(f"⚠️ 수집된 리뷰 없음, 신호만 완료 처리")
                    else:
                        # 2️리뷰 요약
                        summary = summarize_competitor_reviews(reviews, openai_api_key)
                        logger.info("✅ 리뷰 요약 완료")

                        # 3️DB 저장
                        insert_review_summary(
                            host=host,
                            user=user,
                            password=password,
                            db=db,
                            category=category,
                            review_summary=summary,
                            num_reviews=len(reviews)
                        )
                        logger.info("✅ 리뷰 요약본 DB 저장 완료")

                    # 신호 완료 처리 (done 표시 및 완료 시각)
                    cur.execute("""
                        UPDATE crawl_request_signal
                        SET status='done', completed_at=%s
                        WHERE id=%s
                    """, (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), signal_id))
                    conn.commit()
                    logger.info(f"✅ 신호 처리 완료: '{category}'")
                else:
                    logger.debug("🛠️ 처리 대기 신호 없음 (다음 확인까지 대기)")
            conn.close()
        except Exception as e:
            logger.error(f"❌ 신호 감지/처리 중 오류: {type(e).__name__}: {e!r}")
        time.sleep(interval)