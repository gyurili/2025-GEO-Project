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
            "Your job is to create an English background prompt that visually highlights a product, based on the product description in Korean.\n\n"
            "- The background should feel clean and realistic, suitable for the product's use case.\n"
            "- Avoid describing the product directly, but make sure the scene draws attention to the product's area.\n"
            "- Keep the language simple and avoid over-describing. Use 2–3 visual elements only.\n"
            "- Do not include people, logos, text, or abstract artistic details.\n"
            "- Output one sentence in English, under 15 words."
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
            "You are a prompt designer for AI image generation.\n\n"
            "Based on the product description in Korean, write an English prompt that shows a person naturally using the product, with their face not visible.\n\n"
            "- Focus on hands, arms, or body — no visible face.\n"
            "- Use relevant posture or action, e.g., 'a person putting on a sweater in front of a mirror, seen from behind'.\n"
            "- The prompt should highlight the product in use, while avoiding visual clutter.\n"
            "- Do not mention facial features, logos, text, or distractions.\n"
            "- Output one sentence in English, under 15 words."
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

        neg_prompt = response.choices[0].message.content.strip()
        logger.info(f"✅ 생성된 사람 프롬프트: {neg_prompt}")
        return neg_prompt

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