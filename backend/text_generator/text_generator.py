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
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
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

    if product.get("differences"):
        diff_prompt = "\n".join([
            "이 상품은 경쟁사 대비 다음과 같은 차별점을 가지고 있습니다:",
            *[f"- {item}" for item in product["differences"]],
            "위 차별점들을 상세페이지 내용에서 자연스럽게 강조해 주세요."
        ])
        prompt_parts.insert(1, diff_prompt)
    
    prompt_parts += [
        "상세페이지 내에 상품 이미지를 포함시켜주세요.",
        f'상품 이미지는 product["vton_image_path"] 경로에 있습니다.'
        f'따라서 태그는 다음 형식을 지켜주세요. <img class="product-image" src="{product["vton_image_path"]}" alt=" ">',
        "alt 속성은 제품명과 특징을 바탕으로 자동 생성해주세요.",
        "모든 정보를 HTML로 출력해주세요. 결과는 <html> ~ </html> 태그 안에 있어야 합니다"
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


# HuggingFace
hf_model = None
hf_tokenizer = None

def load_hf_model():
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
    global hf_model, hf_tokenizer
    
    if hf_model is None:
        logger.info("🛠️ HuggingFace 모델 로딩 중")
        hf_model, hf_tokenizer = load_hf_model()
        
    prompt_parts = [
        system_instruction(product).strip(),
        css_friendly_prompt().strip(),
        "다음은 제품 상세페이지 HTML입니다.",
        f'이미지 태그는 다음 형식을 지켜주세요. <img class="product-image" src="{product["vton_image_path"]}" alt=" ">',
        "alt 속성은 제품명과 특징을 바탕으로 자동 생성해주세요.",
        "<!DOCTYPE html>"
    ]
    
    if product.get("differences"):
        diff_prompt = "\n".join([
            "이 상품은 다음과 같은 차별점을 가지고 있습니다:",
            *[f"- {item}" for item in product["differences"]],
            "위 차별점들을 상세페이지 내용에서 자연스럽게 강조해 주세요."
        ])
        prompt_parts.insert(1, diff_prompt)

    prompt = "\n".join(prompt_parts)

    logger.info("🛠️ HuggingFace 요청 시작")
    inputs = hf_tokenizer(prompt, return_tensors="pt")
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
    logger.info("✅ HuggingFace 응답 수신 완료")
    html_text = clean_response(output_text, strict=True)
    logger.info("✅ 코드 마크다운 블록 제거 완료")
    
    return {"html_text": html_text}