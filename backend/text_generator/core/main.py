import os
import yaml
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

with open("config.yaml", "r", encoding="utf-8") as file:
    config = yaml.safe_load(file)

product = config["input"]


# GEO 프롬프트 함수
def apply_schema_prompt(product):
    return f"""
    당신은 상품 상세페이지 작성 전문가입니다.
    다음 상품 정보를 Schema.org 포맷을 참고해 구조화된 HTML로 작성해주세요:

    - 상품명: {product['name']}
    - 카테고리: {product['category']}
    - 브랜드: {product['brand']}
    - 가격: {product['price']}원
    - 특징: {product['features']}

    HTML에는 <script type="application/ld+json"> 블록도 포함해 주세요.
    aggregateRating는 높은 평점과 많은 리뷰수로 설정해주세요.
    """

def natural_tone_prompt():
    return "사람과 대화하듯이 자연스러운 문체로, 친절하고 따뜻한 어투를 유지해주세요."

def keyword_variation_prompt():
    return "핵심 키워드를 다양한 표현(동의어, 유사어 등)으로 반복 사용해주세요."

def html_structure_prompt():
    return "HTML은 H1~H3 계층 구조를 따르며, 주요 문장은 <strong>, <blockquote> 등을 활용해주세요."

def qna_format_prompt():
    return "해당 상품에 대해 소비자들이 궁금해할 질문을 예상하고, 상세페이지 내용 중 일부는 Q&A 형식으로 작성해주세요. Q&A는 5개 이상 만들어주세요."

def quantitative_prompt():
    return "정량적 통계, 수치를 사용해 제품의 성능을 강조해주세요."

def expert_quote_prompt():
    return "실제 존재하는 전문가 또는 유명인의 말을 인용하여 상품의 신뢰성을 더해주세요."


# 마크다운 코드블럭 제거
def clean_response(html_text: str) -> str:
    html_text = html_text.strip()

    if html_text.startswith("```html"):
        html_text = html_text.replace("```html", "", 1).strip()
    if html_text.endswith("```"):
        html_text = html_text.rsplit("```", 1)[0].strip()
    return html_text


# 최종 프롬프트 요청
def generate_html(product):
    prompt = "\n".join([
        apply_schema_prompt(product),
        natural_tone_prompt(),
        keyword_variation_prompt(),
        html_structure_prompt(),
        qna_format_prompt(),
        quantitative_prompt(),
        expert_quote_prompt(),
        "모든 정보를 HTML로 출력해주세요. 제공된 정보를 바탕으로 상세페이지를 풍성하게 만들어주세요. 결과는 <html> ~ </html> 태그 안에 있어야 합니다",
    ])

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6
    )

    html_text = response.choices[0].message.content
    html_text = clean_response(html_text)
    return {"html_text": html_text}


# 실행
if __name__ == "__main__":
    result = generate_html(product)

    output_path = config["data"]["output_path"]
    os.makedirs(output_path, exist_ok=True)
    with open(os.path.join(output_path, "result.html"), "w", encoding="utf-8") as f:
        f.write(result["html_text"])

    print("✅ GEO 최적화 HTML 생성 완료")
