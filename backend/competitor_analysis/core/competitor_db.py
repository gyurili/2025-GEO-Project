import pymysql
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)

def insert_review_summary(
    host: str,
    user: str,
    password: str,
    db: str,
    category: str,
    review_summary: str,
    num_reviews: int
):
    """
    경쟁사 리뷰 요약본을 MySQL DB에 저장합니다.

    Args:
        host (str): DB 호스트 주소(IP 또는 도메인)
        user (str): DB 사용자명
        password (str): DB 비밀번호
        db (str): 데이터베이스 이름
        category (str): 상품 카테고리명
        review_summary (str): 요약된 리뷰 내용(문자열)
        num_reviews (int): 크롤링된 리뷰 개수

    Returns:
        None
    """
    logger.debug(f"🛠️ 리뷰 요약본 저장 시작: category={category}, num_reviews={num_reviews}")
    crawled_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        conn = pymysql.connect(
            host=host,
            user=user,
            password=password,
            db=db,
            port=3306,
            charset='utf8mb4'
        )
        with conn.cursor() as cur:
            sql = """
            INSERT INTO competitor_review_summary (category, review_summary, num_reviews, crawled_at)
            VALUES (%s, %s, %s, %s)
            """
            cur.execute(sql, (category, review_summary, num_reviews, crawled_at))
        conn.commit()
        logger.info("✅ 리뷰 요약본 DB 저장 완료")
    except Exception as e:
        logger.error(f"❌ 리뷰 요약본 저장 실패: {type(e).__name__}: {e!r}")
    finally:
        try:
            conn.close()
            logger.debug("🛠️ DB 연결 종료")
        except Exception as e:
            logger.warning(f"⚠️ DB 연결 종료 중 예외 발생: {type(e).__name__}: {e!r}")

def get_latest_review_summary(
    host: str,
    user: str,
    password: str,
    db: str,
    category: str
) -> str:
    """
    주어진 카테고리에서 가장 최근에 저장된 리뷰 요약본을 반환합니다.

    Args:
        host (str): DB 호스트 주소(IP 또는 도메인)
        user (str): DB 사용자명
        password (str): DB 비밀번호
        db (str): 데이터베이스 이름
        category (str): 상품 카테고리명

    Returns:
        str: 가장 최근에 저장된 리뷰 요약본(없으면 None)
    """
    logger.debug(f"🛠️ 최근 리뷰 요약본 조회 시작: category={category}")
    try:
        conn = pymysql.connect(
            host=host,
            user=user,
            password=password,
            db=db,
            port=3306,
            charset='utf8mb4'
        )
        with conn.cursor() as cur:
            sql = """
            SELECT review_summary
            FROM competitor_review_summary
            WHERE category=%s
            ORDER BY crawled_at DESC
            LIMIT 1
            """
            cur.execute(sql, (category,))
            row = cur.fetchone()
            if row:
                logger.info("✅ 최근 리뷰 요약본 조회 성공")
                return row[0]
            else:
                logger.warning("⚠️ 해당 카테고리의 리뷰 요약본이 없습니다")
                return None
    except Exception as e:
        logger.error(f"❌ 리뷰 요약본 조회 실패: {type(e).__name__}: {e!r}")
        return None
    finally:
        try:
            conn.close()
            logger.debug("🛠️ DB 연결 종료")
        except Exception as e:
            logger.warning(f"⚠️ DB 연결 종료 중 예외 발생: {type(e).__name__}: {e!r}")