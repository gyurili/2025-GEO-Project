
# GEO 프롬프트
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
    return f"""
    사람과 대화하듯이 자연스러운 문체로, 친절하고 따뜻한 어투를 유지해주세요.
    각 문장을 명확하고 쉽게 이해되게 작성해주세요.
    """

def keyword_variation_prompt():
    return f"""
    핵심 키워드를 반복하되, 같은 단어를 반복하기보다는 동의어나 유사 표현을 사용해 다양하게 노출해주세요.
    문장 전체의 자연스러움을 해치지 않도록 주의해주세요."
    """
    
def html_structure_prompt():
    return f"""
    HTML은 H1~H3 계층 구조를 따르며, 핵심 단어에는 <strong>, <blockquote> 등의 태그를 활용해주세요.
    """

def qna_format_prompt():
    return f"""
    해당 상품에 대해 소비자들이 궁금해할 질문을 예상하고, 상세페이지 내용 중 일부는 Q&A 형식으로 작성해주세요.
    Q&A는 5개 이상 만들어주세요. 답변은 친절하고 구체적으로 작성하며, 불필요한 중복 없이 핵심 내용을 담아주세요."
    """

def quantitative_prompt():
    return f"""
    정량적 수치를 사용해 상품의 성능을 강조해주세요.
    상세페이지 곳곳에 긍정적이고 설득력 있는 통계 수치를 적절하게 추가해주세요.
    예를 들어 '30% 증가' 처럼 객관적인 수치를 말합니다."
    """

def expert_quote_prompt():
    return f"""
    실제 존재하는 전문가 또는 유명인의 말을 인용하여 상품의 신뢰성을 더해주세요. 
    인용문은 주제와 관련이 있어야 하고, 정보에 가치를 더해야 하며, 내용을 왜곡하거나 오해를 불러일으켜서는 안 됩니다.
    인용문은 신뢰할 수 있는 출처여야 하며, 소비자로 하여금 다른 상품들보다 더 좋다는 인상을 줄 수 있어야 합니다.
    """

def fluent_prompt():
    return f"""
    문장을 더 유창하게 써주세요. 각 문장이 자연스럽게 이어지도록 하고, 어휘 선택도 명확하고 풍부하게 해주세요.
    문장 구조는 너무 복잡하지 않게 하되, 읽는 이의 관심을 끌 수 있도록 유려하게 표현해주세요.
    """


# 상세페이지 보완 프롬프트
def expand_product_details():
    return f"""
    상품의 장점이 더 풍부하게 드러날 수 있도록, '상품 소개'에 기능적인 설명뿐만 아니라 실제 착용 시 장점, 타 제품과의 비교, 실생활에서의 활용 예시 등을 함께 포함해주세요.
    또한, 소비자의 감성을 자극할 수 있도록 계절감, 착용 상황, 감정적 효과(예: 시원함, 가벼움, 편안함 등)를 함께 묘사해주세요.
    구매를 유도할 수 있는 매력적인 문장이나 마무리 문구도 추가해 주세요.
    """
    
def css_friendly_prompt():
    return """
    HTML은 사전에 정의된 CSS 템플릿이 적용될 수 있도록 예측 가능한 구조로 작성해주세요.
    inline 스타일은 사용하지 말고, 시맨틱 태그와 class명을 활용해 구조를 구분해주세요.

    다음과 같은 class 기반 구조를 따라 작성해주세요:

    - <div class="product-page">: 전체 상세페이지 컨테이너
    - <h1 class="product-title">: 제품 제목
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
    """
