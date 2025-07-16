from dotenv import load_dotenv
load_dotenv()
import os
import sys
from openai import OpenAI
from utils.logger import get_logger
from backend.text_generator.cleaner import clean_response
from backend.text_generator.prompt_builder import *

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
logger = get_logger(__name__)


def generate_html(product: dict) -> dict:
    """
    제공된 제품 정보를 바탕으로 OpenAI를 통해 상세페이지 HTML을 생성합니다.
    
    Args:
        product (dict): 상세페이지 생성에 필요한 제품 정보가 담긴 딕셔너리

    Returns:
        dict: 생성된 상세페이지 HTML이 포함된 딕셔너리
    """
    prompt_parts = [
        apply_schema_prompt(product),
        natural_tone_prompt(),
        keyword_variation_prompt(),
        html_structure_prompt(),
        qna_format_prompt(),
        quantitative_prompt(),
        expert_quote_prompt(),
        fluent_prompt(),
        expand_product_details(),
        css_friendly_prompt(),
    ]

    if product.get("differences"):
        diff_prompt = "\n".join([
            "이 상품은 다음과 같은 차별점을 가지고 있습니다:",
            *[f"- {item}" for item in product["differences"]],
            "위 차별점들을 상세페이지 내용에서 자연스럽게 강조해 주세요."
        ])
        prompt_parts.insert(1, diff_prompt)
    
    prompt_parts += [
        "모든 정보를 HTML로 출력해주세요. 제공된 정보를 바탕으로 상세페이지를 풍성하고 길게 만들어주세요.",
        "결과는 <html> ~ </html> 태그 안에 있어야 합니다"
    ]
    
    prompt = "\n".join(prompt_parts)
    logger.info("🛠️ OpenAI 요청 시작")

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9
    )
    logger.info("✅ OpenAI API 응답 수신 완료")

    html_text = response.choices[0].message.content
    html_text = clean_response(html_text)
    logger.info("✅ 코드 마크다운 블록 제거 완료")
    
    return {"html_text": html_text}

