from dotenv import load_dotenv
load_dotenv()
import os
import sys
from openai import OpenAI
from utils.logger import get_logger
from core.cleaner import clean_response
from core.prompt_builder import *

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
logger = get_logger(__name__)


def generate_html(product: dict) -> dict:
    """
    프롬프트 명령을 통해 상세페이지 생성
    """
    prompt = "\n".join([
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
        "모든 정보를 HTML로 출력해주세요. 제공된 정보를 바탕으로 상세페이지를 풍성하고 길게 만들어주세요.",
        "결과는 <html> ~ </html> 태그 안에 있어야 합니다",
    ])
    logger.info("📄 OpenAI 요청 시작")

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9
    )
    logger.info("📄 OpenAI API 응답 수신 완료")

    html_text = response.choices[0].message.content
    html_text = clean_response(html_text)
    
    return {"html_text": html_text}

