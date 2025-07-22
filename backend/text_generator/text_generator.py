import os
import torch
from dotenv import load_dotenv
from openai import OpenAI
from transformers import AutoTokenizer
from backend.models.model_handler import get_model_pipeline
from backend.text_generator.cleaner import clean_response
from backend.text_generator.prompt_builder import *
from backend.text_generator.prompt_builder_hf import system_instruction, css_friendly_prompt
from utils.logger import get_logger
from utils.config import get_openai_api_key

load_dotenv()
logger = get_logger(__name__)

# OpenAI
def generate_openai(product: dict) -> dict:
    """
    제공된 제품 정보를 바탕으로 OpenAI를 통해 상세페이지 HTML을 생성합니다.
    
    Args:
        product (dict): 상세페이지 생성에 필요한 제품 정보가 담긴 딕셔너리

    Returns:
        dict: 생성된 상세페이지 HTML이 포함된 딕셔너리
    """
    client = OpenAI(api_key=get_openai_api_key())
    
    prompt_parts = [
        apply_schema_prompt(product),
        natural_tone_prompt(),
        keyword_variation_prompt(),
        html_structure_prompt(),
        qna_format_prompt(),
        quantitative_prompt(),
        expert_quote_prompt(),
        storytelling_prompt(),
        modern_design_prompt(),
    ]

    # 차별점 반영
    if product.get("differences"):
        diff_prompt = "\n".join([
            "이 상품은 경쟁사 대비 다음과 같은 차별점을 가지고 있습니다:",
            *[f"- {item}" for item in product["differences"]],
            "위 차별점들을 상세페이지 내용에서 자연스럽게 강조해 주세요."
        ])
        prompt_parts.insert(1, diff_prompt)
        
    # 이미지 반영
    image_prompt_lines = []
    image_paths = product.get("image_path_list", [])

    if image_paths:
        image_prompt_lines = ["상세페이지 내에 다음 상품 이미지를 모두 포함시켜주세요:"]
        for path in image_paths:
            image_prompt_lines.append(f'- <img class="product-image" src="{path}" alt="...">')
        image_prompt_lines.append("각 이미지의 alt 속성은 제품명과 특징을 바탕으로 자동 생성해주세요")
        image_prompt_lines.append("각 이미지는 적절한 섹션에 분산하여 배치해주세요.")

    prompt_parts += image_prompt_lines
    prompt_parts.append("모든 정보를 HTML로 출력해주세요. 결과는 <html> ~ </html> 태그 안에 있어야 합니다")
    
    prompt = "\n".join(prompt_parts)
    logger.info("🛠️ OpenAI 요청 시작")

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9
        )
        logger.info("✅ OpenAI API 응답 수신 완료")
    except Exception as e:
        raise RuntimeError(f"❌ OpenAI API 요청 실패: {e}")

    html_text = response.choices[0].message.content
    html_text = clean_response(html_text)
    logger.info("✅ 코드 마크다운 블록 제거 완료")
    
    return {"html_text": html_text}


# HuggingFace
hf_model = None
hf_tokenizer = None

def load_hf_model():
    """
    HuggingFace 모델과 토크나이저를 로컬에서 로딩합니다.

    Returns:
        tuple: (pipeline 모델 객체, 토크나이저 객체)
    """
    model_id = "Markr-AI/Gukbap-Qwen2.5-7B"
    lora_path = "backend/models/adapter"
    model = get_model_pipeline(
                model_id=model_id,
                model_type="casual_lm",
                use_4bit=True,
                lora_path=lora_path,
                use_ip_adapter=False,
                save_dir="/home/spai0103/2025-GEO-Project/backend/models"
            )
    tokenizer = AutoTokenizer.from_pretrained(lora_path, use_fast=False, local_files_only=True)
    return model, tokenizer

def generate_hf(product: dict) -> dict:
    """
    제공된 제품 정보를 바탕으로 HuggingFace를 통해 상세페이지 HTML을 생성합니다.

    Args:
        product (dict): 상세페이지 생성에 필요한 제품 정보가 담긴 딕셔너리

    Returns:
        dict: 생성된 상세페이지 HTML이 포함된 딕셔너리
    """
    global hf_model, hf_tokenizer
    
    if hf_model is None:
        try:
            logger.info("🛠️ HuggingFace 모델 로딩 중")
            hf_model, hf_tokenizer = load_hf_model()
            logger.info("✅ 모델 로딩 완료")
        except Exception as e:
            raise RuntimeError(f"HuggingFace 모델 로딩 실패: {e}")
        
    prompt_parts = [
        system_instruction(product).strip(),
        css_friendly_prompt().strip(),
    ]
    
    # 차별점 반영
    if product.get("differences"):
        diff_prompt = "\n".join([
            "이 상품은 다음과 같은 차별점을 가지고 있습니다:",
            *[f"- {item}" for item in product["differences"]],
            "위 차별점들을 상세페이지 내용에서 자연스럽게 강조해 주세요."
        ])
        prompt_parts.insert(1, diff_prompt)
        
    # 이미지 반영
    image_prompt_lines = []
    image_paths = product.get("image_path_list", [])

    if image_paths:
        image_prompt_lines = ["상세페이지 내에 다음 상품 이미지를 모두 포함시켜주세요:"]
        for path in image_paths:
            image_prompt_lines.append(f'- <img class="product-image" src="{path}" alt="...">')
        image_prompt_lines.append("각 이미지의 alt 속성은 제품명과 특징을 바탕으로 자동 생성해주세요")
        image_prompt_lines.append("각 이미지는 적절한 섹션에 분산하여 배치해주세요.")

    prompt_parts += image_prompt_lines
    prompt_parts += [
        "모든 정보를 HTML로 출력해주세요. 결과는 <html> ~ </html> 태그 안에 있어야 합니다",
        "다음은 제품 상세페이지 HTML입니다.",
        "<!DOCTYPE html>"
    ]

    prompt = "\n".join(prompt_parts)

    logger.info("🛠️ HuggingFace 요청 시작")
    try:
        inputs = hf_tokenizer(prompt, return_tensors="pt", truncation=True)
        input_ids = inputs["input_ids"].to(hf_model.device)
        attention_mask = inputs["attention_mask"].to(hf_model.device)

        with torch.no_grad():
            output_ids = hf_model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                max_new_tokens=2048,
                do_sample=True,
                temperature=0.9,
                top_p=0.95,
                repetition_penalty=1.1
            )

        output_text = hf_tokenizer.decode(output_ids[0], skip_special_tokens=True)
        logger.info("✅ HuggingFace 상세페이지 생성 완료")
    except Exception as e:
        raise RuntimeError(f"HuggingFace 상세페이지 생성 실패: {e}")
    
    html_text = clean_response(output_text, strict=True)
    logger.info("✅ 코드 마크다운 블록 제거 완료")
    
    return {"html_text": html_text}