from fastapi import APIRouter, HTTPException
from backend.competitor_analysis.schemas.input_schema import ProductInput
from backend.competitor_analysis.schemas.output_schema import CompetitorOutput
from backend.competitor_analysis.core.competitor_main import competitor_main
from utils.config import get_openai_api_key
from utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.post("/analyze", response_model=CompetitorOutput, summary="경쟁사 리뷰 분석 및 차별점 생성")
async def analyze_competitor(
    product_input: ProductInput,
) -> CompetitorOutput:
    """
    경쟁사 리뷰 분석 및 차별점 리스트 도출 API

    상품 정보(ProductInput)를 입력하면,
    1. 경쟁사 리뷰 크롤링 (쿠팡/카테고리 or 직접 링크)
    2. GPT 기반 요약 및 차별점(differences) 생성
    3. 차별점 리스트를 반환

    Args:
        product_input (ProductInput): 상품명, 카테고리, 특징 등 상세 정보 입력

    Returns:
        CompetitorOutput: 경쟁사 차별점 리스트 반환 (differences: List[str])

    Raises:
        HTTPException: 경쟁사 분석에 실패하거나 예외 발생 시 500 에러 반환

    Example:
        >>> POST /competitor/analyze
        >>> {
                "name": "우일 여성 여름 인견 7부 블라우스",
                "category": "블라우스",
                "price": 18000,
                "brand": "우일",
                "features": "인견 소재, 우수한 흡수성과 통기성, 부드러운 촉감",
                "image_path": "data/input/product.jpg",
                "product_link": "https://www.coupang.com/vp/products/example_id",
                "css_type": 1
            }
        >>> Response: { "differences": ["땀 흡수력 강화", "부드러운 촉감", ...] }
    """
    logger.debug("🛠️ /analyze 엔드포인트 호출")
    try:
        openai_api_key = get_openai_api_key()
        product_input_dict = product_input.dict()
        result = competitor_main(product_input_dict, openai_api_key)
        return CompetitorOutput(differences=result.get("differences", []))
    except Exception as e:
        logger.error(f"❌ 경쟁사 분석 실패: {type(e).__name__}: {e!r}")
        raise HTTPException(status_code=500, detail="경쟁사 분석 중 오류 발생")