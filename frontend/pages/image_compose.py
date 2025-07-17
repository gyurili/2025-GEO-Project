import streamlit as st
import os
import sys
from typing import Dict, Any, List, Optional
from pathlib import Path
import json

# 로거 임포트 추가
sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.logger import get_logger

# 로거 설정
logger = get_logger(__name__)

def load_models_data():
    """models 폴더에서 모델 데이터 로드"""
    logger.debug("🛠️ 모델 데이터 로드 시작")
    
    models_dir = Path(__file__).parent.parent.parent / "backend" / "data" / "models"
    logger.debug(f"🛠️ 모델 디렉토리: {models_dir}")
    
    models_data = {}
    
    if not models_dir.exists():
        logger.warning(f"⚠️ 모델 디렉토리가 존재하지 않습니다: {models_dir}")
        # 디렉토리 생성
        models_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ 모델 디렉토리 생성: {models_dir}")
        return models_data
    
    try:
        # models 폴더의 하위 폴더들을 모델로 인식
        for model_folder in models_dir.iterdir():
            if model_folder.is_dir():
                model_name = model_folder.name
                logger.debug(f"🛠️ 모델 폴더 발견: {model_name}")
                
                # 각 모델 폴더에서 이미지 파일들 찾기
                model_images = []
                mask_images = []
                
                for file in model_folder.iterdir():
                    if file.is_file() and file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']:
                        if 'mask' in file.name.lower():
                            mask_images.append(str(file))
                            logger.debug(f"🛠️ 마스크 이미지 발견: {file.name}")
                        else:
                            model_images.append(str(file))
                            logger.debug(f"🛠️ 모델 이미지 발견: {file.name}")
                
                if model_images:  # 모델 이미지가 있는 경우만 추가
                    models_data[model_name] = {
                        'model_images': model_images,
                        'mask_images': mask_images
                    }
                    logger.debug(f"🛠️ 모델 {model_name} 등록: 모델 이미지 {len(model_images)}개, 마스크 {len(mask_images)}개")
        
        logger.info(f"✅ 모델 데이터 로드 완료: {len(models_data)}개 모델")
        return models_data
        
    except Exception as e:
        logger.error(f"❌ 모델 데이터 로드 실패: {e}")
        return {}

def display_user_images(tab_key=""):
    """사용자가 업로드한 이미지들 표시 및 선택"""
    logger.debug("🛠️ 사용자 이미지 표시 시작")
    
    if 'processed_data' not in st.session_state or not st.session_state.processed_data:
        logger.warning("⚠️ 처리된 상품 데이터가 없음")
        st.error("❌ 상품 데이터가 없습니다. 먼저 상품 정보를 입력해주세요.")
        if st.button("🔙 상품 입력 페이지로 돌아가기", key=f"back_to_home_user_{tab_key}"):
            st.switch_page("home.py")
        return None
    
    processed_data = st.session_state.processed_data
    logger.debug(f"🛠️ 처리된 데이터: {processed_data}")
    image_paths = processed_data.get('image_path', [])
    logger.debug(f"🛠️ 이미지 경로들: {image_paths}")
    
    if not image_paths:
        logger.warning("⚠️ 업로드된 이미지가 없음")
        st.warning("⚠️ 업로드된 이미지가 없습니다.")
        return None
    
    logger.debug(f"🛠️ 사용자 이미지 수: {len(image_paths)}")
    
    st.subheader("📸 업로드한 상품 이미지 선택")
    st.write("합성에 사용할 상품 이미지를 선택해주세요.")
    
    # 이미지 선택을 위한 라디오 버튼과 이미지 표시
    selected_image = None
    
    # 프로젝트 루트 경로
    project_root = Path(__file__).parent.parent.parent
    
    # 이미지들을 그리드로 표시
    cols = st.columns(min(3, len(image_paths)))
    
    for i, image_path in enumerate(image_paths):
        col_idx = i % len(cols)
        with cols[col_idx]:
            # 절대 경로로 변환
            full_image_path = project_root / image_path
            logger.debug(f"🛠️ 이미지 경로 확인: {full_image_path}")
            logger.debug(f"🛠️ 파일 존재 여부: {full_image_path.exists()}")

            if full_image_path.exists():
                # 선택된 이미지인지 확인
                selected_user = st.session_state.get('selected_user_image')
                is_selected = selected_user and selected_user['index'] == i
                
                if is_selected:
                    st.markdown("</div>", unsafe_allow_html=True)
                
                st.image(str(full_image_path), caption=f"이미지 {i+1}", width=200)
                
                if is_selected:
                    st.markdown("</div>", unsafe_allow_html=True)
                
                # 클릭하면 선택/해제
                if st.button("선택", 
                            key=f"select_user_image_{tab_key}_{i}",
                            type="primary" if is_selected else "secondary"):
                    if is_selected:
                        # 이미 선택된 경우 선택 해제
                        if 'selected_user_image' in st.session_state:
                            del st.session_state.selected_user_image
                    else:
                        # 새로 선택
                        st.session_state.selected_user_image = {
                            'index': i,
                            'path': str(full_image_path),
                            'relative_path': image_path
                        }
                    logger.debug(f"🛠️ 사용자 이미지 선택 변경: {image_path}")
                    st.rerun()
            else:
                # 대안 경로 시도
                alt_path = Path(__file__).parent.parent / image_path
                logger.debug(f"🛠️ 대안 경로 시도: {alt_path}")
                
                if alt_path.exists():
                    # 선택된 이미지인지 확인
                    selected_user = st.session_state.get('selected_user_image')
                    is_selected = selected_user and selected_user['index'] == i
                    
                    if is_selected:
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    st.image(str(alt_path), caption=f"이미지 {i+1}", width=200)
                    
                    if is_selected:
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    # 클릭하면 선택/해제
                    if st.button("선택", 
                                key=f"select_user_image_alt_{tab_key}_{i}",
                                type="primary" if is_selected else "secondary"):
                        if is_selected:
                            # 이미 선택된 경우 선택 해제
                            if 'selected_user_image' in st.session_state:
                                del st.session_state.selected_user_image
                        else:
                            # 새로 선택
                            st.session_state.selected_user_image = {
                                'index': i,
                                'path': str(alt_path),
                                'relative_path': image_path
                            }
                        logger.debug(f"🛠️ 사용자 이미지 선택 변경: {image_path}")
                        st.rerun()
                else:
                    logger.warning(f"⚠️ 이미지 파일이 존재하지 않음: {full_image_path}")
                    st.error(f"이미지를 찾을 수 없습니다: {image_path}")
                    st.write(f"찾는 경로: {full_image_path}")
                    continue
    
    # 선택된 이미지 반환 (메시지 없이)
    if 'selected_user_image' in st.session_state:
        return st.session_state.selected_user_image

    return None

def display_model_selection(models_data: Dict):
    """모델 선택 UI"""
    logger.debug("🛠️ 모델 선택 UI 표시 시작")
    
    if not models_data:
        st.warning("⚠️ 사용 가능한 모델이 없습니다.")
        st.info("💡 backend/data/models 폴더에 모델 이미지를 추가해주세요.")
        return None, None
    
    st.subheader("👤 모델 선택")
    
    # 모델 선택 드롭다운
    model_names = list(models_data.keys())
    selected_model_name = st.selectbox(
        "사용할 모델을 선택하세요",
        options=model_names,
        index=0,
        help="상품을 착용할 모델을 선택해주세요."
    )
    
    if not selected_model_name:
        return None, None
    
    logger.debug(f"🛠️ 선택된 모델: {selected_model_name}")
    
    model_info = models_data[selected_model_name]
    model_images = model_info['model_images']
    mask_images = model_info['mask_images']
    
    # 모델 이미지 선택
    st.write("**모델 이미지 선택:**")
    
    selected_model_image = None
    if model_images:
        # 모델 이미지들을 그리드로 표시
        cols = st.columns(min(3, len(model_images)))
        
        for i, model_image_path in enumerate(model_images):
            col_idx = i % len(cols)
            with cols[col_idx]:
                if os.path.exists(model_image_path):
                    # 선택된 모델 이미지인지 확인
                    current_selected = st.session_state.get('selected_model_image')
                    is_selected = (current_selected and 
                                current_selected['model_name'] == selected_model_name and 
                                current_selected['index'] == i)
                    
                    if is_selected:
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    st.image(model_image_path, caption=f"모델 {i+1}", width=200)
                    
                    if is_selected:
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    if st.button("선택", 
                                key=f"select_model_{selected_model_name}_{i}",
                                type="primary" if is_selected else "secondary"):
                        st.session_state.selected_model_image = {
                            'path': model_image_path,
                            'index': i,
                            'model_name': selected_model_name
                        }
                        logger.debug(f"🛠️ 모델 이미지 선택: {model_image_path}")
                        st.rerun()
                else:
                    st.error(f"이미지를 찾을 수 없습니다: {model_image_path}")
    
    # 선택된 모델 이미지 반환
    selected_model_image = st.session_state.get('selected_model_image')
    if not (selected_model_image and selected_model_image['model_name'] == selected_model_name):
        selected_model_image = None
    
    # 마스크 이미지 선택 (모델 이미지가 선택된 경우에만)
    selected_mask_image = None
    if selected_model_image and mask_images:
        st.write("**마스크 이미지 선택:**")
        
        # 마스크 이미지들을 그리드로 표시
        cols = st.columns(min(3, len(mask_images)))
        
        for i, mask_image_path in enumerate(mask_images):
            col_idx = i % len(cols)
            with cols[col_idx]:
                if os.path.exists(mask_image_path):
                    # 선택된 마스크 이미지인지 확인
                    current_selected_mask = st.session_state.get('selected_mask_image')
                    is_selected = (current_selected_mask and 
                                current_selected_mask['model_name'] == selected_model_name and 
                                current_selected_mask['index'] == i)
                    
                    if is_selected:
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    st.image(mask_image_path, caption=f"마스크 {i+1}", width=200)
                    
                    if is_selected:
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    if st.button("선택", 
                                key=f"select_mask_{selected_model_name}_{i}",
                                type="primary" if is_selected else "secondary"):
                        st.session_state.selected_mask_image = {
                            'path': mask_image_path,
                            'index': i,
                            'model_name': selected_model_name
                        }
                        logger.debug(f"🛠️ 마스크 이미지 선택: {mask_image_path}")
                        st.rerun()
                else:
                    st.error(f"마스크를 찾을 수 없습니다: {mask_image_path}")
        
        # 선택된 마스크 이미지 표시
        selected_mask_image = st.session_state.get('selected_mask_image')
        if selected_mask_image and selected_mask_image['model_name'] == selected_model_name:
            st.success(f"✅ 선택된 마스크: 마스크 {selected_mask_image['index'] + 1}")
        else:
            selected_mask_image = None
    
    elif selected_model_image and not mask_images:
        st.info("💡 이 모델에는 마스크 이미지가 없습니다.")
    
    return selected_model_image, selected_mask_image

def display_generation_options():
    """이미지 생성 요청사항 입력"""
    logger.debug("🛠️ 이미지 생성 옵션 표시 시작")
    
    st.subheader("⚙️ 이미지 생성 옵션")
    
    # 생성 요청사항 (선택사항)
    custom_prompt = st.text_area(
        "생성 요청사항 (선택사항)",
        placeholder="예: 밝은 배경, 자연스러운 조명, 고품질 사진",
        height=100,
        help="이미지 생성 시 추가로 반영하고 싶은 요청사항을 입력해주세요."
    )
    
    # 생성 품질 설정
    quality = st.selectbox(
        "생성 품질",
        options=["표준", "고품질", "최고품질"],
        index=1,
        help="이미지 생성 품질을 선택해주세요. 품질이 높을수록 처리 시간이 길어집니다."
    )
    
    # 생성 스타일
    style = st.selectbox(
        "생성 스타일",
        options=["자연스러운", "상업적", "아티스틱", "미니멀"],
        index=0,
        help="이미지의 전체적인 스타일을 선택해주세요."
    )
    
    return {
        'custom_prompt': custom_prompt.strip() if custom_prompt else None,
        'quality': quality,
        'style': style
    }

def load_backgrounds_data():
    """backgrounds 폴더에서 배경 데이터 로드"""
    logger.debug("🛠️ 배경 데이터 로드 시작")
    
    backgrounds_dir = Path(__file__).parent.parent.parent / "backend" / "data" / "backgrounds"
    logger.debug(f"🛠️ 배경 디렉토리: {backgrounds_dir}")
    
    backgrounds_data = []
    
    if not backgrounds_dir.exists():
        logger.warning(f"⚠️ 배경 디렉토리가 존재하지 않습니다: {backgrounds_dir}")
        backgrounds_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ 배경 디렉토리 생성: {backgrounds_dir}")
        return backgrounds_data
    
    try:
        # 배경 이미지 파일들 찾기
        for file in backgrounds_dir.iterdir():
            if file.is_file() and file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']:
                backgrounds_data.append(str(file))
                logger.debug(f"🛠️ 배경 이미지 발견: {file.name}")
        
        logger.info(f"✅ 배경 데이터 로드 완료: {len(backgrounds_data)}개 배경")
        return backgrounds_data
        
    except Exception as e:
        logger.error(f"❌ 배경 데이터 로드 실패: {e}")
        return []

def show_model_generation_tab():
    """모델 이미지 생성 탭"""
    logger.debug("🛠️ 모델 이미지 생성 탭 표시")
    
    # 모델 데이터 로드
    models_data = load_models_data()
    
    # 기존 코드에서 단계별 UI 부분 이동
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # 1단계: 사용자 이미지 선택
        selected_user_image = display_user_images("model")
    
    with col2:
        # 2단계: 모델 선택
        selected_model_image, selected_mask_image = display_model_selection(models_data)
    
    st.markdown("---")
    
    # 생성 요청사항만 입력 (품질, 스타일 제외)
    custom_prompt = st.text_area(
        "생성 요청사항 (선택사항)",
        placeholder="예: 밝은 배경, 자연스러운 조명, 고품질 사진",
        height=100,
        help="이미지 생성 시 추가로 반영하고 싶은 요청사항을 입력해주세요.",
        key="model_prompt"
    )
    
    generation_options = {
        'custom_prompt': custom_prompt.strip() if custom_prompt else None,
        'type': 'model'
    }
    
    # 합성 버튼
    show_generation_buttons(selected_user_image, selected_model_image, selected_mask_image, generation_options)

def show_background_generation_tab():
    """배경 이미지 생성 탭"""
    logger.debug("🛠️ 배경 이미지 생성 탭 표시")
    
    # 배경 데이터 로드
    backgrounds_data = load_backgrounds_data()
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # 1단계: 사용자 이미지 선택
        selected_user_image = display_user_images("background")
    
    with col2:
        # 2단계: 배경 선택
        selected_background = display_background_selection(backgrounds_data)
    
    st.markdown("---")
    
    # 전체 생성 옵션 (품질, 스타일 포함)
    generation_options = display_generation_options_full()
    generation_options['type'] = 'background'
    
    # 합성 버튼
    show_generation_buttons(selected_user_image, selected_background, None, generation_options)

def display_background_selection(backgrounds_data: List):
    """배경 선택 UI"""
    logger.debug("🛠️ 배경 선택 UI 표시 시작")
    
    if not backgrounds_data:
        st.warning("⚠️ 사용 가능한 배경이 없습니다.")
        st.info("💡 backend/data/backgrounds 폴더에 배경 이미지를 추가해주세요.")
        return None
    
    st.subheader("🖼️ 배경 선택")
    
    selected_background = None
    if backgrounds_data:
        # 배경 이미지들을 그리드로 표시
        cols = st.columns(min(3, len(backgrounds_data)))
        
        for i, background_path in enumerate(backgrounds_data):
            col_idx = i % len(cols)
            with cols[col_idx]:
                if os.path.exists(background_path):
                    # 선택된 배경 이미지인지 확인
                    current_selected_bg = st.session_state.get('selected_background')
                    is_selected = current_selected_bg and current_selected_bg['index'] == i
                    
                    if is_selected:
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    st.image(background_path, caption=f"배경 {i+1}", width=200)
                    
                    if is_selected:
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    if st.button("선택", 
                                key=f"select_background_{i}",
                                type="primary" if is_selected else "secondary"):
                        if is_selected:
                            # 이미 선택된 경우 선택 해제
                            if 'selected_background' in st.session_state:
                                del st.session_state.selected_background
                        else:
                            # 새로 선택
                            st.session_state.selected_background = {
                                'path': background_path,
                                'index': i
                            }
                        logger.debug(f"🛠️ 배경 이미지 선택: {background_path}")
                        st.rerun()
                else:
                    st.error(f"이미지를 찾을 수 없습니다: {background_path}")
    
    # 선택된 배경 표시
    selected_background = st.session_state.get('selected_background')
    if selected_background:
        st.success(f"✅ 선택된 배경: 배경 {selected_background['index'] + 1}")
        return selected_background
    
    return None

def display_generation_options_full():
    """전체 이미지 생성 옵션 (배경 생성용)"""
    logger.debug("🛠️ 전체 이미지 생성 옵션 표시 시작")
    
    st.subheader("⚙️ 이미지 생성 옵션")
    
    # 생성 요청사항 (선택사항)
    custom_prompt = st.text_area(
        "생성 요청사항 (선택사항)",
        placeholder="예: 밝은 배경, 자연스러운 조명, 고품질 사진",
        height=100,
        help="이미지 생성 시 추가로 반영하고 싶은 요청사항을 입력해주세요.",
        key="background_prompt"
    )
    
    # 생성 품질 설정
    quality = st.selectbox(
        "생성 품질",
        options=["표준", "고품질", "최고품질"],
        index=1,
        help="이미지 생성 품질을 선택해주세요. 품질이 높을수록 처리 시간이 길어집니다.",
        key="background_quality"
    )
    
    # 생성 스타일
    style = st.selectbox(
        "생성 스타일",
        options=["자연스러운", "상업적", "아티스틱", "미니멀"],
        index=0,
        help="이미지의 전체적인 스타일을 선택해주세요.",
        key="background_style"
    )
    
    return {
        'custom_prompt': custom_prompt.strip() if custom_prompt else None,
        'quality': quality,
        'style': style
    }

def show_generation_buttons(selected_user_image, selected_target_image, selected_mask_image, generation_options):
    """합성 실행 버튼 표시"""
    logger.debug("🛠️ 합성 버튼 표시")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("🔙 상품 입력 페이지로 돌아가기", key=f"back_to_home_{generation_options['type']}"):
            logger.debug("🛠️ 상품 입력 페이지로 이동")
            st.switch_page("home.py")
    
    with col3:
        # 모든 필수 항목이 선택되었는지 확인
        can_generate = (
            selected_user_image is not None and 
            selected_target_image is not None
        )
        
        generation_type = "모델" if generation_options['type'] == 'model' else "배경"
        
        if can_generate:
            if st.button(f"🎨 {generation_type} 합성 시작", use_container_width=True, type="primary", key=f"generate_{generation_options['type']}"):
                logger.debug(f"🛠️ {generation_type} 합성 시작 버튼 클릭")
                
                # 합성 데이터 세션에 저장
                composition_data = {
                    'user_image': selected_user_image,
                    'target_image': selected_target_image,
                    'mask_image': selected_mask_image,
                    'generation_options': generation_options,
                    'product_data': st.session_state.processed_data
                }
                
                st.session_state.composition_data = composition_data
                logger.info(f"✅ {generation_type} 합성 데이터 준비 완료")
                
                st.success(f"🎉 {generation_type} 이미지 합성이 시작되었습니다!")
                st.info("💡 합성 기능은 아직 구현 중입니다.")
        else:
            st.button(f"🎨 {generation_type} 합성 시작", use_container_width=True, disabled=True, key=f"generate_disabled_{generation_options['type']}")
            
            # 누락된 항목 안내
            missing_items = []
            if not selected_user_image:
                missing_items.append("상품 이미지")
            if not selected_target_image:
                missing_items.append(f"{generation_type} 이미지")
            
            if missing_items:
                st.warning(f"⚠️ 다음 항목을 선택해주세요: {', '.join(missing_items)}")

def main():
    """이미지 합성 페이지 메인"""
    logger.debug("🛠️ 이미지 합성 페이지 시작")
    
    st.set_page_config(
        page_title="이미지 합성",
        page_icon="🎨",
        layout="wide"
    )
    
    st.title("🎨 이미지 합성")
    st.markdown("---")

    # 상품 정보 표시
    if 'processed_data' in st.session_state and st.session_state.processed_data:
        product_data = st.session_state.processed_data
        st.info(f"📦 상품: {product_data['name']} | 브랜드: {product_data['brand']} | 가격: {product_data['price']:,}원")

    # 탭 생성
    tab1, tab2 = st.tabs(["👤 모델 이미지 생성", "🖼️ 배경 이미지 생성"])

    with tab1:
        show_model_generation_tab()

    with tab2:
        show_background_generation_tab()

    # 사이드바 - 선택 상태 요약 및 도움말
    with st.sidebar:
        st.header("📋 선택 상태")
        
        # 세션 상태에서 선택 상태 확인
        selected_user = st.session_state.get('selected_user_image')
        selected_model = st.session_state.get('selected_model_image')
        selected_mask = st.session_state.get('selected_mask_image')
        selected_bg = st.session_state.get('selected_background')
        
        # 사용자 이미지
        if selected_user:
            st.success("✅ 상품 이미지 선택됨")
        else:
            st.error("❌ 상품 이미지 미선택")
        
        # 현재 탭에 따른 표시
        if selected_model:
            st.success("✅ 모델 이미지 선택됨")
        else:
            st.info("ℹ️ 모델 이미지 미선택")
            
        if selected_bg:
            st.success("✅ 배경 이미지 선택됨")
        else:
            st.info("ℹ️ 배경 이미지 미선택")
        
        # 마스크 이미지
        if selected_mask:
            st.success("✅ 마스크 이미지 선택됨")
        else:
            st.info("ℹ️ 마스크 이미지 선택사항")
        
        st.markdown("---")
        
        # 도움말
        st.header("💡 도움말")
        st.write("""
        **폴더 구조:**
        - `backend/data/models/` - 모델 이미지
        - `backend/data/backgrounds/` - 배경 이미지
        
        **모델 폴더 구조:**
        ```
        models/model1/
        ├── photo1.jpg
        └── mask1.png
        ```
        """)
        
        # 초기화 버튼
        if st.button("🔄 선택 초기화", use_container_width=True):
            logger.debug("🛠️ 선택 초기화 버튼 클릭")
            keys_to_remove = ['selected_user_image', 'selected_model_image', 'selected_mask_image', 'selected_background']
            for key in keys_to_remove:
                if key in st.session_state:
                    del st.session_state[key]
            logger.info("✅ 선택 상태 초기화 완료")
            st.rerun()

if __name__ == "__main__":
    main()