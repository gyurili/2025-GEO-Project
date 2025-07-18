from dotenv import load_dotenv
load_dotenv()
import os
import sys
from openai import OpenAI
from utils.logger import get_logger

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
logger = get_logger(__name__)

def build_prompt(
        product: dict,
    ) -> dict:
    return f"""
    - 상품명: {product['name']}
    - 카테고리: {product['category']}
    - 가격: {product['price']}원
    - 브랜드: {product['brand']}
    - 특징: {product['features']}
    """


def generate_background_prompt(product: dict) -> str | None:
    """
    제품 정보를 바탕으로, 해당 제품에 어울리는 배경 생성용 영어 프롬프트를 생성합니다.
    예: "a wooden bathroom shelf with soft natural light, suitable for skincare product"
    """
    try:
        system_prompt = (
            "You are a prompt designer for AI image generation.\n\n"
            "Based on the product description in Korean, write an English prompt that shows a person naturally using the product.\n\n"
            "- The person can be fully visible (face allowed) but the product must be the main focus.\n"
            "- Make the scene realistic and relatable, like a lifestyle photo.\n"
            "- Avoid distractions: no unnecessary objects, no text overlays, no logos.\n"
            "- The background should complement the product, not overpower it.\n"
            "- Output one short sentence in English, under 15 words."
        )

        user_prompt = build_prompt(product)

        logger.debug(f"🛠️ 배경 프롬프트 생성 시작")
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
        )

        prompt_text = response.choices[0].message.content.strip()
        logger.info(f"✅ 생성된 배경 프롬프트: {prompt_text}")
        return prompt_text

    except Exception as e:
        logger.error(f"❌ 배경 프롬프트 생성 실패: {e}")
        return None


def generate_human_prompt(product: dict) -> str | None:
    """
    사람이 제품을 사용하는 장면을 묘사하는 프롬프트 생성
    """
    try:
        system_prompt = (
            "You are a visual prompt engineer. Based on the product description in Korean, "
            "list visual elements that should NOT appear in the image so the product remains the main focus.\n"
            "- Exclude text, logos, busy patterns, excessive clutter, irrelevant objects, and flashy colors.\n"
            "- Do NOT exclude faces or people.\n"
            "- Output a comma-separated list of keywords only.\n"
            "- Example: text, logo, clutter, busy background, bright colors, excessive objects."
        )

        user_prompt = build_prompt(product)  # 기존 제품 요약 한국어 문자열

        logger.debug(f"🛠️ 사람 프롬프트 생성 시작")
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
        )

        human_prompt = response.choices[0].message.content.strip()
        logger.info(f"✅ 생성된 사람 프롬프트: {human_prompt}")
        return human_prompt

    except Exception as e:
        logger.error(f"❌ 사람 프롬프트 생성 실패: {e}")
        return None


def generate_negative_prompt(product: dict) -> str | None:
    """
    제품과 겹치지 않는 배경을 만들기 위해, 배제할 요소(negative prompt)를 영어로 생성합니다.
    """
    try:
        system_prompt = (
            "You are a visual prompt engineer. Based on the product description in Korean, "
            "list visual elements that should NOT appear in the background so the product stands out clearly.\n"
            "- Include things like distracting textures, objects, people, or strong visual elements.\n"
            "- Always exclude face, eyes, portrait, logo, text, busy patterns, and bright or flashy colors.\n"
            "- Output a comma-separated list of keywords only, not full sentences.\n"
            "- Example: face, eyes, portrait, hands, logo, text, clutter, bright colors, busy background, background people."
        )

        user_prompt = build_prompt(product)  # 기존 제품 요약 한국어 문자열

        logger.debug(f"🛠️ 부정 프롬프트 생성 시작")
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
        )

        neg_prompt = response.choices[0].message.content.strip()
        logger.info(f"✅ 생성된 네거티브 프롬프트: {neg_prompt}")
        return neg_prompt

    except Exception as e:
        logger.error(f"❌ 네거티브 프롬프트 생성 실패: {e}")
        return None

def generate_prompts(product: dict, mode: str = "background") -> dict:
    """
    mode: "background" or "human"
    """
    if mode == "human":
        prompt = generate_human_prompt(product)
    else:
        prompt = generate_background_prompt(product)

    neg_prompt = generate_negative_prompt(product)
    return {
        "background_prompt": prompt,
        "negative_prompt": neg_prompt
    }


def classify_product(product: dict) -> str | None:
    """
    OpenAI 모델을 사용하여 제품을 상의/하의/세트/신발/장갑/모자 중 하나로 분류합니다.

    Args:
        product (dict): 제품 정보 (예: {"name": "스트라이프 셔츠", "category": "패션", "price": 30000, "brand": "ABC", "features": "면소재, 여름용"})

    Returns:
        str: 분류 결과 ("상의", "하의", "세트", "신발", "장갑", "모자") 중 하나
    """
    try:
        system_prompt = (
            "당신은 패션 카테고리 분류 전문가입니다.\n\n"
            "주어진 제품 정보를 읽고, 다음 중 하나로만 답하세요:\n"
            "- 상의\n- 하의\n- 세트\n- 신발\n- 장갑\n- 모자\n\n"
            "규칙:\n"
            "- 반드시 정확히 위 6개 단어 중 하나로만 출력\n"
            "- 다른 설명이나 문장은 절대 추가하지 마세요\n"
            "- 모르면 가장 관련성이 높은 것으로 추정하세요"
        )

        user_prompt = f"""
        상품 정보:
        - 상품명: {product['name']}
        - 카테고리: {product['category']}
        - 가격: {product['price']}원
        - 브랜드: {product['brand']}
        - 특징: {product['features']}
        """

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0,
        )

        result = response.choices[0].message.content.strip()
        logger.info(f"✅ 제품 분류 결과: {result}")
        return result

    except Exception as e:
        logger.error(f"❌ 제품 분류 실패: {e}")
        return None
