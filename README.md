# 2025-GEO-Project: GEOPage

---

![Demo](assets/demo.gif)

> **GEOPage**는 생성형 AI 기반으로 소상공인의 상품 상세페이지를 자동 생성하여 AI 검색(GEO)에 최적화된 마케팅 콘텐츠를 제공하는 플랫폼입니다.

## 1. 📌 프로젝트 개요

---

**프로젝트명**: **GEOPage**

**핵심 아이디어**: 소상공인의 상품 정보를 기반으로 **AI 검색(GEO) 최적화 전략**을 적용한 상세페이지를 자동 생성하여 **AI 친화적 마케팅 콘텐츠**를 제공하는 플랫폼 개발

### **배경**

- 온라인 검색 패러다임은 **SEO(키워드 중심)에서 GEO(Generative Engine Optimization) 중심으로 변화**하고 있습니다.
- 기존 상세페이지는 이미지 중심으로 **AI 검색 노출에 불리한 구조**를 갖고 있습니다.
- AI 검색에서 제품이 노출되려면 **AI가 이해할 수 있는 구조적 콘텐츠**가 필요합니다. 그러나 대부분의 소상공인은 **이 변화를 따라가기 어려운 현실**에 직면해 있습니다.

### **목표**

- **단순 입력(상품명, 특징, 이미지**)만으로 **AI 검색에 최적화된 상세페이지**를 자동 생성할 수 있도록 지원합니다.
- 텍스트와 이미지를 동시에 생성해 **브랜드 아이덴티티와 마케팅 효과를 강화**합니다.
- **SEO + GEO 전략을 통합**해 AI 검색 시대에도 경쟁력 있는 온라인 스토어 구축을 지원합니다.

### **기대 효과**

- **AI 친화적 콘텐츠 자동화**로 **소상공인의 마케팅 비용과 시간을 절감**
- **AI 검색 노출 강화**로 **유입 트래픽 증가 및 매출 성장**
- **AI 친화형 콘텐츠 자동화**로 디지털 격차 해소

### 기술스택

- **언어**: ![Python](https://img.shields.io/badge/Python-3776AB?style=plastic&logo=Python&logoColor=white)
![Jupyter Notebook](https://img.shields.io/badge/jupyter-%23FA0F00?style=plastic&logo=jupyter&logoColor=white)
- **프레임워크**: ![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=plastic&logo=Streamlit&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=plastic&logo=FastAPI&logoColor=white)
![MySQL](https://img.shields.io/badge/mysql-4479A1.svg?style=plastic&logo=mysql&logoColor=white)
- **라이브러리**: ![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=plastic&logo=PyTorch&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=plastic&logo=OpenAI&logoColor=white)
![Hugging Face](https://img.shields.io/badge/Hugging%20Face-FFD21E?style=plastic&logo=HuggingFace&logoColor=black)
- **도구**: ![GitHub](https://img.shields.io/badge/GitHub-181717?style=plastic&logo=GitHub&logoColor=white)
![Notion](https://img.shields.io/badge/Notion-000000?style=plastic&logo=Notion&logoColor=white)
![Canva](https://img.shields.io/badge/Canva-00C4CC?style=plastic&logo=Canva&logoColor=white)
![Discord](https://img.shields.io/badge/Discord-%235865F2.svg?style=plastic&logo=discord&logoColor=white)

## 2. ⚙️ 설치 및 실행 방법

---

### 1) 시스템 의존성 및 패키지 설치

```bash
chmod +x setup.sh
./setup.sh
source .venv/bin/activate
```

---

### 2) 환경 변수 (.env)

`.env` 파일은 프로젝트 루트에 위치합니다.

```ini
OPENAI_API_KEY=YourOpenAIKey
GEMINI_API_KEY=YourGeminiKey
HF_TOKEN=YourHuggingfaceKey
DB_HOST=localhost   # 또는 고정 DB IP
DB_PASSWORD=your_password
```

`config.yaml`

```yaml
db_config:
  host: ""      # .env로 덮어씀
  user: GEOGEO
  password: ""  # .env로 덮어씀
  db: geo_db
```

---

### 3) MySQL 설정

**MySQL 설치:**

- Windows: [다운로드](https://dev.mysql.com/downloads/installer/)
- macOS: `brew install mysql`
- Ubuntu: `sudo apt install mysql-server`

**DB 및 테이블 생성:**

```sql
CREATE DATABASE geo_db DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'GEOGEO'@'%' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON geo_db.* TO 'GEOGEO'@'%';
FLUSH PRIVILEGES;
```

**테이블 구조:**

```sql
USE geo_db;
CREATE TABLE competitor_review_summary (
    category VARCHAR(100) PRIMARY KEY,
    review_summary TEXT,
    num_reviews INT,
    crawled_at DATETIME
);

CREATE TABLE crawl_request_signal (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category VARCHAR(100),
    status ENUM('pending', 'done') DEFAULT 'pending',
    requested_at DATETIME,
    completed_at DATETIME
);
```

> 포트 3306 외부 오픈 필요 (클라우드/GCP 방화벽 설정) 

---

### 4) 실행 순서

```bash
# [OS별 PYTHONPATH 설정]
# macOS/Linux
export PYTHONPATH=/2025-GEO-Project
# Windows
set PYTHONPATH=c:/2025-GEO-Project
```

**1. 크롤러(local_run.py) 실행 (VPN/프록시 적용 후)**

```bash
python backend/competitor_analysis/core/local_run.py
```

- 리뷰 크롤링 → 요약 → DB 저장 (백그라운드 실행 필요)

**2. 메인 애플리케이션 실행(run.py)**

```bash
python run.py
```

- competitor_main → DB에서 요약 조회 or 신호 등록 → local_run 반응

---

### 구조 요약 (단일 & 2대 이상 환경)

```css
[단일 서버]
MySQL ✅     
local_run.py ✅
Proxy/VPN 적용
run.py ✅
.env (DB 고정 IP)
```
또는
```css
[DB 서버]       [크롤링 서버(VPN)]
MySQL ✅        local_run.py ✅
run.py ✅       Proxy/VPN 적용
.env (DB 고정 IP)
```

> 핵심: 모든 장비는 DB에 접근 가능해야 함 (3306 포트 오픈)

## 3. 📂 프로젝트 구조

---

```arduino
geopage/
├── backend/                    # 백엔드 전체
│   ├── input_handler/          # 사용자 입력 처리 및 유효성 검증
│   ├── competitor_analysis/    # 경쟁사 리뷰 크롤링 및 요약
│   ├── image_generator/        # AI 기반 제품 이미지 생성 (SDXL + IP-Adapter)
│   ├── text_generator/         # GPT 기반 상세페이지 문구 생성
│   ├── page_generator/         # HTML 상세페이지 생성 및 이미지 변환
│   ├── routers/                # FastAPI 라우터 (모듈별 엔드포인트 관리)
│   ├── models/                 # 외부 AI 모델 로딩 및 추론 모듈
│   ├── data/                   # 입력/출력 데이터 저장 (input, output 디렉토리)
│   └── main.py                 # FastAPI 진입점
├── frontend/                   # Streamlit UI (상품 입력 → 결과 페이지 렌더링)
├── utils/                      # 공통 설정(config) 및 로거 유틸
├── run.py                      # 서버 실행 스크립트 (Frontend + Backend 통합 실행)
├── .env                        # 환경 변수 설정 (API 키 등)
├── config.yaml                 # 프로젝트 설정 (모델 경로, API 옵션)
├── setup.sh                    # 설치 자동화 스크립트
├── requirements.txt            # Python 패키지 목록
└── README.md                   # 프로젝트 설명 문서
```

## 4. 👥 팀 소개: **GEO-GEO**

---

> GEO-GEO 팀은 AI 기반의 차세대 마케팅 솔루션 개발을 목표로, 텍스트 생성·이미지 생성·웹 서비스 개발 역량을 가진 팀원들이 모였습니다.
단순한 상세페이지 제작을 넘어, AI 검색에 친화적인 콘텐츠 전략을 실제 서비스로 구현합니다.

| 이학진 | 김민준 | 박규리 | 정영선 |
|:------:|:------:|:------:|:------:|
| <a href="https://github.com/kyakyak"><img src="https://github.com/kyakyak.png" width="100"/></a> | <a href="https://github.com/kmjune1535"><img src="https://github.com/kmjune1535.png" width="100"/></a> | <a href="https://github.com/gyurili"><img src="https://github.com/gyurili.png" width="100"/></a> | <a href="https://github.com/YS-2357"><img src="https://github.com/YS-2357.png" width="100"/></a> |
| 팀장/ 경쟁분석/ DB 관리 | 프론트엔드/ 이미지 생성 | GEO 최적화/ 상세페이지 생성 | 이미지 생성/ 서버 관리 |
| <a href="mailto:udosjdjdjdj@gmail.com"><img src="https://img.shields.io/badge/Gmail-D14836?style=plastic&logo=gmail&logoColor=white"/></a> | <a href="mailto:kmjune1535@gmail.com"><img src="https://img.shields.io/badge/Gmail-D14836?style=plastic&logo=gmail&logoColor=white"/></a>  | <a href="mailto:inglifestora@naver.com"><img src="https://img.shields.io/badge/NaverMail-03C75A?style=plastic&logo=naver&logoColor=white"/></a> | <a href="mailto:joungyoungsun20@gmail.com"><img src="https://img.shields.io/badge/Gmail-D14836?style=plastic&logo=gmail&logoColor=white"/></a> | 

## 5. 📊 타임라인

---

| **날짜** | **주요 내용** | **담당자** | **상태** |
| --- | --- | --- | --- |
| **2025-06-30** | 프로젝트 시작 및 팀 구성 | 전원 | 완료 |
| **2025-07-01** | **요구사항 정의** 및 기술 스택 확정 | 전원 | 완료 |
| **2025-07-02** | **프로젝트 디렉토리 구조 설계** 및 초기 GitHub 세팅 | 전원 | 완료 |
| **2025-07-04** | **경쟁사 분석 모듈** (쿠팡 리뷰 크롤러 + DB 스키마 설계) 개발 | 이학진 | 완료 |
| **2025-07-06** | **프롬프트 생성기 설계** 및 OpenAI API 연동 테스트 | 박규리 | 완료 |
| **2025-07-08** | **이미지 생성 파이프라인** 초기 버전 구현 (SDXL + rembg) | 정영선 | 완료 |
| **2025-07-10** | **Streamlit UI 프로토타입** 구현 및 FastAPI 연동 | 김민준 | 완료 |
| **2025-07-12** | **상세페이지 자동 생성 로직** 완성 (GEO 최적화 프롬프트 적용) | 박규리 | 완료 |
| **2025-07-15** | **IP-Adapter + ControlNet 적용** 실험 및 이미지 품질 개선 | 정영선 | 완료 |
| **2025-07-22** | **UI 고도화 + 기능 통합** (프론트-백엔드 통합 테스트) | 김민준 | 완료 |
| **2025-07-25** | **최종 테스트 & GEO 성능 검증** | 전원 | 완료 |
| **2025-07-30** | **최종 보고서 및 README 정리 + 발표자료 제작** | 전원 | 완료 |
## 6. 📎 참고 자료 및 산출물

---

- 📘 **최종 보고서**: [다운로드](https://drive.google.com/file/d/1hW6I3pQv1s-bpWh30OJhhI47VSNig9Uv/view?usp=sharing)
- 📽️ **발표자료 (PPT)**: [확인하기](https://www.canva.com/design/DAGuCSTvzSM/Hbghlmvl8-dPgXEr2vlF3Q/edit?utm_content=DAGuCSTvzSM&utm_campaign=designshare&utm_medium=link2&utm_source=sharebutton)

- 🗂️ **팀원별 협업 일지**
    - [이학진 협업일지](https://www.notion.so/22500f54e76e809e865fef8ddaa73bcd?source=copy_link)
    - [김민준 협업일지](https://www.notion.so/1bb8e82988b280039641cff37cbdd44a?source=copy_link)
    - [박규리 협업일지](https://www.notion.so/1f1caf59f0188065bec3c9fefc30f7e3?source=copy_link)
    - [정영선 협업일지](https://sapphire-cart-f52.notion.site/22201c050cec81388f3ad4a7e1694e7d)

## 7. 📄 사용한 모델 및 라이센스

---

- **OpenAI GPT-4.1-mini**: OpenAI API 전용 (상업적 사용 가능, API 기반)
- **Gemini-2.0-flash-preview-image-generation**: Google AI API 전용 (상업적 사용 가능, 이미지 생성 특화)
- **Markr-AI/Gukbap-Qwen2.5-7B**: CC BY-NC 4.0 (비상업적 사용만 허용)
- **SG161222/RealVisXL_V5.0**: OpenRAIL++ (상업적 사용 가능, 모델 사용 시 제한된 사용 정책 준수 필요)
- **h94/IP-Adapter**: Apache-2.0 (상업적 사용 가능, 라이선스 및 저작권 고지 필요)
- **diffusers/stable-diffusion-xl-1.0-inpainting-0.1**: OpenRAIL++ (상업적 사용 가능, 모델 사용 시 제한된 사용 정책 준수 필요)
- **madebyollin/sdxl-vae-fp16-fix**: OpenRAIL++ (상업적 사용 가능, 모델 사용 시 제한된 사용 정책 준수 필요)
- **diffusers/controlnet-depth-sdxl-1.0**: OpenRAIL++ (상업적 사용 가능, 모델 사용 시 제한된 사용 정책 준수 필요)
- **lllyasviel/ControlNet**: OpenRAIL++ (상업적 사용 가능, 모델 사용 시 제한된 사용 정책 준수 필요)
- **Norod78/weird-fashion-show-outfits-sdxl-lora**: bespoke-lora-trained-license (상업적 이미지 생성 가능, 모델 자체 판매 불가, 크레딧 없이 사용 가능, 머지 공유 가능)
