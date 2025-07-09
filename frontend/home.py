import streamlit as st
import requests
import json
import os
import sys
from typing import Dict, Any, Optional
from pathlib import Path

# 백엔드 모듈 임포트를 위한 경로 설정
backend_path = Path(__file__).parent.parent / "backend"
sys.path.append(str(backend_path))

from backend.input_handler.core.input_main import InputHandler

# 페이지 설정
st.set_page_config(
    page_title="상품 정보 입력",
    page_icon="🛍️",
    layout="wide"
)

# 세션 상태 초기화
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None
if 'config_created' not in st.session_state:
    st.session_state.config_created = False

def validate_form_data(form_data: Dict[str, Any], uploaded_files=None) -> Dict[str, str]:
    """폼 데이터 유효성 검증"""
    errors = {}
    
    if not form_data.get('name', '').strip():
        errors['name'] = "상품명을 입력해주세요."
    
    if not form_data.get('category', '').strip():
        errors['category'] = "카테고리를 입력해주세요."
    
    if not form_data.get('brand', '').strip():
        errors['brand'] = "브랜드명을 입력해주세요."
    
    if not form_data.get('features', '').strip():
        errors['features'] = "상품 특징을 입력해주세요."
    
    try:
        price = int(form_data.get('price', 0))
        if price <= 0:
            errors['price'] = "가격은 0보다 커야 합니다."
        elif price > 10000000:
            errors['price'] = "가격은 1천만원 이하여야 합니다."
    except (ValueError, TypeError):
        errors['price'] = "올바른 가격을 입력해주세요."
    
    # 이미지 검증 (필수)
    if not uploaded_files or len(uploaded_files) == 0:
        errors['images'] = "이미지는 필수 항목입니다. 최소 1개의 이미지를 업로드해주세요."
    else:
        # 이미지 확장자 검증
        allowed_extensions = ['png', 'jpg', 'jpeg', 'webp']
        invalid_files = []
        
        for uploaded_file in uploaded_files:
            file_extension = uploaded_file.name.split('.')[-1].lower()
            if file_extension not in allowed_extensions:
                invalid_files.append(uploaded_file.name)
        
        if invalid_files:
            errors['images'] = f"허용되지 않은 파일 형식입니다. 허용 형식: {', '.join(allowed_extensions.upper())}. 오류 파일: {', '.join(invalid_files)}"
    
    return errors

def process_input_locally(form_data: Dict[str, Any], uploaded_files=None) -> Optional[Dict[str, Any]]:
    """로컬에서 직접 입력 처리"""
    try:
        # InputHandler 인스턴스 생성
        project_root = Path(__file__).parent.parent
        handler = InputHandler(project_root=str(project_root))
        
        # 입력 처리
        result = handler.process_form_input(form_data, uploaded_files)
        
        return result
        
    except Exception as e:
        st.error(f"입력 처리 중 오류 발생: {str(e)}")
        return None

def display_product_summary(product_data: Dict[str, Any]):
    """상품 정보 요약 표시"""
    st.subheader("📋 입력된 상품 정보")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**상품명:** {product_data['name']}")
        st.write(f"**카테고리:** {product_data['category']}")
        st.write(f"**브랜드:** {product_data['brand']}")
        st.write(f"**가격:** {product_data['price']:,}원")
    
    with col2:
        st.write(f"**특징:** {product_data['features']}")
        if product_data.get('product_link'):
            st.write(f"**상품 링크:** {product_data['product_link']}")
        if product_data.get('image_path'):
            st.write(f"**이미지:** {len(product_data['image_path'])}개")
            for i, img_path in enumerate(product_data['image_path']):
                st.write(f"  - 이미지 {i+1}: {img_path}")

def main():
    st.title("🛍️ 상품 정보 입력")
    st.markdown("---")
    
    # 입력 폼
    with st.form("product_form"):
        st.subheader("📝 상품 기본 정보")
        
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input(
                "상품명 *",
                placeholder="예: 우일 여성 여름 인견 7부 블라우스",
                help="상품의 정확한 이름을 입력해주세요."
            )
            # 상품명 오류 표시
            if 'validation_errors' in st.session_state and 'name' in st.session_state.validation_errors:
                st.error(f"❌ {st.session_state.validation_errors['name']}")
            
            category = st.text_input(
                "카테고리 *",
                placeholder="예: 블라우스",
                help="상품이 속하는 카테고리를 입력해주세요."
            )
            # 카테고리 오류 표시
            if 'validation_errors' in st.session_state and 'category' in st.session_state.validation_errors:
                st.error(f"❌ {st.session_state.validation_errors['category']}")
            
            brand = st.text_input(
                "브랜드명 *",
                placeholder="예: 우일",
                help="상품의 브랜드명을 입력해주세요."
            )
            # 브랜드 오류 표시
            if 'validation_errors' in st.session_state and 'brand' in st.session_state.validation_errors:
                st.error(f"❌ {st.session_state.validation_errors['brand']}")
        
        with col2:
            price = st.number_input(
                "가격 (원) *",
                min_value=0,
                max_value=10000000,
                value=0,
                step=1000,
                help="상품의 가격을 입력해주세요."
            )
            # 가격 오류 표시
            if 'validation_errors' in st.session_state and 'price' in st.session_state.validation_errors:
                st.error(f"❌ {st.session_state.validation_errors['price']}")
            
            product_link = st.text_input(
                "상품 링크 (선택사항)",
                placeholder="https://www.example.com/product/123",
                help="상품 페이지 링크가 있다면 입력해주세요."
            )
        
        st.subheader("📋 상품 상세 정보")
        
        features = st.text_area(
            "상품 특징 *",
            placeholder="예: 인견 소재, 우수한 흡수성과 통기성, 부드러운 촉감",
            height=100,
            help="상품의 주요 특징을 입력해주세요."
        )
        # 특징 오류 표시
        if 'validation_errors' in st.session_state and 'features' in st.session_state.validation_errors:
            st.error(f"❌ {st.session_state.validation_errors['features']}")
        
        st.subheader("🖼️ 상품 이미지 *")

        uploaded_files = st.file_uploader(
            "상품 이미지 업로드 (필수, 여러 개 가능)",
            type=['png', 'jpg', 'jpeg', 'webp'],
            accept_multiple_files=True,
            help="상품 이미지를 업로드하세요. 여러 개의 이미지를 선택할 수 있습니다. (PNG, JPG, JPEG, WEBP 형식만 지원)"
        )

        # 이미지 오류 표시
        if 'validation_errors' in st.session_state and 'images' in st.session_state.validation_errors:
            st.error(f"❌ {st.session_state.validation_errors['images']}")

        if uploaded_files:
            st.write(f"📸 선택된 이미지: {len(uploaded_files)}개")
            
            # 이미지 미리보기 (최대 5개까지)
            cols = st.columns(min(5, len(uploaded_files)))
            for i, uploaded_file in enumerate(uploaded_files[:5]):
                with cols[i]:
                    st.image(uploaded_file, caption=f"이미지 {i+1}", width=120)
            
            if len(uploaded_files) > 5:
                st.info(f"+ {len(uploaded_files) - 5}개의 추가 이미지가 업로드되었습니다.")
        
        st.markdown("---")
        
        # 폼 제출 버튼
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col2:
            submit_button = st.form_submit_button(
                "상세페이지 생성",
                use_container_width=True,
                type="primary"
            )
    
    # 폼 제출 처리
    if submit_button:
        # 폼 데이터 구성
        form_data = {
            "name": name,
            "category": category,
            "price": price,
            "brand": brand,
            "features": features,
            "product_link": product_link if product_link else None
        }
        
        # 유효성 검증
        errors = validate_form_data(form_data, uploaded_files)
        
        if errors:
            st.session_state.validation_errors = errors
            st.rerun()
        else:
            if 'validation_errors' in st.session_state:
                del st.session_state.validation_errors
            
            # 🎯 세션 상태에 데이터 저장
            st.session_state.form_data = form_data
            st.session_state.uploaded_files = uploaded_files
            st.session_state.processing_success = True
            st.rerun()

    # 처리 성공 플래그가 있으면 실제 처리 실행 (라인 244-255 수정)
    if st.session_state.get('processing_success', False):
        st.session_state.processing_success = False  # 플래그 리셋
        
        # 🎯 세션에서 데이터 가져오기
        form_data = st.session_state.get('form_data', {})
        uploaded_files = st.session_state.get('uploaded_files', None)
        
        with st.spinner("상품 정보를 처리 중입니다..."):
            result = process_input_locally(form_data, uploaded_files)
            
            if result:
                st.session_state.processed_data = result
                st.session_state.config_created = True
                st.success("✅ 상품 정보 처리가 완료되었습니다!")
                st.balloons()
            else:
                st.error("❌ 상품 정보 처리에 실패했습니다.")
    
    # 처리 결과 표시
    if st.session_state.processed_data:
        st.markdown("---")
        display_product_summary(st.session_state.processed_data)
        
        # JSON 데이터 표시
        with st.expander("🔍 상세 JSON 데이터 보기"):
            st.json(st.session_state.processed_data)
        
        # 설정 파일 상태
        if st.session_state.config_created:
            st.success("📁 config.yaml 파일이 생성되었습니다.")
            
            # 다운로드 버튼
            json_str = json.dumps(st.session_state.processed_data, ensure_ascii=False, indent=2)
            st.download_button(
                label="📥 JSON 데이터 다운로드",
                data=json_str,
                file_name="product_data.json",
                mime="application/json"
            )
    
    # 사이드바 - 추가 정보
    with st.sidebar:
        st.header("ℹ️ 사용 가이드")
        
        st.markdown("""
        ### 📝 입력 필수 항목
        - 상품명
        - 카테고리  
        - 브랜드명
        - 가격
        - 상품 특징
        - 이미지
        """)
        
        st.markdown("---")
        
        # 초기화 버튼
        if st.button("🔄 초기화", use_container_width=True):
            # 모든 세션 상태 초기화
            st.session_state.processed_data = None
            st.session_state.config_created = False
            
            # 유효성 검사 오류 메시지 초기화
            if 'validation_errors' in st.session_state:
                del st.session_state.validation_errors
            
            # 처리 관련 플래그 초기화
            if 'processing_success' in st.session_state:
                del st.session_state.processing_success
            if 'form_data' in st.session_state:
                del st.session_state.form_data
            if 'uploaded_files' in st.session_state:
                del st.session_state.uploaded_files
            
            # 페이지 새로고침으로 입력 필드와 이미지 초기화
            st.rerun()

if __name__ == "__main__":
    main()