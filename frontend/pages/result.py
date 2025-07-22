import streamlit as st
import os
import sys
from typing import Dict, Any, Optional
from pathlib import Path
import json
import zipfile
import tempfile
from datetime import datetime

# 로거 임포트 추가
sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.logger import get_logger

# 로거 설정
logger = get_logger(__name__)

def load_result_data() -> Optional[Dict[str, Any]]:
    """결과 데이터 로드"""
    logger.debug("🛠️ 결과 데이터 로드 시작")
    
    # 세션에서 합성 결과 확인
    if 'composition_result' in st.session_state:
        result = st.session_state.composition_result
        logger.debug(f"🛠️ 세션에서 결과 로드: {result.keys()}")
        return result
    
    logger.warning("⚠️ 결과 데이터가 없음")
    return None

def display_result_summary(result_data: Dict[str, Any]):
    """결과 요약 정보 표시"""
    logger.debug("🛠️ 결과 요약 표시 시작")
    
    st.subheader("📊 생성 결과 요약")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="생성 타입",
            value=result_data.get('generation_type', 'N/A').title()
        )
    
    with col2:
        st.metric(
            label="입력 이미지 수",
            value=f"{result_data.get('input_images', 0)}개"
        )
    
    with col3:
        st.metric(
            label="상품 이미지 수",
            value=f"{result_data.get('product_images_count', 1)}개"
        )
    
    with col4:
        generation_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        st.metric(
            label="생성 시간",
            value=generation_time
        )

def display_result_image(result_data: Dict[str, Any]):
    """결과 이미지 표시"""
    logger.debug("🛠️ 결과 이미지 표시 시작")
    
    # image_path = result_data.get('result_image_path')
    image_path = r'/home/ubuntu/2025-GEO-Project/backend/data/result/page_20250721_132933_074.png'
    if not image_path:
        st.error("❌ 결과 이미지 경로가 없습니다.")
        return None
    
    # 프로젝트 루트 기준 절대 경로 생성
    project_root = Path(__file__).parent.parent.parent
    full_image_path = project_root / image_path
    
    logger.debug(f"🛠️ 이미지 경로: {full_image_path}")
    
    if full_image_path.exists():
        st.subheader("🎨 생성된 이미지")
        
        # 이미지를 전체 너비로 크게 표시 (수정된 부분)
        st.image(
            str(full_image_path), 
            caption="생성된 합성 이미지",
            use_container_width=True  # use_column_width → use_container_width로 변경
        )
        
        logger.info("✅ 결과 이미지 표시 완료")
        return full_image_path
    else:
        st.error(f"❌ 이미지 파일을 찾을 수 없습니다: {image_path}")
        logger.error(f"❌ 이미지 파일 없음: {full_image_path}")
        return None

def display_result_html(html_path: str = None):
    """결과 HTML 표시"""
    logger.debug("🛠️ 결과 HTML 표시 시작")
    
    if not html_path:
        st.info("💡 HTML 결과물이 준비되면 여기에 표시됩니다.")
        return None
    
    # 프로젝트 루트 기준 절대 경로 생성
    project_root = Path(__file__).parent.parent.parent
    full_html_path = project_root / html_path
    
    logger.debug(f"🛠️ HTML 경로: {full_html_path}")
    
    if full_html_path.exists():
        st.subheader("📄 생성된 HTML")
        
        try:
            # HTML 파일 읽기
            with open(full_html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # HTML 미리보기 (iframe 또는 코드 블록)
            with st.expander("🔍 HTML 미리보기", expanded=True):
                # HTML을 iframe으로 표시
                st.components.v1.html(html_content, height=600, scrolling=True)
            
            # HTML 코드 보기
            with st.expander("📝 HTML 코드 보기"):
                st.code(html_content, language='html')
            
            logger.info("✅ 결과 HTML 표시 완료")
            return full_html_path
            
        except Exception as e:
            st.error(f"❌ HTML 파일 읽기 실패: {e}")
            logger.error(f"❌ HTML 파일 읽기 실패: {e}")
            return None
    else:
        st.warning(f"⚠️ HTML 파일을 찾을 수 없습니다: {html_path}")
        logger.warning(f"⚠️ HTML 파일 없음: {full_html_path}")
        return None

def create_download_package(image_path: Path, html_path: Path = None, result_data: Dict[str, Any] = None) -> Optional[str]:
    """다운로드용 패키지 생성 (ZIP 파일)"""
    logger.debug("🛠️ 다운로드 패키지 생성 시작")
    
    try:
        # 임시 ZIP 파일 생성
        temp_dir = tempfile.gettempdir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"geopage_result_{timestamp}.zip"
        zip_path = os.path.join(temp_dir, zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 이미지 파일 추가
            if image_path and image_path.exists():
                zipf.write(image_path, f"image/{image_path.name}")
                logger.debug(f"🛠️ 이미지 파일 추가: {image_path.name}")
            
            # HTML 파일 추가 (있는 경우)
            if html_path and html_path.exists():
                zipf.write(html_path, f"html/{html_path.name}")
                logger.debug(f"🛠️ HTML 파일 추가: {html_path.name}")
            
            # 메타데이터 JSON 추가
            if result_data:
                metadata = {
                    "generation_info": {
                        "type": result_data.get('generation_type'),
                        "input_images": result_data.get('input_images'),
                        "product_images_count": result_data.get('product_images_count'),
                        "prompt_used": result_data.get('prompt_used'),
                        "generation_time": datetime.now().isoformat()
                    },
                    "files": {
                        "image": f"image/{image_path.name}" if image_path else None,
                        "html": f"html/{html_path.name}" if html_path else None
                    }
                }
                
                metadata_json = json.dumps(metadata, ensure_ascii=False, indent=2)
                zipf.writestr("metadata.json", metadata_json)
                logger.debug("🛠️ 메타데이터 JSON 추가")
            
            # README 파일 추가
            readme_content = """# GeoPage 생성 결과물

이 패키지에는 다음 파일들이 포함되어 있습니다:

## 📁 폴더 구조
- `image/` - 생성된 합성 이미지
- `html/` - 생성된 HTML 상세페이지 (있는 경우)
- `metadata.json` - 생성 정보 메타데이터
- `README.md` - 이 파일

## 📝 사용 방법
1. `image/` 폴더의 이미지를 확인하세요
2. `html/` 폴더의 HTML 파일을 브라우저에서 열어보세요
3. `metadata.json`에서 생성 과정의 상세 정보를 확인할 수 있습니다

## 🔧 생성 정보
생성 시간: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """
생성 도구: GeoPage AI Image Composer
"""
            zipf.writestr("README.md", readme_content)
            logger.debug("🛠️ README 파일 추가")
        
        logger.info(f"✅ 다운로드 패키지 생성 완료: {zip_path}")
        return zip_path
        
    except Exception as e:
        logger.error(f"❌ 다운로드 패키지 생성 실패: {e}")
        return None

def display_download_section(image_path: Path, html_path: Path = None, result_data: Dict[str, Any] = None):
    """다운로드 섹션 표시"""
    logger.debug("🛠️ 다운로드 섹션 표시 시작")
    
    st.subheader("📥 결과물 다운로드")
    
    col1, col2, col3 = st.columns(3)
    
    # 개별 파일 다운로드
    with col1:
        if image_path and image_path.exists():
            with open(image_path, "rb") as file:
                st.download_button(
                    label="🖼️ 이미지 다운로드",
                    data=file.read(),
                    file_name=image_path.name,
                    mime="image/png",
                    use_container_width=True
                )
        else:
            st.button("🖼️ 이미지 다운로드", disabled=True, use_container_width=True)
    
    with col2:
        if html_path and html_path.exists():
            with open(html_path, "rb") as file:
                st.download_button(
                    label="📄 HTML 다운로드",
                    data=file.read(),
                    file_name=html_path.name,
                    mime="text/html",
                    use_container_width=True
                )
        else:
            st.button("📄 HTML 다운로드", disabled=True, use_container_width=True)

def display_generation_details(result_data: Dict[str, Any]):
    """생성 상세 정보 표시"""
    logger.debug("🛠️ 생성 상세 정보 표시 시작")
    
    with st.expander("🔍 생성 상세 정보", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**생성 설정:**")
            st.write(f"- 생성 타입: {result_data.get('generation_type', 'N/A')}")
            st.write(f"- 입력 이미지 수: {result_data.get('input_images', 0)}개")
            st.write(f"- 상품 이미지 수: {result_data.get('product_images_count', 1)}개")
        
        with col2:
            st.write("**기술 정보:**")
            st.write("- AI 모델: Gemini 2.0 Flash")
            st.write("- 프롬프트 변환: GPT-4o-mini")
            st.write("- 이미지 형식: PNG")
        
        # 사용된 프롬프트 표시
        if result_data.get('prompt_used'):
            st.write("**사용된 프롬프트:**")
            st.code(result_data['prompt_used'], language='text')

def main():
    """결과 페이지 메인"""
    logger.debug("🛠️ 결과 페이지 시작")
    
    st.set_page_config(
        page_title="생성 결과",
        page_icon="🎉",
        layout="wide"
    )
    
    st.title("🎉 생성 결과")
    st.markdown("---")
    
    # 결과 데이터 로드
    result_data = load_result_data()
    
    if not result_data:
        st.error("❌ 표시할 결과가 없습니다.")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🔙 이미지 합성 페이지로 돌아가기", use_container_width=True):
                st.switch_page("pages/image_compose.py")
        
        return
    
    # 결과 요약 표시
    display_result_summary(result_data)
    
    st.markdown("---")
    
    # 결과 이미지 표시 (전체 너비)
    image_path = display_result_image(result_data)
    
    # 결과 HTML 표시 (미래 기능)
    html_path = result_data.get('result_html_path')
    if html_path:
        display_result_html(html_path)
    
    st.markdown("---")
    
    # 메인 정보 섹션 (이미지 아래로 이동)
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # 다운로드 섹션 (이미지 아래로 이동)
        html_path_obj = None
        if html_path:
            project_root = Path(__file__).parent.parent.parent
            html_path_obj = project_root / html_path
        
        display_download_section(image_path, html_path_obj, result_data)
    
    with col2:
        # 상품 정보 표시
        if 'product_data' in st.session_state:
            product_data = st.session_state.product_data
            st.subheader("📦 상품 정보")
            st.write(f"**상품명:** {product_data.get('name', 'N/A')}")
            st.write(f"**브랜드:** {product_data.get('brand', 'N/A')}")
            st.write(f"**카테고리:** {product_data.get('category', 'N/A')}")
            st.write(f"**가격:** {product_data.get('price', 0):,}원")
            st.write(f"**특징:** {product_data.get('features', 'N/A')}")
    
    st.markdown("---")
    
    # 생성 상세 정보
    display_generation_details(result_data)
    
    # 네비게이션 버튼
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("🔙 이미지 합성 페이지", use_container_width=True):
            st.switch_page("pages/image_compose.py")
    
    with col2:
        if st.button("🏠 상품 입력 페이지", use_container_width=True):
            st.switch_page("home.py")
    
    with col3:
        if st.button("🔄 새로 시작하기", use_container_width=True):
            # 세션 상태 초기화
            keys_to_clear = [
                'processed_data', 'composition_result', 'composition_data',
                'selected_user_images_model', 'selected_user_images_background',
                'selected_model_image', 'selected_mask_image', 'selected_background'
            ]
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            
            logger.info("✅ 세션 상태 초기화 완료")
            st.switch_page("home.py")

if __name__ == "__main__":
    main()