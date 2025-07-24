
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
    
    반드시 다음 HTML 구조로 내용을 풍성하게 생성해주세요:

    ```html
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>[제품명] - [브랜드]</title>
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.4.0/css/all.min.css">
        <style>
            body {{ font-family: 'Noto Sans KR', sans-serif; }}
            .hero-bg {{ background: linear-gradient(120deg, #48c6ef 0%, #6f86d6 100%); }}
        </style>
    </head>
    <body class="bg-gray-50">
        <!-- Hero Section -->
        <section class="hero-bg pt-20 pb-16 text-white">
            <!-- 임팩트 있는 헤드라인 -->
        </section>

        <!-- Problem Section -->
        <section class="py-16 bg-white">
            <!-- 고객 문제점 3가지 -->
        </section>

        <!-- 나머지 섹션들... -->
    </body>
    </html>
    ```
    """

def natural_tone_prompt():
    return f"""
    광고 문구처럼 과장되거나 번역체가 느껴지지 않도록, 자연스럽고 일상적인 한국어 문장을 사용해주세요.
    마치 친한 친구나 지인이 설명해주는 것처럼 부드럽고 편안한 어조로 작성해주세요.
    자연스럽고 공감가는 말투를 사용하되, 상품의 장점은 명확하게 전달해주세요.
    """

def keyword_variation_prompt():
    return f"""
    핵심 키워드를 반복하되, 같은 단어를 반복하기보다는 동의어나 유사 표현을 사용해 다양하게 노출해주세요.
    문장 전체의 자연스러움을 해치지 않도록 주의해주세요."
    """

def html_structure_prompt():
    return f"""
    HTML은 heading 태그의 계층 구조를 따르며, 핵심 단어에는 <strong>, <blockquote> 등의 태그를 활용해주세요.
    """

def qna_format_prompt():
    return f"""
    해당 상품에 대해 소비자들이 궁금해할 질문을 예상하고, 상세페이지 내용 중 일부는 Q&A 형식으로 작성해주세요.
    Q&A는 5개 이상 만들어주세요. FontAwesome 아이콘을 사용하세요.
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
    인용문은 주제와 관련이 있어야 하고, 정보에 가치를 더해야 합니다.
    """


# 상세페이지 보완 프롬프트
def storytelling_prompt():
    return """
    도널드밀러의 스토리텔링 기법을 사용해서 반드시 다음 구조를 따라주세요:
    
    1. Hero Section (브랜드명, 임팩트 있는 헤드라인)
    
    2. Problem Section (고객의 고민/문제점 3가지)
        - "이런 경험 있으신가요?"로 감정적 어필
        - 고객이 겪는 문제 상황 3가지 제시
        - 각 문제에 대한 감정적 공감과 이해
        - 우리 제품이 제공하는 명확한 해결책
        - 각 문제 상황은 3개의 열로 나열
    
    3. Guide Section (브랜드가 이해한다는 공감 + 약속)
        - 전체 레이아웃은 2단 그리드로 구성: 왼쪽은 텍스트, 오른쪽은 제품 이미지
        - 왼쪽 텍스트 블록에는 다음 구성 요소를 포함
            1) 고객의 문제를 공감하고 브랜드가 해결책을 찾았음을 선언하는 임팩트 있는 검정색 헤드라인 (예: "{브랜드명}이 해결책을 드립니다")
            2) 브랜드의 가치와 철학을 설명하는 본문 2~3문단
            3) 고객이 신뢰할 수 있는 강점을 강조한 포인트박스 2개, 각각은 다음 스타일을 포함할 것:
               - `bg-blue-50`, `border-l-4`, `border-blue-600`, `p-6`, `rounded-lg`, `shadow-lg`
               - 상단엔 소제목 `<h3 class="text-xl font-semibold mb-2 text-blue-700">`, 아래엔 본문 `<p>` 포함
        - 오른쪽에는 제품 이미지 1장을 포함 (`rounded-xl`, `shadow-xl`, `mx-auto`, `max-w-sm` 등으로 스타일 지정)
    
    4. Product Section (제품 특징)
        - 리스트 전체는 <ul class="grid md:grid-cols-3 gap-10 max-w-6xl mx-auto text-gray-800">로 감싸고, 각 항목은 <li class="bg-white p-6 rounded-xl shadow-lg">로 구성
        - 특징 이름(소제목)은 <blockquote class="text-xl font-semibold mb-3 text-blue-700"> 형식으로 강조, 설명은 그 아래 <p> 태그로 자연스럽게 이어서 작성
    
    5. Plan Section (선택-주문-배송의 간단한 3단계 프로세스)
        - 각 단계는 FontAwesome 아이콘을 사용하여 시각적으로 표현
        - 아이콘 색은 text-blue-600색으로 구성
    
    6. Success/Failure Section (선택했을 때 vs 선택하지 않았을 때)
        - 성공 시나리오와 실패 시나리오를 대비하여 작성
        - 선택했을 때: <i class="fas fa-check text-green-600 mr-2"></i>
        - 선택하지 않았을 때: <i class="fas fa-times text-red-600 mr-2"></i>
    
    7. Reviews Section (고객 후기 4개)
        - 총 4개의 고객 후기를 2x2 형태로 배치
        - <div class="grid md:grid-cols-2 gap-10">를 사용해 2열 그리드로 구성
        - 각 후기는 <div class="bg-sky-50 p-6 rounded-xl shadow-lg text-left"> 형식의 카드 스타일로 작성
        - 고객 이름과 직업은 <p class="font-semibold text-blue-700">로 표시
        - <i class="fas fa-star text-yellow-400 mr-1"></i> 아이콘을 반복 사용하여 별 5개를 표현
    """

def modern_design_prompt():
    return """
    반드시 다음 디자인 요소들을 포함해주세요:

    1. Tailwind CSS 사용: 
       - <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
       - 모든 스타일링은 Tailwind 클래스 사용
       - italic은 사용 금지

    2. FontAwesome 아이콘:
       - '고객의 고민 3가지', '고객 후기' 파트에만 아이콘 사용 금지
       - 반드시 실제 존재하는 아이콘만 사용해야 하며, 의미가 유사하더라도 존재하지 않으면 사용 금지
       - 예를 들어 `fa-fabric`, `fa-textile`, `fa-material` 같은 이름은 실제로 존재하지 않으므로 사용 금지
       - h1, h2 제목 태그에만 FontAwesome 아이콘 사용 금지
       - 각 섹션에만 유치하지 않은 적절한 아이콘 사용
       - 폰트는 Noto Sans KR만 사용

    3. 카드 스타일:
       - 그림자: shadow-lg, shadow-xl
       - 둥근 모서리: rounded-xl, rounded-lg
       - 배경색 조합: bg-white, bg-sky-50, bg-blue-50

    4. 반응형 그리드:
       - grid md:grid-cols-2, grid md:grid-cols-3 사용
       
    5. 레이아웃:
       - 풀스크린 Hero 섹션
       - 전체 섹션은 반드시 동일한 max-w-6xl 너비 사용
       - 섹션별 충분한 여백 (py-20 이상)
       
    6. <li> 디자인:
        - <li> 태그는 list 스타일을 제거하고, 점 기호(불릿)가 보이지 않도록 처리
        
    7. Hero Section 디자인:
        - 다음 네 가지 요소를 반드시 포함
            1) 브랜드 또는 제품을 강조하는 임팩트 있는 헤드라인 문장
            2) 제품의 장점을 요약한 키워드 3~4개를 버튼 또는 배지 스타일로 표시 (<span class="bg-white bg-opacity-20 rounded-full py-1.5 px-4 text-sm font-semibold tracking-wide">)
            3) 1~2줄 분량의 제품 소개 문장 (무엇을 위한 제품인지, 어떤 특징이 핵심인지 간략히 설명)
            4) 제품 대표 이미지 1장 (`max-w-md`, `rounded-xl`, `shadow-xl`, `mx-auto`)
        - 전체 콘텐츠는 가운데 정렬 (`text-center`, `items-center`)
        - .hero-bg {{ background: linear-gradient(120deg, #48c6ef 0%, #6f86d6 100%); }} 준수

    8. CTA(Call-To-Action) 버튼은 생성 금지
    """