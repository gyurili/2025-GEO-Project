import asyncio
from backend.competitor_analysis.core.differentiator import generate_differentiators
from backend.competitor_analysis.core.competitor_db import get_latest_review_summary
from backend.competitor_analysis.core.crawl_signal_server import send_crawl_request_signal
from utils.config import get_openai_api_key, get_db_config
from utils.logger import get_logger

logger = get_logger(__name__)

async def competitor_main(
    product_input: dict,
    poll_interval=5,
    poll_timeout=120
) -> dict:
    """
    경쟁사 리뷰 분석 및 차별점 리스트 도출 (딕셔너리만 사용)
    1. DB에 요약본 있으면 바로 사용.
    2. 없으면 신호 송신→DB polling→요약본 확보 후 차별점 생성.

    Args:
        product_input (dict): 상품명, 카테고리, 특징 등 상세 정보
        poll_interval (int): polling 간격(초)
        poll_timeout (int): polling 최대 대기시간(초)

    Returns:
        dict: 경쟁사 차별점 리스트 {'differences': List[str]}
    """
    logger.debug("🛠️ competitor_main 시작")
    try:
        logger.debug("🛠️ openai_api_key, db_config 로딩 시도")
        openai_api_key = get_openai_api_key()
        db_config = get_db_config()
        category = product_input.get("category", "")

        logger.debug(f"🛠️ DB에서 최신 리뷰 요약본 조회 시도 (category={category})")
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
            logger.warning("⚠️ 리뷰 요약본 미존재, 신호 송신 및 polling 대기 시작")
            send_crawl_request_signal(
                db_config["host"],
                db_config["user"],
                db_config["password"],
                db_config["db"],
                category
            )
            waited = 0
            while waited < poll_timeout:
                logger.debug(f"🛠️ {poll_interval}초 대기 후 요약본 재조회 예정 (누적 {waited}/{poll_timeout})")
                await asyncio.sleep(poll_interval)
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
                    logger.debug(f"🛠️ 리뷰 요약본 polling 대기 중... ({waited}/{poll_timeout}s)")
            else:
                logger.error("❌ polling timeout - 리뷰 요약본 생성 실패")
                return {"differences": []}

        logger.debug("🛠️ 차별점 문장 생성(generate_differentiators) 시도")
        diff_dict = generate_differentiators(product_input, summary, openai_api_key)
        differences = diff_dict.get("differences", [])

        if differences:
            logger.info("✅ 차별점 리스트 생성 완료")
        else:
            logger.warning("⚠️ 차별점 문장 생성 결과가 비어 있음")

        return {"differences": differences}
    except Exception as e:
        logger.error(f"❌ 경쟁사 분석 실패: {type(e).__name__}: {e!r}")
        return {"differences": []}

if __name__ == "__main__":
    # 테스트용 입력 데이터
    test_product = {
        "name": "쿠쿠 IH 전기압력밥솥 6인용",
        "category": "주방용품",
        "price": 189000,
        "brand": "쿠쿠",
        "features": "IH 가열, 6인용, 분리형 커버, 예약취사, 고압모드 지원",
        "image_path": "",
        "css_type": 1
    }

    # competitor_main은 async 함수이므로 asyncio.run으로 호출!
    result = asyncio.run(competitor_main(test_product))
    print("분석 결과:", result)
    print("차별점 리스트:", result.get("differences", []))