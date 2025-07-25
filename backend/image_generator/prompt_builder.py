from dotenv import load_dotenv
import os
import sys
from openai import OpenAI
from utils.logger import get_logger

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
logger = get_logger(__name__)

def build_prompt(product: dict) -> str:
    """상품 정보를 기반으로 기본 텍스트를 생성"""
    return f"""
    - 상품명: {product['name']}
    - 카테고리: {product['category']}
    - 가격: {product['price']}원
    - 브랜드: {product['brand']}
    - 특징: {product['features']}
    """

def generate_prompt(system_prompt: str, user_prompt: str, description: str) -> str | None:
    """
    GPT 기반 프롬프트 생성을 안전하게 실행 (예외 처리 공통화)
    """
    try:
        logger.debug(f"🛠️ {description} 생성 시작")
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
        )
        content = response.choices[0].message.content.strip()
        logger.info(f"✅ 생성된 {description}: {content}")
        return content

    except Exception as e:
        logger.error(f"❌ {description} 생성 실패: {e}")
        return None


def generate_background_prompt(product: dict) -> str | None:
    system_prompt = (
        "You are a prompt designer for AI image generation.\n\n"
        "Based on the product description in Korean, write an English prompt that shows a person naturally using the product.\n\n"
        "- The person can be fully visible (face allowed) but the product must be the main focus.\n"
        "- Make the scene realistic and relatable, like a lifestyle photo.\n"
        "- Avoid distractions: no unnecessary objects, no text overlays, no logos.\n"
        "- The background should complement the product, not overpower it.\n"
        "- Output one short sentence in English, under 15 words."
    )
    return generate_prompt(system_prompt, build_prompt(product), "배경 프롬프트")


def generate_human_prompt(product: dict) -> str | None:
    system_prompt = (
        "You are a prompt designer for AI image generation.\n\n"
        "Based on the product description in Korean, write an English prompt that shows a person naturally using the product.\n\n"
        "- The person can be fully visible (face allowed) but the product must be the main focus.\n"
        "- Make the scene realistic and relatable, like a lifestyle photo.\n"
        "- Avoid distractions: no unnecessary objects, no text overlays, no logos.\n"
        "- The background should complement the product, not overpower it.\n"
        "- Output one short sentence in English, under 15 words."
    )
    return generate_prompt(system_prompt, build_prompt(product), "사람 프롬프트")


def generate_negative_prompt(product: dict) -> str | None:
    system_prompt = (
        "You are a visual prompt engineer. Based on the product description in Korean, "
        "list visual elements that should NOT appear in the image so the product remains the main focus.\n"
        "- Exclude text, logos, busy patterns, excessive clutter, irrelevant objects, and flashy colors.\n"
        "- Do NOT exclude faces or people.\n"
        "- Output a comma-separated list of keywords only.\n"
        "- Example: text, logo, clutter, busy background, bright colors, excessive objects."
    )
    return generate_prompt(system_prompt, build_prompt(product), "네거티브 프롬프트")

def generate_prompts(product: dict, mode: str = "human") -> dict:
    try:
        if mode == "human":
            main_prompt = generate_human_prompt(product)
        else:
            main_prompt = generate_background_prompt(product)

        negative_prompt = generate_negative_prompt(product)

        return {
            "background_prompt": main_prompt or "",
            "negative_prompt": negative_prompt or "",
        }
    except Exception as e:
        logger.error(f"❌ 프롬프트 생성 전체 실패: {e}")
        return {"background_prompt": "", "negative_prompt": ""}
