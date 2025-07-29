import streamlit as st
import requests
import json
import os
import time
import sys
from typing import Dict, Any, Optional
from pathlib import Path

# 로거 임포트 추가
sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import get_logger

# API 클라이언트 임포트
from api import (
    check_server_connection, 
    process_product_via_api, 
    get_product_data,
    get_current_config,
    validate_current_config
)

# 로거 설정
logger = get_logger(__name__)

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
if 'server_connected' not in st.session_state:
    st.session_state.server_connected = None

def validate_form_data(form_data: Dict[str, Any], uploaded_files=None) -> Dict[str, str]:
    """폼 데이터 유효성 검증"""
    logger.debug("🛠️ 폼 데이터 유효성 검증 시작")
    logger.debug(f"🛠️ 입력 데이터: {list(form_data.keys())}")
    
    errors = {}
    
    if not form_data.get('name', '').strip():
        errors['name'] = "상품명을 입력해주세요."
        logger.debug("🛠️ 상품명 검증 실패")
    
    if not form_data.get('category', '').strip():
        errors['category'] = "카테고리를 입력해주세요."
        logger.debug("🛠️ 카테고리 검증 실패")
    
    if not form_data.get('brand', '').strip():
        errors['brand'] = "브랜드명을 입력해주세요."
        logger.debug("🛠️ 브랜드명 검증 실패")
    
    if not form_data.get('features', '').strip():
        errors['features'] = "상품 특징을 입력해주세요."
        logger.debug("🛠️ 상품 특징 검증 실패")
    
    try:
        price = int(form_data.get('price', 0))
        if price <= 0:
            errors['price'] = "가격은 0보다 커야 합니다."
            logger.debug("🛠️ 가격 범위 검증 실패 (0 이하)")
        elif price > 10000000:
            errors['price'] = "가격은 1천만원 이하여야 합니다."
            logger.debug("🛠️ 가격 범위 검증 실패 (상한선 초과)")
    except (ValueError, TypeError):
        errors['price'] = "올바른 가격을 입력해주세요."
        logger.debug("🛠️ 가격 형식 검증 실패")
    
    # 이미지 검증 (필수)
    if not uploaded_files or len(uploaded_files) == 0:
        errors['images'] = "이미지는 필수 항목입니다. 최소 1개의 이미지를 업로드해주세요."
        logger.debug("🛠️ 이미지 필수 검증 실패")
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
            logger.debug(f"🛠️ 이미지 확장자 검증 실패: {invalid_files}")
    
    if errors:
        logger.warning(f"⚠️ 폼 데이터 검증 실패: {len(errors)}개 오류")
    else:
        logger.info("✅ 폼 데이터 유효성 검증 완료")
    
    return errors

def process_input_via_api(form_data: Dict[str, Any], uploaded_files=None) -> Optional[Dict[str, Any]]:
    """API를 통한 입력 처리"""
    logger.debug("🛠️ API를 통한 입력 처리 시작")
    logger.debug(f"🛠️ 폼 데이터: {list(form_data.keys())}")
    logger.debug(f"🛠️ 업로드된 파일 수: {len(uploaded_files) if uploaded_files else 0}")
    
    try:
        # 서버 연결 상태 확인
        logger.debug("🛠️ 서버 연결 상태 확인")
        if not check_server_connection():
            logger.error("❌ 백엔드 서버 연결 실패")
            st.error("❌ 백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
            return None
        
        # 다중 파일 업로드 처리
        if uploaded_files and len(uploaded_files) > 0:
            logger.debug(f"🛠️ 다중 이미지 업로드 처리: {len(uploaded_files)}개")
            # API 요청을 위한 files 딕셔너리 준비
            files = []
            
            for uploaded_file in uploaded_files:
                # 파일을 bytes로 읽어서 준비
                file_bytes = uploaded_file.getvalue()
                files.append((
                    'images',  # 필드명
                    (uploaded_file.name, file_bytes, uploaded_file.type)
                ))
                logger.debug(f"🛠️ 파일 준비: {uploaded_file.name} ({len(file_bytes)} bytes)")
            
            # multipart/form-data 요청으로 전송
            logger.debug("🛠️ API 요청 전송 (다중 이미지)")
            response = requests.post(
                "http://localhost:8010/input/process-multiple",
                data=form_data,
                files=files,
                timeout=30
            )
        else:
            logger.debug("🛠️ 이미지 없는 JSON 요청 처리")
            # 이미지가 없는 경우 JSON 요청
            response = requests.post(
                "http://localhost:8010/input/process-json",
                json=form_data,
                timeout=30
            )
        
        logger.debug(f"🛠️ API 응답 상태: HTTP {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            logger.debug(f"🛠️ API 응답 성공: {result.get('success', False)}")
            
            if result.get('success'):
                logger.info("✅ API를 통한 입력 처리 완료")
                return result.get('data')
            else:
                error_msg = result.get('message', '알 수 없는 오류')
                logger.error(f"❌ 서버 처리 오류: {error_msg}")
                st.error(f"❌ 서버 처리 오류: {error_msg}")
                return None
        else:
            logger.error(f"❌ API 요청 실패: HTTP {response.status_code}")
            st.error(f"❌ API 요청 실패: HTTP {response.status_code}")
            try:
                error_detail = response.json()
                if error_detail.get('detail'):
                    logger.error(f"❌ 상세 오류: {error_detail['detail']}")
                    st.error(f"상세 오류: {error_detail['detail']}")
            except:
                logger.debug("🛠️ 오류 응답 JSON 파싱 실패")
                pass
            return None
            
    except requests.exceptions.ConnectionError:
        logger.error("❌ 백엔드 서버 연결 오류")
        st.error("❌ 백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
        return None
    except requests.exceptions.Timeout:
        logger.error("❌ API 요청 시간 초과")
        st.error("❌ 요청 시간이 초과되었습니다. 다시 시도해주세요.")
        return None
    except Exception as e:
        logger.error(f"❌ API 처리 중 예외 발생: {str(e)}")
        st.error(f"❌ 처리 중 오류 발생: {str(e)}")
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
        if product_data.get('image_path_list'):
            st.write(f"**이미지:** {len(product_data['image_path_list'])}개")
            for i, img_path in enumerate(product_data['image_path_list']):
                st.write(f"  - 이미지 {i+1}: {img_path}")

def check_server_status():
    """서버 상태 확인 및 표시"""
    logger.debug("🛠️ 서버 상태 확인 함수 호출")
    
    if st.session_state.server_connected is None:
        # 처음 확인하는 경우
        logger.debug("🛠️ 첫 서버 연결 상태 확인")
        with st.spinner("서버 연결 상태 확인 중..."):
            st.session_state.server_connected = check_server_connection()
        
        if st.session_state.server_connected:
            logger.info("✅ 서버 연결 상태 확인 완료 - 연결됨")
        else:
            logger.warning("⚠️ 서버 연결 상태 확인 완료 - 연결 안됨")

def main():
    logger.debug("🛠️ Streamlit 메인 함수 시작")
    st.title("🛍️ 상품 정보 입력")
    st.markdown("---")
    
    # 서버 상태 확인
    check_server_status()
    
    # 서버 연결되지 않은 경우 기능 제한
    if not st.session_state.server_connected:
        logger.warning("⚠️ 서버 미연결로 기능 제한")
        st.warning("⚠️ 백엔드 서버에 연결되지 않아 일부 기능이 제한됩니다.")
        
        # 서버 재연결 버튼
        if st.button("🔄 서버 연결 재시도"):
            logger.debug("🛠️ 서버 재연결 버튼 클릭")
            st.session_state.server_connected = None
            st.rerun()
        return
    
    logger.debug("🛠️ 서버 연결 확인됨, 정상 기능 제공")
    
    # 입력 폼
    with st.form("product_form"):
        logger.debug("🛠️ 상품 입력 폼 렌더링 시작")
        st.subheader("📝 상품 기본 정보")
        
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input(
                "상품명 *",
                placeholder="예: 우일 여성 여름 인견 7부 블라우스",
                value="롤프 남성 정장자켓 수트마이 양복상의",
                help="상품의 정확한 이름을 입력해주세요."
            )
            # 상품명 오류 표시
            if 'validation_errors' in st.session_state and 'name' in st.session_state.validation_errors:
                st.error(f"❌ {st.session_state.validation_errors['name']}")
            
            category = st.text_input(
                "카테고리 *",
                placeholder="예: 블라우스",
                value="양복",
                help="상품이 속하는 카테고리를 입력해주세요."
            )
            # 카테고리 오류 표시
            if 'validation_errors' in st.session_state and 'category' in st.session_state.validation_errors:
                st.error(f"❌ {st.session_state.validation_errors['category']}")
            
            
        
        with col2:
            price = st.number_input(
                "가격 (원) *",
                min_value=0,
                max_value=10000000,
                value=58000,
                step=1000,
                help="상품의 가격을 입력해주세요."
            )

            # 브랜드 오류 표시
            if 'validation_errors' in st.session_state and 'price' in st.session_state.validation_errors:
                st.error(f"❌ {st.session_state.validation_errors['price']}")

            brand = st.text_input(
                "브랜드명 *",
                placeholder="예: 우일",
                value="롤프",
                help="상품의 브랜드명을 입력해주세요." 
            )
            # 브랜드 오류 표시
            if 'validation_errors' in st.session_state and 'brand' in st.session_state.validation_errors:
                st.error(f"❌ {st.session_state.validation_errors['brand']}")

        
        st.subheader("📋 상품 상세 정보")
        
        features = st.text_area(
            "상품 특징 *",
            placeholder="예: 인견 소재, 우수한 흡수성과 통기성, 부드러운 촉감",
            value="꼼꼼한 박음질, 고급스러운 원단, 클래식한 디자인",
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
            logger.debug(f"🛠️ 업로드된 이미지 파일 수: {len(uploaded_files)}")
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
        logger.debug("🛠️ 폼 제출 버튼 클릭됨")
        # 폼 데이터 구성
        form_data = {
            "name": name,
            "category": category,
            "price": price,
            "brand": brand,
            "features": features
        }
        
        logger.debug(f"🛠️ 폼 데이터 구성 완료: {list(form_data.keys())}")
        
        # 유효성 검증
        errors = validate_form_data(form_data, uploaded_files)
        
        if errors:
            logger.warning(f"⚠️ 폼 유효성 검증 실패: {len(errors)}개 오류")
            st.session_state.validation_errors = errors
            st.rerun()
        else:
            logger.info("✅ 폼 유효성 검증 성공")
            if 'validation_errors' in st.session_state:
                del st.session_state.validation_errors
            
            # 🎯 세션 상태에 데이터 저장
            st.session_state.form_data = form_data
            st.session_state.uploaded_files = uploaded_files
            st.session_state.processing_success = True
            logger.debug("🛠️ 세션 상태에 데이터 저장 완료")
            st.rerun()

    # 처리 성공 플래그가 있으면 실제 처리 실행
    if st.session_state.get('processing_success', False):
        logger.debug("🛠️ 처리 성공 플래그 감지, 실제 처리 시작")
        st.session_state.processing_success = False  # 플래그 리셋
        
        # 🎯 세션에서 데이터 가져오기
        form_data = st.session_state.get('form_data', {})
        uploaded_files = st.session_state.get('uploaded_files', None)
        
        logger.debug(f"🛠️ 세션에서 데이터 로드: {len(uploaded_files) if uploaded_files else 0}개 이미지")
        
        with st.spinner("상품 정보를 처리 중입니다..."):
            result = process_input_via_api(form_data, uploaded_files)
            
            if result:
                logger.info("✅ 상품 정보 처리 성공")
                st.session_state.processed_data = result
                st.session_state.config_created = True
                st.success("✅ 상품 정보 처리가 완료되었습니다!")
                st.info("🎨 이미지 합성 페이지로 이동합니다...")
                time.sleep(1)  # 1초 대기
                st.switch_page("pages/image_compose.py")
            else:
                logger.error("❌ 상품 정보 처리 실패")
                st.error("❌ 상품 정보 처리에 실패했습니다.")
    
    # 사이드바 - 추가 정보
    with st.sidebar:
        logger.debug("🛠️ 사이드바 렌더링")
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
        
        # 서버 상태 정보
        st.header("🔧 서버 상태")
        if st.session_state.server_connected:
            st.success("✅ 연결됨")
        else:
            st.error("❌ 연결 안됨")
            
        # 서버 재연결 버튼
        if st.button("🔄 서버 상태 확인", use_container_width=True):
            logger.debug("🛠️ 사이드바 서버 상태 확인 버튼 클릭")
            st.session_state.server_connected = None
            st.rerun()
        
        st.markdown("---")
        
        # 초기화 버튼
        if st.button("🔄 초기화", use_container_width=True):
            logger.debug("🛠️ 초기화 버튼 클릭")
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
            
            logger.info("✅ 세션 상태 초기화 완료")
            # 페이지 새로고침으로 입력 필드와 이미지 초기화
            st.rerun()

if __name__ == "__main__":
    main()