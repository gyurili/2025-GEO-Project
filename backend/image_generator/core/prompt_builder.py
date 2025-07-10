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
    - 브랜드: {product['brand']}
    - 가격: {product['price']}원
    - 특징: {product['features']}
    """


def generate_background_prompt(product: dict) -> str | None:
    """
    제품 정보를 바탕으로, 해당 제품에 어울리는 배경 생성용 영어 프롬프트를 생성합니다.
    예: "a wooden bathroom shelf with soft natural light, suitable for skincare product"
    """
    try:
        system_prompt = (
            "You are a background prompt designer for AI image generation.\n\n"
            "Given the following product description in Korean, write an English prompt that describes a **simple and minimal background scene** to visually complement the product.\n\n"
            "- Focus on a unified environment (e.g., 'a wooden kitchen table with warm morning light').\n"
            "- Do **not** include the product itself.\n"
            "- Avoid people, text, branding, or complex objects.\n"
            "- Use neutral tones, clean surfaces, and natural lighting.\n"
            "- Output should be one **concise** sentence, **under 30 words**."
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

def generate_negative_prompt(product: dict) -> str | None:
    """
    제품과 겹치지 않는 배경을 만들기 위해, 배제할 요소(negative prompt)를 영어로 생성합니다.
    """
    try:
        system_prompt = (
            "You are a visual prompt engineer. Based on the product description in Korean, "
            "list elements that should NOT appear in the background so that the product stands out. "
            "Output a comma-separated English list of visual elements to avoid, such as objects, textures, or colors. "
            "Do not include full sentences. Example: 'bottle, label, cream texture, hands, logo, skincare product'."
        )

        user_prompt = build_prompt(product)  # 기존 제품 요약 한국어 문자열

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

def generate_prompts(product: dict) -> dict:
    bg_prompt = generate_background_prompt(product)
    ng_prompt = generate_negative_prompt(product)
    return {"background_prompt": bg_prompt, "negative_prompt": ng_prompt}