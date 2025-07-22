import streamlit as st
import os
import sys
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import requests
import time
import requests
from typing import List

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


def load_all_backgrounds_json():
    project_root = Path(__file__).parent.parent.parent
    json_path = project_root / "backend" / "data" / "backgrounds" / "json" / "all_backgrounds.json"
    if not json_path.exists():
        raise FileNotFoundError(f"배경 json 파일이 없습니다: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def display_user_images(tab_key=""):
    """사용자가 업로드한 이미지들 표시 및 다중 선택"""
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
    st.write("합성에 사용할 상품 이미지를 선택해주세요. (여러 개 선택 가능)")
    
    # 세션 상태에서 선택된 이미지들 초기화
    selected_images_key = f'selected_user_images_{tab_key}'
    if selected_images_key not in st.session_state:
        st.session_state[selected_images_key] = []
    
    # 프로젝트 루트 경로
    project_root = Path(__file__).parent.parent.parent
    
    # 전체 선택/해제 버튼
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("🔘 전체 선택", key=f"select_all_user_{tab_key}"):
            st.session_state[selected_images_key] = list(range(len(image_paths)))
            st.rerun()
    
    with col2:
        if st.button("⭕ 전체 해제", key=f"deselect_all_user_{tab_key}"):
            st.session_state[selected_images_key] = []
            st.rerun()
    
    with col3:
        selected_count = len(st.session_state[selected_images_key])
        st.write(f"**선택된 이미지: {selected_count}개**")
    
    # 이미지들을 그리드로 표시
    cols = st.columns(min(3, len(image_paths)))
    
    for i, image_path in enumerate(image_paths):
        col_idx = i % len(cols)
        with cols[col_idx]:
            # 절대 경로로 변환
            full_image_path = project_root / image_path
            logger.debug(f"🛠️ 이미지 경로 확인: {full_image_path}")

            if full_image_path.exists():
                # 선택된 이미지인지 확인
                is_selected = i in st.session_state[selected_images_key]
                
                st.image(str(full_image_path), caption=f"이미지 {i+1}", width=200)
                
                if is_selected:
                    st.markdown("</div>", unsafe_allow_html=True)
                
                # 개별 선택/해제 버튼
                if st.button(
                    "✅ 선택됨" if is_selected else "⭕ 선택", 
                    key=f"toggle_user_image_{tab_key}_{i}",
                    type="primary" if is_selected else "secondary"
                ):
                    if is_selected:
                        # 선택 해제
                        st.session_state[selected_images_key].remove(i)
                    else:
                        # 선택 추가
                        st.session_state[selected_images_key].append(i)
                        st.session_state[selected_images_key].sort()  # 순서 정렬
                    
                    logger.debug(f"🛠️ 사용자 이미지 선택 변경: {image_path}")
                    st.rerun()
                    
            else:
                # 대안 경로 시도 (기존 코드와 동일)
                alt_path = Path(__file__).parent.parent / image_path
                logger.debug(f"🛠️ 대안 경로 시도: {alt_path}")
                
                if alt_path.exists():
                    # 선택된 이미지인지 확인
                    is_selected = i in st.session_state[selected_images_key]
                    
                    if is_selected:
                        st.markdown(
                            '<div style="border: 3px solid #FF6B6B; border-radius: 10px; padding: 5px;">',
                            unsafe_allow_html=True
                        )
                    
                    st.image(str(alt_path), caption=f"이미지 {i+1}", width=200)
                    
                    if is_selected:
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    # 개별 선택/해제 버튼
                    if st.button(
                        "✅ 선택됨" if is_selected else "⭕ 선택", 
                        key=f"toggle_user_image_alt_{tab_key}_{i}",
                        type="primary" if is_selected else "secondary"
                    ):
                        if is_selected:
                            st.session_state[selected_images_key].remove(i)
                        else:
                            st.session_state[selected_images_key].append(i)
                            st.session_state[selected_images_key].sort()
                        
                        logger.debug(f"🛠️ 사용자 이미지 선택 변경: {image_path}")
                        st.rerun()
                else:
                    logger.warning(f"⚠️ 이미지 파일이 존재하지 않음: {full_image_path}")
                    st.error(f"이미지를 찾을 수 없습니다: {image_path}")
                    continue
    
    # 선택된 이미지들 반환
    selected_indices = st.session_state[selected_images_key]
    if selected_indices:
        selected_user_images = []
        for idx in selected_indices:
            if idx < len(image_paths):
                full_path = project_root / image_paths[idx]
                if not full_path.exists():
                    full_path = Path(__file__).parent.parent / image_paths[idx]
                
                selected_user_images.append({
                    'index': idx,
                    'path': str(full_path),
                    'relative_path': image_paths[idx]
                })
        
        logger.debug(f"🛠️ 선택된 사용자 이미지 수: {len(selected_user_images)}")
        return selected_user_images

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

def show_model_generation_tab():
    """모델 이미지 생성 탭"""
    logger.debug("🛠️ 모델 이미지 생성 탭 표시")
    
    # 모델 데이터 로드
    models_data = load_models_data()
    
    # 기존 코드에서 단계별 UI 부분 이동
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # 1단계: 사용자 이미지 선택
        selected_user_images = display_user_images("model")
    
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
    show_generation_buttons(selected_user_images, selected_model_image, selected_mask_image, generation_options)

def show_background_generation_tab():
    logger.debug("🛠️ 배경 이미지 생성 탭 표시 (카테고리 기반)")

    backgrounds_json = load_all_backgrounds_json()

    col1, col2 = st.columns([1, 1])

    with col1:
        # 기존과 동일하게 사용자 이미지 선택
        selected_user_images = display_user_images("background")

    with col2:
        # 🟦 카테고리/소분류 선택 → 프롬프트
        selected_category_info = display_background_category_ui(backgrounds_json)

    st.markdown("---")

    # 품질/스타일 옵션(선택)
    generation_options = display_generation_options_full()
    generation_options['type'] = 'background'
    # 🟦 카테고리 기반 프롬프트 사용
    generation_options['category'] = selected_category_info['category']
    generation_options['subcategory'] = selected_category_info['subcategory']
    generation_options['custom_prompt'] = selected_category_info['prompt']  # 기존 커스텀 대신

    # 합성 버튼
    show_generation_buttons(selected_user_images, selected_category_info, None, generation_options)

def display_background_category_ui(backgrounds_json):
    st.subheader("🗂️ 배경 카테고리/소분류 선택")
    
    # 1. 대분류(카테고리) 선택
    categories = list(backgrounds_json.keys())
    selected_category = st.selectbox("대분류를 선택하세요", categories, key="category_select")

    # 2. 소분류(항목) 선택
    sub_items = list(backgrounds_json[selected_category].keys())
    selected_subcategory = st.selectbox("소분류를 선택하세요", sub_items, key="subcategory_select")

    # 3. 프롬프트/예시 이미지
    selected_info = backgrounds_json[selected_category][selected_subcategory]
    prompt = selected_info["prompt"]
    example_image = selected_info["example_image"]

    # 프로젝트 루트를 기준으로 절대 경로 생성
    project_root = Path(__file__).parent.parent.parent
    example_path = project_root / example_image
    
    if example_path.exists():
        st.image(str(example_path), caption="예시 이미지", width=350)
    else:
        st.warning("예시 이미지를 찾을 수 없습니다.")

    # 선택 결과 반환
    return {
        "category": selected_category,
        "subcategory": selected_subcategory,
        "prompt": prompt,
        "example_image": example_image
    }



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

def show_generation_buttons(selected_user_images, selected_target_image, selected_mask_image, generation_options):
    """합성 실행 버튼 표시 (다중 상품 이미지 → 단일 결과)"""
    logger.debug("🛠️ 합성 버튼 표시")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("🔙 상품 입력 페이지로 돌아가기", key=f"back_to_home_{generation_options['type']}"):
            logger.debug("🛠️ 상품 입력 페이지로 이동")
            st.switch_page("home.py")
    
    with col3:
        # 모든 필수 항목이 선택되었는지 확인
        can_generate = (
            selected_user_images is not None and 
            len(selected_user_images) > 0 and  # 최소 1개 이상
            selected_target_image is not None
        )
        
        generation_type = "모델" if generation_options['type'] == 'model' else "배경"
        
        if can_generate:
            user_count = len(selected_user_images)
            if user_count == 1:
                button_text = f"🎨 {generation_type} 합성 시작"
            else:
                button_text = f"🎨 {generation_type} 합성 시작 ({user_count}개 상품)"
            
            if st.button(button_text, use_container_width=True, type="primary", key=f"generate_{generation_options['type']}"):
                logger.debug(f"🛠️ {generation_type} 합성 시작 버튼 클릭 ({user_count}개 상품)")
                
                # 단일 API 호출용 합성 데이터
                composition_data = {
                    'user_images': selected_user_images,  # 다중 이미지를 배열로 전달
                    'target_image': selected_target_image,
                    'mask_image': selected_mask_image,
                    'generation_options': generation_options,
                    'product_data': st.session_state.processed_data
                }
                
                st.session_state.composition_data = composition_data
                logger.info(f"✅ {generation_type} 합성 데이터 준비 완료 ({user_count}개 상품)")
                
                # 단일 API 호출
                with st.spinner(f"{generation_type} 이미지 합성 중... ({user_count}개 상품 → 1개 결과)"):
                    try:
                        response = requests.post(
                            "http://localhost:8010/api/input/compose",
                            json=composition_data,
                            timeout=120  # 다중 이미지 처리를 위해 시간 증가
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            if result.get('success'):
                                st.success(f"🎉 {generation_type} 이미지 합성이 완료되었습니다! ({user_count}개 상품)")
                                
                                # 단일 결과 저장
                                st.session_state.composition_result = result['data']
                                
                            else:
                                st.error(f"❌ 합성 실패: {result.get('message', '알 수 없는 오류')}")
                        else:
                            st.error(f"❌ API 요청 실패: HTTP {response.status_code}")
                            
                    except requests.exceptions.Timeout:
                        st.error("❌ 요청 시간 초과. 다중 이미지 합성에는 시간이 걸릴 수 있습니다.")
                    except Exception as e:
                        st.error(f"❌ 합성 중 오류: {str(e)}")
        else:
            st.button(f"🎨 {generation_type} 합성 시작", use_container_width=True, disabled=True, key=f"generate_disabled_{generation_options['type']}")
            
            # 누락된 항목 안내
            missing_items = []
            if not selected_user_images or len(selected_user_images) == 0:
                missing_items.append("상품 이미지 (최소 1개)")
            if not selected_target_image:
                missing_items.append(f"{generation_type} 이미지")
            
            if missing_items:
                st.warning(f"⚠️ 다음 항목을 선택해주세요: {', '.join(missing_items)}")

def display_result_selection(result: Dict[str, Any]):
    """단일 합성 결과 표시 및 선택"""
    logger.debug("🛠️ 단일 합성 결과 표시 시작")
    
    # 결과 이미지 표시
    project_root = Path(__file__).parent.parent.parent
    result_image_path = project_root / result['result_image_path']
    
    if result_image_path.exists():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(str(result_image_path), caption="합성 결과", width=500)
        
        # 결과 정보
        st.write(f"**생성 타입:** {result['generation_type']}")
        st.write(f"**사용된 이미지 수:** {result['input_images']}개")
        
        # 사용된 프롬프트 표시
        with st.expander("🔍 사용된 프롬프트 보기"):
            st.code(result['prompt_used'])
        
        # 이미지 선택 상태
        selected_key = 'selected_result_for_detail'
        if selected_key not in st.session_state:
            st.session_state[selected_key] = None
        
        # 선택 버튼
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            is_selected = st.session_state[selected_key] == result['result_image_path']
            
            if st.button(
                "✅ 선택됨" if is_selected else "⭕ 선택하기",
                key="select_single_result",
                type="primary" if is_selected else "secondary",
                use_container_width=True
            ):
                if is_selected:
                    st.session_state[selected_key] = None
                else:
                    st.session_state[selected_key] = result['result_image_path']
                st.rerun()
        
        # 상세페이지 생성 버튼
        display_detail_page_generation_button()
        
        # 다운로드 버튼
        with open(result_image_path, "rb") as file:
            st.download_button(
                label="📥 결과 이미지 다운로드",
                data=file.read(),
                file_name=result_image_path.name,
                mime="image/png",
                use_container_width=True
            )
    else:
        st.error("결과 이미지를 찾을 수 없습니다.")

def display_multiple_results_selection(results: List[Dict[str, Any]]):
    """다중 합성 결과 표시 및 선택"""
    logger.debug(f"🛠️ 다중 합성 결과 표시 시작: {len(results)}개")
    
    if not results:
        st.warning("표시할 결과가 없습니다.")
        return
    
    st.write(f"**생성된 결과: {len(results)}개**")
    st.write("마음에 드는 이미지를 선택한 후 상세페이지를 생성하세요.")
    
    # 선택된 결과 상태 관리
    selected_key = 'selected_result_for_detail'
    if selected_key not in st.session_state:
        st.session_state[selected_key] = None
    
    project_root = Path(__file__).parent.parent.parent
    
    # 결과들을 그리드로 표시
    cols_per_row = 3
    for i in range(0, len(results), cols_per_row):
        cols = st.columns(cols_per_row)
        
        for j, result in enumerate(results[i:i+cols_per_row]):
            result_idx = i + j
            with cols[j]:
                result_image_path = project_root / result['result_image_path']
                
                if result_image_path.exists():
                    # 선택된 이미지인지 확인
                    is_selected = st.session_state[selected_key] == result['result_image_path']
                    
                    # 선택된 이미지는 테두리 표시
                    if is_selected:
                        st.markdown(
                            '<div style="border: 3px solid #FF6B6B; border-radius: 10px; padding: 5px;">',
                            unsafe_allow_html=True
                        )
                    
                    st.image(str(result_image_path), caption=f"결과 {result_idx + 1}", width=250)
                    
                    if is_selected:
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    # 개별 선택 버튼
                    if st.button(
                        "✅ 선택됨" if is_selected else "⭕ 선택",
                        key=f"select_result_{result_idx}",
                        type="primary" if is_selected else "secondary",
                        use_container_width=True
                    ):
                        if is_selected:
                            st.session_state[selected_key] = None
                        else:
                            st.session_state[selected_key] = result['result_image_path']
                        st.rerun()
                    
                    # 결과 정보 요약
                    st.caption(f"타입: {result['generation_type']}")
                    st.caption(f"이미지: {result['input_images']}개")
                else:
                    st.error(f"결과 {result_idx + 1} 이미지를 찾을 수 없습니다.")
    
    # 선택된 결과 요약 표시
    if st.session_state[selected_key]:
        selected_result = next(
            (r for r in results if r['result_image_path'] == st.session_state[selected_key]), 
            None
        )
        if selected_result:
            st.success(f"✅ 선택된 이미지: {selected_result['result_image_path']}")
            
            # 선택된 이미지의 프롬프트 표시
            with st.expander("🔍 선택된 이미지의 프롬프트 보기"):
                st.code(selected_result['prompt_used'])
    
    # 상세페이지 생성 버튼
    display_detail_page_generation_button()

def display_detail_page_generation_button():
    """상세페이지 생성 버튼 표시"""
    logger.debug("🛠️ 상세페이지 생성 버튼 표시")
    
    selected_key = 'selected_result_for_detail'
    selected_image = st.session_state.get(selected_key)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        if selected_image:
            if st.button(
                "📄 상세페이지 생성", 
                use_container_width=True, 
                type="primary",
                key="generate_detail_page"
            ):
                logger.debug(f"🛠️ 상세페이지 생성 버튼 클릭: {selected_image}")
                generate_detail_page(selected_image)
        else:
            st.button(
                "📄 상세페이지 생성", 
                use_container_width=True, 
                disabled=True,
                key="generate_detail_page_disabled"
            )
            st.caption("⚠️ 먼저 이미지를 선택해주세요")

def generate_detail_page(selected_image_path: str):
    """선택된 이미지로 상세페이지 생성"""
    logger.debug(f"🛠️ 상세페이지 생성 시작: {selected_image_path}")
    
    try:
        # 상세페이지 생성 API 호출
        generation_data = {
            'selected_image_path': selected_image_path,
            'product_data': st.session_state.get('processed_data'),
            'composition_data': st.session_state.get('composition_data')
        }
        
        with st.spinner("상세페이지 생성 중... (30초~1분 소요)"):
            response = requests.post(
                "http://localhost:8010/api/input/generate-detail-page",
                json=generation_data,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    logger.info("✅ 상세페이지 생성 완료")
                    
                    # 결과를 세션에 저장
                    detail_result = result['data']
                    st.session_state.detail_page_result = detail_result
                    
                    st.success("🎉 상세페이지 생성이 완료되었습니다!")
                    st.info("📄 결과 페이지로 이동합니다...")
                    
                    # 결과 페이지로 이동
                    time.sleep(1)
                    st.switch_page("pages/result.py")
                    
                else:
                    st.error(f"❌ 상세페이지 생성 실패: {result.get('message', '알 수 없는 오류')}")
            else:
                st.error(f"❌ API 요청 실패: HTTP {response.status_code}")
                
    except requests.exceptions.Timeout:
        st.error("❌ 요청 시간 초과. 상세페이지 생성에는 시간이 걸릴 수 있습니다.")
    except Exception as e:
        logger.error(f"❌ 상세페이지 생성 중 오류: {e}")
        st.error(f"❌ 상세페이지 생성 중 오류: {str(e)}")

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
        
        # 세션 상태에서 선택 상태 확인 (수정된 부분)
        selected_user_model = st.session_state.get('selected_user_images_model', [])
        selected_user_background = st.session_state.get('selected_user_images_background', [])
        selected_model = st.session_state.get('selected_model_image')
        selected_mask = st.session_state.get('selected_mask_image')
        selected_bg = st.session_state.get('selected_background')
        
        # 사용자 이미지 (탭별로 다른 키 확인)
        current_tab = "model"
        selected_user_images = selected_user_model if current_tab == "model" else selected_user_background
        
        if selected_user_images and len(selected_user_images) > 0:
            st.success(f"✅ 상품 이미지 선택됨 ({len(selected_user_images)}개)")
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
        
        # 초기화 버튼
        if st.button("🔄 선택 초기화", use_container_width=True):
            logger.debug("🛠️ 선택 초기화 버튼 클릭")
            keys_to_remove = ['selected_user_image', 'selected_model_image', 'selected_mask_image', 'selected_background']
            for key in keys_to_remove:
                if key in st.session_state:
                    del st.session_state[key]
            logger.info("✅ 선택 상태 초기화 완료")
            st.rerun()
    
    # 합성 결과 표시
    if 'composition_result' in st.session_state:
        st.markdown("---")
        st.header("🎨 합성 결과")
        
        result = st.session_state.composition_result
        
        # 결과 이미지 표시 및 선택
        display_result_selection(result)

    # 또는 composition_results (다중 결과)가 있는 경우
    if 'composition_results' in st.session_state:
        st.markdown("---")
        st.header("🎨 합성 결과들")
        
        results = st.session_state.composition_results
        display_multiple_results_selection(results)

if __name__ == "__main__":
    main()