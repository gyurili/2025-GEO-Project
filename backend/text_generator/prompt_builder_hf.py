
# GEO 프롬프트
def system_instruction(product: dict) -> str:
    return f"""
당신은 상품 상세페이지 전문 작성가입니다. 아래 제품 정보를 바탕으로, 친절하고 설득력 있는 문체로 GEO 최적화된 상세페이지 HTML을 작성해주세요.

- 상품명: {product['name']}
- 카테고리: {product['category']}
- 브랜드: {product['brand']}
- 가격: {product['price']}원
- 특징: {product['features']}

작성 시 유의사항:
- 핵심 키워드는 반복하되 표현은 다양하게
- 정량적 수치 및 전문가 인용 포함
- Q&A 5개 이상 포함
- HTML 내 <script type="application/ld+json"> 블록 포함
"""

# 상세페이지 보완 프롬프트
def css_friendly_prompt() -> str:
    return """
HTML은 사전에 정의된 CSS 템플릿이 적용될 수 있도록 예측 가능한 구조로 작성해주세요.
inline 스타일은 사용하지 말고, 시맨틱 태그와 class명을 활용해 구조를 구분해주세요.

다음과 같은 class 기반 구조를 따라 작성해주세요:

- <div class="product-page">: 전체 상세페이지 컨테이너
- <h1 class="product-title">: 제품 제목
- <img class="product-image" src="..." alt="...">: 제품 착용 이미지
- <p class="product-summary">: 간단한 제품 요약 문장
- <ul class="product-features">: 제품 주요 특징 리스트
    - <li>단일 특징</li>
- <div class="product-section">: 각 주요 섹션 래퍼
    - <h2>소제목</h2>
    - <p>내용</p>
- <div class="product-faq">: Q&A 전체 영역
    - 각 질문/답변 쌍은 다음처럼 <div class="faq-item">으로 묶어주세요:
        - <div class="faq-item">
            <div class="question">Q. 질문 내용</div>
            <div class="answer">A. 답변 내용</div>
          </div>

이 구조를 반드시 지켜주세요. class명은 변경하지 말고, 각 항목을 정확히 감싸주세요.
인용하는 전문가의 말은 반드시 <blockquote> 태그로 감싸주세요.
강조할 키워드는 <strong> 태그로 감싸주세요.
"""
