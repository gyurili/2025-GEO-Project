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

def get_user_session_key(base_key: str) -> str:
    """사용자별 세션 키 생성"""
    user_id = st.session_state.get('user_session_id', 'default')
    return f"{base_key}_{user_id}"

def load_result_data() -> Optional[Dict[str, Any]]:
    """결과 데이터 로드 (사용자별)"""
    logger.debug("🛠️ 결과 데이터 로드 시작")
    
    # 사용자별 세션에서 상세페이지 생성 결과 확인
    detail_result_key = get_user_session_key('detail_page_result')
    if detail_result_key in st.session_state:
        result = st.session_state[detail_result_key]
        logger.debug(f"🛠️ 사용자별 세션에서 상세페이지 결과 로드: {result.keys() if result else 'None'}")
        return result
    
    # 백업: 전역 세션 확인
    if 'detail_page_result' in st.session_state:
        result = st.session_state.detail_page_result
        logger.debug(f"🛠️ 전역 세션에서 상세페이지 결과 로드: {result.keys() if result else 'None'}")
        return result
    
    # 백업: 합성 결과도 확인 (사용자별)
    composition_result_key = get_user_session_key('composition_result')
    if composition_result_key in st.session_state:
        result = st.session_state[composition_result_key]
        logger.debug(f"🛠️ 사용자별 세션에서 합성 결과 로드: {result.keys() if result else 'None'}")
        return result
    
    logger.warning("⚠️ 결과 데이터가 없음")
    return None

def display_result_image(result_data: Dict[str, Any]):
    """결과 이미지 표시"""
    logger.debug("🛠️ 결과 이미지 표시 시작")
    
    # session_id 기반으로 이미지 경로 생성
    session_id = result_data.get('session_id')
    if session_id:
        # 상세페이지 생성 결과 이미지 (PNG)
        image_filename = f"page_{session_id}.png"
        image_path = f"backend/data/result/{image_filename}"
        logger.debug(f"🛠️ session_id 기반 이미지 경로: {image_path}")
    else:
        # 백업: 기존 방식 (합성 결과)
        image_path = result_data.get('result_image_path')
        logger.debug(f"🛠️ 기존 방식 이미지 경로: {image_path}")
    
    if not image_path:
        st.error("❌ 결과 이미지 경로가 없습니다.")
        return None
    
    # 프로젝트 루트 기준 절대 경로 생성
    project_root = Path(__file__).parent.parent.parent
    full_image_path = project_root / image_path
    
    logger.debug(f"🛠️ 이미지 절대 경로: {full_image_path}")
    
    if full_image_path.exists():
        st.subheader("🎨 생성된 상세페이지 이미지")
        
        # 이미지를 전체 너비로 크게 표시
        st.image(
            str(full_image_path), 
            caption="생성된 상세페이지 이미지",
            use_container_width=True
        )
        
        logger.info("✅ 결과 이미지 표시 완료")
        return full_image_path
    else:
        st.error(f"❌ 이미지 파일을 찾을 수 없습니다: {image_path}")
        logger.error(f"❌ 이미지 파일 없음: {full_image_path}")
        return None

def display_result_html(result_data: Dict[str, Any]):
    """결과 HTML 표시"""
    logger.debug("🛠️ 결과 HTML 표시 시작")
    
    # session_id 기반으로 HTML 경로 생성
    session_id = result_data.get('session_id')
    if session_id:
        html_filename = f"page_{session_id}.html"
        html_path = f"backend/data/result/{html_filename}"
        logger.debug(f"🛠️ session_id 기반 HTML 경로: {html_path}")
    else:
        st.info("💡 HTML 결과물이 준비되면 여기에 표시됩니다.")
        return None
    
    # 프로젝트 루트 기준 절대 경로 생성
    project_root = Path(__file__).parent.parent.parent
    full_html_path = project_root / html_path
    
    logger.debug(f"🛠️ HTML 절대 경로: {full_html_path}")
    
    if full_html_path.exists():
        st.subheader("📄 생성된 상세페이지 HTML")
        
        try:
            # HTML 파일 읽기
            with open(full_html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # 이미지 경로를 base64로 변환하여 embedded 방식으로 변경
            import re
            import base64
            
            def replace_image_with_base64(match):
                src = match.group(1)
                try:
                    # 상대 경로를 절대 경로로 변환
                    if src.startswith('../'):
                        image_path = project_root / "backend" / "data" / src.replace('../', '')
                    elif src.startswith('file://'):
                        image_path = Path(src.replace('file://', ''))
                    else:
                        image_path = project_root / src
                    
                    if image_path.exists():
                        # 이미지를 base64로 인코딩
                        with open(image_path, 'rb') as img_file:
                            img_data = img_file.read()
                            img_base64 = base64.b64encode(img_data).decode('utf-8')
                            
                        # 파일 확장자에 따른 MIME 타입 결정
                        ext = image_path.suffix.lower()
                        if ext in ['.jpg', '.jpeg']:
                            mime_type = 'image/jpeg'
                        elif ext == '.png':
                            mime_type = 'image/png'
                        elif ext == '.webp':
                            mime_type = 'image/webp'
                        else:
                            mime_type = 'image/png'  # 기본값
                        
                        return f'src="data:{mime_type};base64,{img_base64}"'
                    else:
                        logger.warning(f"⚠️ 이미지 파일을 찾을 수 없음: {image_path}")
                        return f'src=""'  # 빈 src
                        
                except Exception as e:
                    logger.error(f"❌ 이미지 처리 실패: {e}")
                    return f'src=""'  # 빈 src
            
            # HTML 내의 이미지 src 속성을 base64로 변경
            preview_html = re.sub(r'src="([^"]*)"', replace_image_with_base64, html_content)
            
            # HTML 미리보기
            with st.expander("🔍 HTML 미리보기", expanded=True):
                st.components.v1.html(preview_html, height=600, scrolling=True)
            
            # 원본 HTML 코드 보기 (상대 경로 유지)
            with st.expander("📝 HTML 코드 보기"):
                st.code(html_content, language='html')
                st.info("💡 다운로드한 HTML 파일은 브라우저에서 정상적으로 이미지가 표시됩니다.")
            
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
            # 메인 결과 이미지 추가
            if image_path and image_path.exists():
                zipf.write(image_path, f"images/{image_path.name}")
                logger.debug(f"🛠️ 메인 이미지 파일 추가: {image_path.name}")
            
            # HTML 파일과 관련 이미지들 처리
            if html_path and html_path.exists():
                # HTML 파일 읽기
                with open(html_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                # HTML 내 이미지 경로 추출 및 변경
                import re
                project_root = Path(__file__).parent.parent.parent
                
                def process_image_for_download(match):
                    src = match.group(1)
                    try:
                        # 현재 이미지 경로를 절대 경로로 변환
                        if src.startswith('../'):
                            source_path = project_root / "backend" / "data" / src.replace('../', '')
                        elif src.startswith('file://'):
                            source_path = Path(src.replace('file://', ''))
                        elif src.startswith('backend/data/'):
                            source_path = project_root / src
                        else:
                            source_path = project_root / src
                        
                        if source_path.exists():
                            # 이미지를 ZIP에 추가
                            image_filename = source_path.name
                            zipf.write(source_path, f"images/{image_filename}")
                            logger.debug(f"🛠️ HTML 관련 이미지 추가: {image_filename}")
                            
                            # 상대 경로로 변경 (./images/filename.ext)
                            return f'src="./images/{image_filename}"'
                        else:
                            logger.warning(f"⚠️ 이미지 파일을 찾을 수 없음: {source_path}")
                            return f'src="{src}"'  # 원본 유지
                            
                    except Exception as e:
                        logger.error(f"❌ 이미지 처리 실패: {e}")
                        return f'src="{src}"'  # 원본 유지
                
                # HTML 내의 이미지 src 속성을 로컬 상대 경로로 변경
                modified_html = re.sub(r'src="([^"]*)"', process_image_for_download, html_content)
                
                # 수정된 HTML을 ZIP에 추가
                zipf.writestr(f"{html_path.stem}.html", modified_html)
                logger.debug(f"🛠️ 수정된 HTML 파일 추가: {html_path.name}")
            
            # 메타데이터 JSON 추가
            if result_data:
                metadata = {
                    "generation_info": {
                        "type": result_data.get('generation_type', '상세페이지'),
                        "input_images": result_data.get('input_images'),
                        "product_images_count": result_data.get('product_images_count'),
                        "prompt_used": result_data.get('prompt_used'),
                        "generation_time": datetime.now().isoformat()
                    },
                    "files": {
                        "html": f"{html_path.stem}.html" if html_path else None,
                        "images_folder": "images/",
                        "main_image": f"images/{image_path.name}" if image_path else None
                    },
                    "usage": {
                        "html_file": "HTML 파일을 브라우저에서 열어보세요",
                        "images_folder": "images/ 폴더에 모든 관련 이미지가 포함되어 있습니다"
                    }
                }
                
                metadata_json = json.dumps(metadata, ensure_ascii=False, indent=2)
                zipf.writestr("metadata.json", metadata_json)
                logger.debug("🛠️ 메타데이터 JSON 추가")
            
            # README 파일 추가
            readme_content = """# GeoPage 생성 결과물

이 패키지에는 다음 파일들이 포함되어 있습니다:

## 📁 폴더 구조
├── [product_name].html          # 메인 상세페이지 HTML
├── images/                      # 모든 이미지 파일들
│   ├── [main_image].png        # 메인 결과 이미지
│   └── [other_images]...       # HTML 내 사용된 이미지들
├── metadata.json               # 생성 정보 메타데이터
└── README.md                   # 이 파일

## 📝 사용 방법
1. **HTML 파일 열기**: 메인 HTML 파일을 더블클릭하거나 브라우저로 드래그하세요
2. **이미지 확인**: images/ 폴더의 모든 이미지가 HTML에서 자동으로 표시됩니다
3. **메타데이터**: metadata.json에서 생성 과정의 상세 정보를 확인할 수 있습니다

## ⚠️ 주의사항
- HTML 파일과 images/ 폴더는 같은 위치에 있어야 합니다
- 폴더 구조를 변경하지 마세요

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
    
    with col3:
        # 통합 패키지 다운로드 (이미지 포함)
        if html_path and html_path.exists():
            if st.button("📦 전체 패키지", use_container_width=True, type="primary"):
                with st.spinner("패키지 생성 중..."):
                    zip_path = create_download_package(image_path, html_path, result_data)
                    
                    if zip_path and os.path.exists(zip_path):
                        with open(zip_path, "rb") as zip_file:
                            st.download_button(
                                label="📦 패키지 다운로드",
                                data=zip_file.read(),
                                file_name=os.path.basename(zip_path),
                                mime="application/zip",
                                use_container_width=True,
                                key="download_package"
                            )
                        # 임시 파일 정리
                        try:
                            os.unlink(zip_path)
                        except:
                            pass
                    else:
                        st.error("❌ 패키지 생성에 실패했습니다.")
        else:
            st.button("📦 전체 패키지", disabled=True, use_container_width=True)
    
    # 안내 메시지
    st.info("💡 **전체 패키지**를 다운로드하면 HTML 파일과 모든 이미지가 포함된 ZIP 파일을 받을 수 있습니다. 압축 해제 후 HTML 파일을 열면 이미지가 정상적으로 표시됩니다.")

def display_generation_details(result_data: Dict[str, Any]):
    """생성 상세 정보 표시"""
    logger.debug("🛠️ 생성 상세 정보 표시 시작")
    
    with st.expander("🔍 생성 상세 정보", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**생성 설정:**")
            st.write(f"- 생성 타입: 상세페이지")
            st.write(f"- 포함된 이미지: {len(result_data.get('image_path_list', []))}개")
            st.write(f"- 반영된 차별점: {len(result_data.get('difference', []))}개")
        
        with col2:
            st.write("**기술 정보:**")
            st.write("- 텍스트 생성: OpenAI GPT-4o-mini")
            st.write("- HTML 생성: 구조화된 템플릿")
            st.write("- 이미지 변환: Playwright")
            st.write("- 출력 형식: HTML + PNG")
        
        # 포함된 이미지 경로들 표시
        image_paths = result_data.get('image_path_list', [])
        if image_paths:
            st.write("**포함된 이미지 파일들:**")
            for i, path in enumerate(image_paths, 1):
                st.write(f"  {i}. `{Path(path).name}`")
        
        # 반영된 차별점들 표시
        differences = result_data.get('difference', [])
        if differences:
            st.write("**반영된 차별점들:**")
            for i, diff in enumerate(differences, 1):
                st.write(f"  {i}. {diff}")
        
        # session_id 정보
        if result_data.get('session_id'):
            st.write(f"**세션 ID:** `{result_data['session_id']}`")

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
    
    # 결과 이미지 표시 (전체 너비)
    image_path = display_result_image(result_data)
    
    # 결과 HTML 표시
    html_path = display_result_html(result_data)
    
    st.markdown("---")
    
    # 메인 정보 섹션 (이미지 아래로 이동)
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # 다운로드 섹션 (이미지 아래로 이동)
        display_download_section(image_path, html_path, result_data)
    
    with col2:
        # 상품 정보 표시 (사용자별 세션 고려)
        processed_data_key = get_user_session_key('processed_data')
        
        if processed_data_key in st.session_state:
            product_data = st.session_state[processed_data_key]
            st.subheader("📦 상품 정보")
            st.write(f"**상품명:** {product_data.get('name', 'N/A')}")
            st.write(f"**브랜드:** {product_data.get('brand', 'N/A')}")
            st.write(f"**카테고리:** {product_data.get('category', 'N/A')}")
            st.write(f"**가격:** {product_data.get('price', 0):,}원")
            st.write(f"**특징:** {product_data.get('features', 'N/A')}")
        elif 'processed_data' in st.session_state:
            # 백업: 전역 세션에서 가져오기
            product_data = st.session_state.processed_data
            st.subheader("📦 상품 정보")
            st.write(f"**상품명:** {product_data.get('name', 'N/A')}")
            st.write(f"**브랜드:** {product_data.get('brand', 'N/A')}")
            st.write(f"**카테고리:** {product_data.get('category', 'N/A')}")
            st.write(f"**가격:** {product_data.get('price', 0):,}원")
            st.write(f"**특징:** {product_data.get('features', 'N/A')}")
        elif result_data:
            # 결과 데이터에서 상품 정보 가져오기
            st.subheader("📦 상품 정보")
            st.write(f"**상품명:** {result_data.get('name', 'N/A')}")
            st.write(f"**브랜드:** {result_data.get('brand', 'N/A')}")
            st.write(f"**카테고리:** {result_data.get('category', 'N/A')}")
            st.write(f"**가격:** {result_data.get('price', 0):,}원")
            st.write(f"**특징:** {result_data.get('features', 'N/A')}")
    
    st.markdown("---")
    
    # 생성 상세 정보
    # display_generation_details(result_data)
    
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
            # 사용자별 세션 상태 초기화
            user_session_id = st.session_state.get('user_session_id', 'default')
            
            # 사용자별 키들 초기화
            user_keys_to_clear = [
                'processed_data', 'composition_result', 'composition_data', 'detail_page_result',
                'selected_user_images_model', 'selected_user_images_background',
                'selected_model_image', 'selected_background',
                'analysis_result', 'analysis_started', 'combined_results'
            ]
            
            for base_key in user_keys_to_clear:
                user_key = get_user_session_key(base_key)
                if user_key in st.session_state:
                    del st.session_state[user_key]
            
            # 전역 키들도 초기화 (호환성)
            for key in user_keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            
            logger.info(f"✅ 사용자 세션 상태 초기화 완료 (세션: {user_session_id[:8]}...)")
            st.switch_page("home.py")

if __name__ == "__main__":
    main()