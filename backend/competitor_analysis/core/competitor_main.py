import asyncio
from backend.competitor_analysis.schemas.input_schema import ProductInput
from backend.competitor_analysis.schemas.output_schema import CompetitorOutput
from backend.competitor_analysis.core.differentiator import generate_differentiators
from backend.competitor_analysis.core.competitor_db import get_latest_review_summary
from backend.competitor_analysis.core.crawl_signal_server import send_crawl_request_signal
from utils.config import get_openai_api_key, get_db_config
from utils.logger import get_logger

logger = get_logger(__name__)

async def competitor_main(
    product_input: ProductInput,
    poll_interval=5,
    poll_timeout=120
) -> CompetitorOutput:
    """
    경쟁사 리뷰 분석 및 차별점 리스트 도출 (라우터/엔드포인트 없이 단일 함수)
    1. DB에 요약본 있으면 바로 사용.
    2. 없으면 신호 송신→DB polling→요약본 확보 후 차별점 생성.

    Args:
        product_input (ProductInput): 상품명, 카테고리, 특징 등 상세 정보
        poll_interval (int): polling 간격(초)
        poll_timeout (int): polling 최대 대기시간(초)

    Returns:
        CompetitorOutput: 경쟁사 차별점 리스트 (differences: List[str])
    """
    logger.debug("🛠️ competitor_main 시작")
    try:
        logger.debug("🛠️ openai_api_key, db_config 로딩 시도")
        openai_api_key = get_openai_api_key()
        db_config = get_db_config()
        product_input_dict = product_input.model_dump()
        category = product_input_dict.get("category", "")

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
                return CompetitorOutput(differences=[])

        logger.debug("🛠️ 차별점 문장 생성(generate_differentiators) 시도")
        diff_dict = generate_differentiators(product_input_dict, summary, openai_api_key)
        differences = diff_dict.get("differences", [])

        if differences:
            logger.info("✅ 차별점 리스트 생성 완료")
        else:
            logger.warning("⚠️ 차별점 문장 생성 결과가 비어 있음")

        return CompetitorOutput(differences=differences)
    except Exception as e:
        logger.error(f"❌ 경쟁사 분석 실패: {type(e).__name__}: {e!r}")
        return CompetitorOutput(differences=[])