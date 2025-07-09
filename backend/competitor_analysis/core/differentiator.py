import openai
import json
from typing import List, Dict
from utils.logger import get_logger

logger = get_logger(__name__)

def summarize_competitor_reviews(
    reviews: List[str], 
    openai_api_key: str, 
    model: str = "gpt-4o"
) -> str:
    """
    경쟁사 부정 리뷰들을 GPT로 요약해 한글 요약문을 반환한다.

    Args:
        reviews (List[str]): 경쟁사 리뷰 문자열 리스트.
        openai_api_key (str): OpenAI API 키.
        model (str): 사용할 GPT 모델명 (기본: "gpt-4o").

    Returns:
        str: 리뷰 요약 결과 (한글).
    """
    logger.debug(f"🛠️ 리뷰 {len(reviews)}개에 대해 요약 시작 (model={model})")
    client = openai.OpenAI(api_key=openai_api_key)
    joined = "\n".join(reviews)
    prompt = (
        "아래는 경쟁사 상품에 대한 부정적 리뷰들입니다.\n\n"
        f"{joined}\n\n"
        "이 리뷰에서 반복적으로 언급된 불만, 단점, 개선점만 한글로 핵심 키워드 중심으로 3~7개 항목으로 리스트화해줘. "
        "각 항목은 한글 20자 이내로 간결히 써줘. 예를 들어, '배터리 방전 문제', '블루투스 연결 불안정', '음질 저하', '착용감 불편' 등."
    )
    try:
        res = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=256,
            temperature=0.5
        )
        summary = res.choices[0].message.content.strip()
        logger.info("✅ 경쟁사 리뷰 요약 완료")
        return summary
    except Exception as e:
        logger.error(f"❌ 경쟁사 리뷰 요약 중 오류 발생: {type(e).__name__}: {e!r}")
        return ""

def generate_differentiators(
    product_input: Dict,
    competitor_summary: str,
    openai_api_key: str,
    model: str = "gpt-4o"
) -> Dict:
    """
    내 상품 특징과 경쟁사 리뷰 요약을 GPT에 입력하여 
    차별점(differences) 리스트 딕셔너리를 생성한다.

    Args:
        product_input (Dict): 내 상품 정보 딕셔너리 (features, name 필수).
        competitor_summary (str): 경쟁사 리뷰 요약문 (한글).
        openai_api_key (str): OpenAI API 키.
        model (str): 사용할 GPT 모델명 (기본: "gpt-4o").

    Returns:
        Dict: {"differences": [차별점1, 차별점2, ...]} 구조 딕셔너리
    """
    logger.debug("🛠️ 차별점 생성 시작 (generate_differentiators)")
    client = openai.OpenAI(api_key=openai_api_key)
    features = product_input.get('features', '')
    name = product_input.get('name', '')
    prompt = (
        f"내 제품 이름: {name}\n"
        f"특징: {features}\n"
        f"경쟁사 리뷰 요약: {competitor_summary}\n\n"
        "경쟁사 단점이나 불만을 보완하면서, 우리 제품의 강점이 드러나는 차별화 포인트를 2~4개 한글로 짧게 문장 리스트로 만들어줘. "
        "문장은 온점과 ~다로 끝나는게 아닌 ~가능, ~해결 등 명사형으로 끝내줘."
        "아래와 같이 JSON 딕셔너리로 반환해줘. 예시: {\"differences\": [\"...\", \"...\"]}"
    )
    try:
        res = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=256,
            temperature=0.7
        )
        content = res.choices[0].message.content.strip()
        logger.debug(f"🛠️ 차별점 원문 응답: {content}")
        # JSON 파싱
        try:
            start = content.find('{')
            end = content.rfind('}') + 1
            diff_dict = json.loads(content[start:end])
            logger.info("✅ 차별점 JSON 파싱 성공")
            return diff_dict
        except Exception as json_err:
            logger.warning(f"⚠️ JSON 파싱 실패, 리스트 변환 시도: {json_err}")
            lines = [line.strip('-• ').strip() for line in content.split('\n') if line.strip()]
            return {"differences": lines}
    except Exception as e:
        logger.error(f"❌ 차별점 생성 중 오류 발생: {type(e).__name__}: {e!r}")
        return {"differences": []}