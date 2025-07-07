import openai
import json
from typing import List, Dict

def summarize_competitor_reviews(
    reviews: List[str], 
    openai_api_key: str, 
    model: str = "gpt-4o"
) -> str:
    """
    경쟁사 부정 리뷰들을 GPT로 요약해 한글 요약문을 반환 (openai 1.x+)
    """
    client = openai.OpenAI(api_key=openai_api_key)
    joined = "\n".join(reviews)
    prompt = (
        "아래는 경쟁사 상품에 대한 부정적 리뷰들입니다.\n\n"
        f"{joined}\n\n"
        "이 리뷰에서 자주 언급된 불만, 단점, 개선점만 한글로 간결히 요약해줘."
    )
    res = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=256,
        temperature=0.5
    )
    return res.choices[0].message.content.strip()

def generate_differentiators(
    product_input: Dict,
    competitor_summary: str,
    openai_api_key: str,
    model: str = "gpt-4o"
) -> Dict:
    """
    내 상품 특징과 경쟁사 리뷰 요약을 합쳐 차별점(differences) 리스트 딕셔너리 생성 (openai 1.x+)
    """
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
    res = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=256,
        temperature=0.7
    )
    content = res.choices[0].message.content.strip()
    # JSON 파싱 시도
    try:
        start = content.find('{')
        end = content.rfind('}') + 1
        return json.loads(content[start:end])
    except Exception:
        # 파싱 실패 시 단순 리스트 반환
        lines = [line.strip('-• ').strip() for line in content.split('\n') if line.strip()]
        return {"differences": lines}