from backend.competitor_analysis.core.differentiator import generate_differentiators
from backend.competitor_analysis.core.competitor_db import get_latest_review_summary
from backend.competitor_analysis.core.crawl_signal_server import send_crawl_request_signal
from utils.logger import get_logger
import time

logger = get_logger(__name__)

def competitor_main(
    product_input,
    openai_api_key,
    db_config,
    poll_interval=5,
    poll_timeout=120
):
    """
    카테고리로 DB에 요약본이 있으면 바로 사용.
    없으면 신호 송신→DB polling→요약본 확보 후 차별점 문장 생성.

    Args:
        product_input (dict): 상품 정보 (name, category, features, product_link 등)
        openai_api_key (str): OpenAI API 키
        db_config (dict): DB 연결정보 (host, user, password, db)
        poll_interval (int): polling 간격(초)
        poll_timeout (int): polling 최대 대기시간(초)

    Returns:
        dict: {
            "review_summary": "경쟁사 리뷰 요약",
            "differences": [...]
        }
    """
    logger.debug("🛠️ competitor_main 동기 DB조회/신호 모드 시작")
    category = product_input.get("category", "")
    # 1. DB에 이미 저장된 요약본이 있으면 바로 사용
    summary = get_latest_review_summary(
        db_config["host"],
        db_config["user"],
        db_config["password"],
        db_config["db"],
        category
    )
    if summary:
        logger.info("✅ DB에서 최신 리뷰 요약본 바로 사용")
    else:
        logger.info("⚠️ 리뷰 요약본 미존재, 신호 송신 및 대기")
        send_crawl_request_signal(
            db_config["host"],
            db_config["user"],
            db_config["password"],
            db_config["db"],
            category
        )
        waited = 0
        while waited < poll_timeout:
            time.sleep(poll_interval)
            waited += poll_interval
            summary = get_latest_review_summary(
                db_config["host"],
                db_config["user"],
                db_config["password"],
                db_config["db"],
                category
            )
            if summary:
                logger.info(f"✅ {waited}초만에 리뷰 요약본 생성 완료")
                break
            else:
                logger.debug(f"🛠️ 리뷰 요약본 대기 중... ({waited}/{poll_timeout}s)")
        else:
            logger.error("❌ polling timeout - 리뷰 요약본 생성 실패")
            return {"review_summary": "", "differences": []}

    # 2. 차별점 문장 생성 (GPT)
    diff_dict = generate_differentiators(product_input, summary, openai_api_key)
    differences = diff_dict.get("differences", [])

    logger.info("✅ 차별점 리스트 생성 완료")
    return {
        "review_summary": summary,
        "differences": differences
    }