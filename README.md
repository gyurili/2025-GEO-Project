# 2025-GEO-Project: GEOPage

---

![Demo]()

> **GEOPage**는 생성형 AI 기반으로 소상공인의 상품 상세페이지를 자동 생성하여 AI 검색(GEO)에 최적화된 마케팅 콘텐츠를 제공한다.

## 1. 📌 프로젝트 개요

---

**프로젝트명**: **GEOPage**

**핵심 아이디어**: 소상공인의 상품 정보를 기반으로 **AI 검색(GEO) 최적화 전략**을 적용한 상세페이지를 자동 생성하여 **AI 친화적 마케팅 콘텐츠**를 제공하는 플랫폼 개발

### **배경**

최근 온라인 검색 패러다임은 **SEO 중심에서 GEO(Generative Engine Optimization) 중심으로 변화**하고 있습니다.

- GPT, Perplexity 등 생성형 AI 검색 엔진의 보급으로, 기존의 **키워드 중심 검색(SEO)** 방식은 점차 약화되고 있습니다.
- AI 검색에서 제품이 노출되려면 **AI가 이해할 수 있는 구조적 콘텐츠**가 필요합니다. 그러나 대부분의 소상공인은 **이 변화를 따라가기 어려운 현실**에 직면해 있습니다.

### **목표**

- 소상공인이 **단순 입력(상품명, 키워드, 이미지)**만으로 **AI 검색에 최적화된 상세페이지**를 자동 생성할 수 있도록 지원
- 텍스트와 이미지를 동시에 생성해 **브랜드 아이덴티티와 마케팅 효과를 강화**
- **SEO + GEO 전략을 통합**해 AI 검색 시대에도 경쟁력 있는 온라인 스토어 구축 지원

### **기대 효과**

- **AI 친화적 콘텐츠 자동화**로 **소상공인의 마케팅 비용과 시간을 절감**
- **AI 검색 노출 강화**로 **유입 트래픽 증가 및 매출 성장**
- 디지털 격차 해소: 비전문가도 손쉽게 GEO 기반 상세페이지 제작 가능

### 기술스택

- **언어**: ![Python](https://img.shields.io/badge/Python-3776AB?style=plastic&logo=Python&logoColor=white)
![Jupyter Notebook](https://img.shields.io/badge/jupyter-%23FA0F00?style=plastic&logo=jupyter&logoColor=white)
- **프레임워크**: ![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=plastic&logo=Streamlit&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=plastic&logo=FastAPI&logoColor=white)
- **라이브러리**: ![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=plastic&logo=PyTorch&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=plastic&logo=OpenAI&logoColor=white)
![Hugging Face](https://img.shields.io/badge/Hugging%20Face-FFD21E?style=plastic&logo=HuggingFace&logoColor=black)
- **도구**: ![GitHub](https://img.shields.io/badge/GitHub-181717?style=plastic&logo=GitHub&logoColor=white)
![Notion](https://img.shields.io/badge/Notion-000000?style=plastic&logo=Notion&logoColor=white)
![Canva](https://img.shields.io/badge/Canva-00C4CC?style=plastic&logo=Canva&logoColor=white)
![Discord](https://img.shields.io/badge/Discord-%235865F2.svg?style=plastic&logo=discord&logoColor=white)

## 2. ⚙️ 설치 및 실행 방법

---

```bash
# 1. 가상환경 설치

# 2. 실행

```

## 3. 📂 프로젝트 구조

---

```arduino
geopage/
├── backend/                    # 백엔드 전체
│   ├── input_handler/          # 사용자 입력 및 전처리
│   ├── competitor_analysis/    # 경쟁사 데이터 수집 및 분석
│   ├── text_generator/         # 상세페이지 텍스트 생성
│   ├── image_generator/        # 제품 이미지 생성
│   ├── page_generator/         # 상세페이지 생성
│   ├── models/                 # 외부 AI 모델 호출
│   ├── data/                   # 입력 및 출력 데이터
│   └── main.py                 # FastAPI 진입점
├── frontend/                   # Streamlit UI
├── utils/                      # 공통 설정 및 유틸
├── .env                        # 환경 변수 파일
├── config.yaml                 # 설정 파일
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

- `backend`: 
- `frontend`: 

## 4. 👥 팀 소개: **GEO-GEO**

---

> GEO-GEO 팀은 AI 기반의 차세대 마케팅 솔루션 개발을 목표로, 텍스트 생성·이미지 생성·웹 서비스 개발 역량을 가진 팀원들이 모였습니다.
우리는 단순한 상세페이지 제작을 넘어, AI 검색에 친화적인 콘텐츠 전략을 실제 서비스로 구현합니다.

| 이학진 | 김민준 | 박규리 | 정영선 |
|:------:|:------:|:------:|:------:|
| <a href="https://github.com/kyakyak"><img src="https://github.com/kyakyak.png" width="100"/></a> | <a href="https://github.com/kmjune1535"><img src="https://github.com/kmjune1535.png" width="100"/></a> | <a href="https://github.com/gyurili"><img src="https://github.com/gyurili.png" width="100"/></a> | <a href="https://github.com/YS-2357"><img src="https://github.com/YS-2357.png" width="100"/></a> |
| 팀장 | 역할 | 역할 | 역할 |
| <a href="mailto:udosjdjdjdj@gmail.com"><img src="https://img.shields.io/badge/Gmail-D14836?style=plastic&logo=gmail&logoColor=white"/></a> | 메일 | <a href="mailto:inglifestora@naver.com"><img src="https://img.shields.io/badge/NaverMail-03C75A?style=plastic&logo=naver&logoColor=white"/></a> | <a href="mailto:joungyoungsun20@gmail.com"><img src="https://img.shields.io/badge/Gmail-D14836?style=plastic&logo=gmail&logoColor=white"/></a> | 

## 5. 📊 타임라인

---

| 날짜 | 주요 내용 | 담당자 | 상태 |
| :---: | :--- | :---: | :---: |
| 2025-06-30 | 프로젝트 시작 및 팀 구성 | 전원 | 완료 |
| 2025-07- |  |  | 진행중 |
| 2025-07- |  |  | 진행중 |
| 2025-07- |  |  | 진행중 |
| 2025-07- |  |  | 진행중 |
| 2025-07- |  |  | 진행중 |
| 2025-07- |  |  | 진행중 |
| 2025-07- |  |  | 진행중 |

## 6. 📎 참고 자료 및 산출물

---

- 📘 **최종 보고서**: 
- 📽️ **발표자료 (PPT)**: 
- 🗂️ **팀원별 협업 일지**
    - 이학진 협업일지:
    - 김민준 협업일지:
    - 박규리 협업일지:
    - 정영선 협업일지:

## 7. 📄 사용한 모델 및 라이센스

---

- **OpenAI GPT-4.1-mini**: OpenAI API 전용 (상업적 사용 가능, API 기반)
- **Markr-AI/Gukbap-Qwen2.5-7B**: CC BY-NC 4.0 (비상업적 사용만 허용)
- **SG161222/RealVisXL_V5.0**: OpenRAIL++ (상업적 사용 가능, 모델 사용 시 제한된 사용 정책 준수 필요)
- **h94/IP-Adapter**: Apache-2.0 (상업적 사용 가능, 라이선스 및 저작권 고지 필요)
- **Norod78/weird-fashion-show-outfits-sdxl-lora**: bespoke-lora-trained-license (상업적 이미지 생성 가능, 모델 자체 판매 불가, 크레딧 없이 사용 가능, 머지 공유 가능)