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
import threading
import asyncio
from datetime import datetime
import uuid

# 로거 임포트 추가
sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.logger import get_logger

# API 클라이언트 임포트
sys.path.append(str(Path(__file__).parent.parent))
from api import analyze_product, compose_images, generate_detail_page

# 로거 설정
logger = get_logger(__name__)

# 세션 상태 기반 상태 관리 (전역 변수 대신)
def get_analysis_status():
    return st.session_state.get('analysis_status', 'idle')

def set_analysis_status(status):
    st.session_state.analysis_status = status

def get_analysis_result():
    return st.session_state.get('analysis_result', None)

def set_analysis_result(result):
    st.session_state.analysis_result = result

def get_analysis_start_time():
    return st.session_state.get('analysis_start_time', None)

def set_analysis_start_time(start_time):
    st.session_state.analysis_start_time = start_time

def analyze_product_async(product_data: Dict[str, Any]):
    """백그라운드에서 상품 분석을 수행하는 함수"""
    import json
    import os
    from pathlib import Path
    
    try:
        logger.info("🚀 백그라운드 상품 분석 시작")
        
        # 임시 파일로 상태 저장 (스레드 안전성)
        temp_dir = Path(__file__).parent.parent.parent / "temp"
        temp_dir.mkdir(exist_ok=True)
        status_file = temp_dir / "analysis_status.json"
        
        # 실행 중 상태 저장
        status_data = {
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "result": None
        }
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, ensure_ascii=False)
        
        # API 호출
        start_time = datetime.now()
        result = analyze_product(product_data)
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"🛠️ 상품 분석 API 호출 결과 (소요시간: {duration:.2f}초): {result}")
        
        # 백엔드 응답 형태에 맞게 처리
        if result and result.get('success') and 'data' in result:
            logger.info("✅ 백그라운드 상품 분석 성공")
            final_result = {"success": True, "data": result['data']}
            logger.debug(f"🛠️ 저장될 후보 이미지: {final_result['data'].get('candidate_images', [])}")
        elif result and isinstance(result, dict) and 'differences' in result:
            # 이전 형태의 응답 처리 (하위 호환성)
            logger.info("✅ 백그라운드 상품 분석 성공 (이전 형태)")
            final_result = {"success": True, "data": result}
        else:
            logger.error(f"❌ 백그라운드 상품 분석 실패: {result}")
            final_result = result or {"success": False, "error": "API 응답 없음"}
        
        # 완료 상태 저장
        status_data = {
            "status": "completed" if final_result.get('success') else "failed",
            "start_time": start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "result": final_result
        }
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, ensure_ascii=False)
            
        logger.debug(f"🛠️ 분석 결과를 임시 파일에 저장: {status_file}")
            
    except Exception as e:
        logger.error(f"❌ 백그라운드 상품 분석 중 예외 발생: {str(e)}")
        status_data = {
            "status": "failed",
            "start_time": datetime.now().isoformat(),
            "end_time": datetime.now().isoformat(),
            "result": {"success": False, "error": str(e)}
        }
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, ensure_ascii=False)

def handle_async_product_analysis():
    """비동기 상품 분석을 처리하는 메인 함수 (백그라운드 실행)"""
    import json
    from pathlib import Path
    
    # 처리된 데이터가 있는지 확인
    if 'processed_data' not in st.session_state or not st.session_state.processed_data:
        return
    
    # 페이지 진입 시 한 번만 실행하도록 처리
    page_entry_key = 'image_compose_page_entered'
    if page_entry_key not in st.session_state:
        st.session_state[page_entry_key] = True
        # 페이지 첫 진입 시 임시 파일 정리
        temp_dir = Path(__file__).parent.parent.parent / "temp"
        status_file = temp_dir / "analysis_status.json"
        if status_file.exists():
            try:
                status_file.unlink()
                logger.info("🛠️ 기존 분석 상태 파일 삭제")
            except Exception as e:
                logger.warning(f"⚠️ 상태 파일 삭제 실패: {e}")
    
    # 이미 분석을 시작했는지 세션에서 확인 (무한루프 방지)
    if 'analysis_started' not in st.session_state:
        st.session_state.analysis_started = False
    
    # 임시 파일에서 상태 확인
    temp_dir = Path(__file__).parent.parent.parent / "temp"
    status_file = temp_dir / "analysis_status.json"
    
    current_status = "idle"
    current_result = None
    current_start_time = None
    
    if status_file.exists():
        try:
            with open(status_file, 'r', encoding='utf-8') as f:
                status_data = json.load(f)
                current_status = status_data.get("status", "idle")
                current_result = status_data.get("result")
                start_time_str = status_data.get("start_time")
                if start_time_str:
                    current_start_time = datetime.fromisoformat(start_time_str)
                logger.debug(f"🛠️ 파일에서 로드한 상태: {current_status}")
        except Exception as e:
            logger.error(f"❌ 상태 파일 읽기 실패: {e}")
    
    if current_status == "idle" and not st.session_state.analysis_started:
        # 자동으로 분석 시작 (사용자에게 노출 안됨)
        logger.info("🚀 상품 분석 백그라운드 시작")
        
        st.session_state.analysis_started = True
        
        # 스레드로 백그라운드 실행
        thread = threading.Thread(
            target=analyze_product_async,
            args=(st.session_state.processed_data,)
        )
        thread.daemon = True
        thread.start()
    
    elif current_status == "completed":
        # 완료 상태 - 결과를 세션에 저장만 하고 UI 노출 안함
        if current_result and 'analysis_result' not in st.session_state:
            st.session_state.analysis_result = current_result
            logger.info("✅ 백그라운드 상품 분석 완료 - 세션에 저장")
            logger.debug(f"🛠️ 저장된 후보 이미지 수: {len(current_result.get('data', {}).get('candidate_images', []))}")
    
    elif current_status == "failed":
        # 실패 상태 - 로그만 남기고 UI 노출 안함
        if current_result:
            error_msg = current_result.get("error", "알 수 없는 오류")
            logger.error(f"❌ 백그라운드 상품 분석 실패: {error_msg}")
        else:
            logger.error("❌ 백그라운드 상품 분석 실패: 알 수 없는 오류")
    

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
    image_paths = processed_data.get('image_path_list', [])
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
                
                # 🔍 분석 결과 확인
                analysis_result = st.session_state.get('analysis_result')
                
                if not analysis_result:
                    # 분석 결과가 아직 없는 경우
                    with st.spinner("🔍 상품 분석이 진행 중입니다... 잠시만 기다려주세요."):
                        # 최대 30초 동안 분석 완료 대기
                        max_wait_time = 30
                        wait_interval = 1
                        elapsed_time = 0
                        
                        while elapsed_time < max_wait_time:
                            time.sleep(wait_interval)
                            elapsed_time += wait_interval
                            
                            # 분석 결과 다시 확인
                            analysis_result = st.session_state.get('analysis_result')
                            if analysis_result:
                                logger.info(f"✅ 분석 완료 ({elapsed_time}초 대기)")
                                break
                            
                            # 상태 파일에서도 확인
                            temp_dir = Path(__file__).parent.parent.parent / "temp"
                            status_file = temp_dir / "analysis_status.json"
                            
                            if status_file.exists():
                                try:
                                    with open(status_file, 'r', encoding='utf-8') as f:
                                        status_data = json.load(f)
                                        if status_data.get("status") == "completed":
                                            current_result = status_data.get("result")
                                            if current_result:
                                                st.session_state.analysis_result = current_result
                                                analysis_result = current_result
                                                logger.info(f"✅ 상태 파일에서 분석 결과 로드 ({elapsed_time}초 대기)")
                                                break
                                except Exception as e:
                                    logger.warning(f"⚠️ 상태 파일 읽기 실패: {e}")
                    
                    # 여전히 분석 결과가 없는 경우
                    if not analysis_result:
                        st.error("❌ 상품 분석이 아직 완료되지 않았습니다. 잠시 후 다시 시도해주세요.")
                        st.info("💡 상품 분석은 백그라운드에서 진행되며, 보통 30초~1분 정도 소요됩니다.")
                        return
                
                # 분석 결과 유효성 검사
                if not (analysis_result.get('success') and 'data' in analysis_result):
                    st.error("❌ 상품 분석 결과가 유효하지 않습니다. 페이지를 새로고침 후 다시 시도해주세요.")
                    return
                
                logger.info(f"✅ 분석 결과 확인 완료 - 합성 진행")
                
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
                
                # API 클라이언트를 사용한 이미지 합성 호출
                with st.spinner(f"{generation_type} 이미지 합성 중... ({user_count}개 상품)"):
                    try:
                        result = compose_images(composition_data)
                        
                        if result and result.get('success'):
                            # 결과가 단일인지 다중인지 확인
                            if 'results' in result['data']:
                                # 다중 결과 (개별 생성)
                                results_data = result['data']['results']
                                st.success(f"🎉 {generation_type} 이미지 {len(results_data)}개가 생성되었습니다!")
                                
                                combined_results = []
                                
                                # 각 개별 결과를 combined_results에 추가
                                for i, individual_result in enumerate(results_data):
                                    composition_result = {
                                        **individual_result,
                                        'result_type': 'composition',
                                        'title': f'{generation_type} 합성 결과 {i+1}',
                                        'generation_type': generation_type,
                                        'input_images': 2 if generation_type == 'model' else 1,  # 상품+모델 또는 상품만
                                    }
                                    combined_results.append(composition_result)
                            else:
                                # 단일 결과 (통합 생성)
                                st.success(f"🎉 {generation_type} 이미지 합성이 완료되었습니다!")
                                
                                combined_results = []
                                
                                # 단일 합성 결과 추가
                                composition_result = result['data']
                                composition_result['result_type'] = 'composition'
                                composition_result['title'] = f'{generation_type} 합성 결과'
                                combined_results.append(composition_result)
                            
                            # 2. 분석 결과의 후보 이미지들 추가 (이제 analysis_result 확보됨)
                            if analysis_result and analysis_result.get('success') and 'data' in analysis_result:
                                analysis_data = analysis_result['data']
                                candidate_images = analysis_data.get('candidate_images', [])
                                
                                logger.debug(f"🛠️ 후보 이미지 데이터 구조: {candidate_images}")
                                logger.debug(f"🛠️ 후보 이미지 그룹 수: {len(candidate_images)}")
                                
                                # 후보 이미지 처리
                                for group_idx, image_group in enumerate(candidate_images):
                                    logger.debug(f"🛠️ 그룹 {group_idx}: {image_group} (타입: {type(image_group)})")
                                    if isinstance(image_group, list):
                                        for img_idx, img_path in enumerate(image_group):
                                            if img_path:  # 이미지 경로가 존재하는 경우
                                                logger.debug(f"🛠️ 후보 이미지 경로 원본: {img_path}")
                                                
                                                # 경로 정규화 (./ 제거)
                                                clean_path = img_path.lstrip('./')
                                                logger.debug(f"🛠️ 정리된 경로: {clean_path}")
                                                
                                                candidate_result = {
                                                    'result_image_path': clean_path,  # 정리된 경로 사용
                                                    'result_type': 'analysis_candidate',
                                                    'title': f'AI 분석 후보 이미지 {group_idx+1}-{img_idx+1}',
                                                    'generation_type': 'AI 분석',
                                                    'input_images': user_count,
                                                    'prompt_used': f"AI 상품 분석을 통해 생성된 후보 이미지 (그룹 {group_idx+1}, 이미지 {img_idx+1})"
                                                }
                                                combined_results.append(candidate_result)
                                                logger.debug(f"✅ 후보 이미지 추가됨: {clean_path}")
                            
                            # 전체 결과를 세션에 저장
                            st.session_state.combined_results = combined_results
                            st.rerun()  # 결과 표시를 위해 페이지 새로고침
                                
                        else:
                            error_msg = result.get('message', '알 수 없는 오류') if result else 'API 호출 실패'
                            st.error(f"❌ 합성 실패: {error_msg}")
                            
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

def display_combined_results_selection(results: List[Dict[str, Any]]):
    """결합된 결과 (합성 + 분석) 표시 및 다중 선택"""
    logger.debug(f"🛠️ 결합된 결과 표시 시작: {len(results)}개")
    
    if not results:
        st.warning("표시할 결과가 없습니다.")
        return
    
    # 원본 상품 개수 확인 (선택 가능한 최대 개수 결정)
    processed_data = st.session_state.get('processed_data', {})
    original_product_count = len(processed_data.get('image_path_list', []))
    max_selections = min(original_product_count, len(results))  # 원본 상품 수 또는 전체 결과 수 중 작은 값
    
    logger.debug(f"🛠️ 원본 상품 수: {original_product_count}, 최대 선택 가능: {max_selections}")
    
    # 모든 결과 타입 확인
    logger.debug("🛠️ 모든 결과 항목 확인:")
    for i, result in enumerate(results):
        logger.debug(f"  결과 {i}: result_type={result.get('result_type')}, title={result.get('title')}, path={result.get('result_image_path')}")
    
    # 결과를 타입별로 분류
    composition_results = [r for r in results if r.get('result_type') == 'composition']
    analysis_results = [r for r in results if r.get('result_type') == 'analysis_candidate']
    
    logger.debug(f"🛠️ 분류 결과: 합성 {len(composition_results)}개, 분석 후보 {len(analysis_results)}개")
    
    st.write(f"**총 생성된 결과: {len(results)}개**")
    if composition_results:
        st.write(f"  📦 합성 결과: {len(composition_results)}개")
    if analysis_results:
        st.write(f"  🤖 AI 분석 후보: {len(analysis_results)}개")
    
    # 다중 선택 안내
    if max_selections > 1:
        st.write(f"**최대 {max_selections}개까지 선택 가능합니다.** 선택한 이미지들이 모두 상세페이지에 포함됩니다.")
    else:
        st.write("**1개의 이미지를 선택해주세요.**")
    
    # 선택된 결과 상태 관리 (리스트로 변경)
    selected_key = 'selected_combined_results'  # 복수형으로 변경
    if selected_key not in st.session_state:
        st.session_state[selected_key] = []
    
    project_root = Path(__file__).parent.parent.parent
    
    # 전체 선택/해제 버튼 (최대 선택 수 제한)
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
    with col1:
        if st.button("🔘 전체 선택", key="select_all_combined"):
            # 최대 선택 수만큼만 선택
            all_paths = [r['result_image_path'] for r in results]
            st.session_state[selected_key] = all_paths[:max_selections]
            st.rerun()
    
    with col2:
        if st.button("⭕ 전체 해제", key="deselect_all_combined"):
            st.session_state[selected_key] = []
            st.rerun()
    
    with col3:
        selected_count = len(st.session_state[selected_key])
        st.write(f"**선택: {selected_count}/{max_selections}**")
    
    # 합성 결과 먼저 표시
    if composition_results:
        st.subheader("📦 합성 결과")
        display_result_grid_multi_select(composition_results, project_root, selected_key, "comp", max_selections)
    
    # AI 분석 후보 이미지 표시
    if analysis_results:
        st.subheader("🤖 AI 분석 후보 이미지")
        display_result_grid_multi_select(analysis_results, project_root, selected_key, "analysis", max_selections)
    
    # 선택된 결과 요약 표시
    selected_paths = st.session_state[selected_key]
    if selected_paths:
        st.success(f"✅ 선택된 이미지: {len(selected_paths)}개")
        
        # 선택된 이미지들의 정보 표시
        with st.expander("🔍 선택된 이미지 정보"):
            for i, path in enumerate(selected_paths, 1):
                selected_result = next(
                    (r for r in results if r['result_image_path'] == path), 
                    None
                )
                if selected_result:
                    st.write(f"**{i}. {selected_result.get('title', '알 수 없는 이미지')}**")
                    st.write(f"   타입: {selected_result.get('generation_type', 'N/A')}")
                    if selected_result.get('result_type') == 'composition':
                        st.write(f"   사용된 상품 이미지: {selected_result.get('input_images', 'N/A')}개")
    
    # 상세페이지 생성 버튼
    display_detail_page_generation_button_with_multi_selection(max_selections)

def display_result_grid_multi_select(results: List[Dict[str, Any]], project_root: Path, selected_key: str, key_prefix: str, max_selections: int):
    """결과 그리드 표시 (다중 선택 지원)"""
    logger.debug(f"🛠️ display_result_grid_multi_select 호출: {len(results)}개 결과, key_prefix={key_prefix}, 최대 선택={max_selections}")
    
    cols_per_row = 3
    for i in range(0, len(results), cols_per_row):
        cols = st.columns(cols_per_row)
        
        for j, result in enumerate(results[i:i+cols_per_row]):
            result_idx = i + j
            with cols[j]:
                relative_path = result['result_image_path']
                result_image_path = project_root / relative_path
                
                logger.debug(f"🛠️ 이미지 {result_idx}: {result.get('title', 'N/A')}")
                logger.debug(f"🛠️ 상대 경로: {relative_path}")
                logger.debug(f"🛠️ 절대 경로: {result_image_path}")
                logger.debug(f"🛠️ 파일 존재: {result_image_path.exists()}")
                
                if result_image_path.exists():
                    # 선택된 이미지인지 확인
                    selected_paths = st.session_state[selected_key]
                    is_selected = result['result_image_path'] in selected_paths
                    
                    # 이미지 표시
                    st.image(str(result_image_path), caption=result.get('title', f'결과 {result_idx + 1}'), width=250)
                    logger.debug(f"✅ 이미지 표시 성공: {result.get('title', 'N/A')}")
                    
                    # 선택 상태에 따른 스타일링
                    if is_selected:
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    # 개별 선택/해제 버튼
                    button_disabled = False
                    button_text = "✅ 선택됨" if is_selected else "⭕ 선택"
                    button_type = "primary" if is_selected else "secondary"
                    
                    # 최대 선택 수 도달 시 선택 버튼 비활성화 (이미 선택된 것은 제외)
                    if not is_selected and len(selected_paths) >= max_selections:
                        button_disabled = True
                        button_text = f"⭕ 선택 (최대 {max_selections}개)"
                        button_type = "secondary"
                    
                    if st.button(
                        button_text,
                        key=f"select_{key_prefix}_{result_idx}",
                        type=button_type,
                        use_container_width=True,
                        disabled=button_disabled
                    ):
                        if is_selected:
                            # 선택 해제
                            st.session_state[selected_key].remove(result['result_image_path'])
                        else:
                            # 선택 추가 (최대 개수 확인)
                            if len(selected_paths) < max_selections:
                                st.session_state[selected_key].append(result['result_image_path'])
                        
                        logger.debug(f"🛠️ 선택 상태 변경: {result['result_image_path']}")
                        st.rerun()
                    
                    # 결과 정보 요약
                    st.caption(f"타입: {result.get('generation_type', 'N/A')}")
                    if result.get('result_type') == 'composition':
                        st.caption(f"이미지: {result.get('input_images', 'N/A')}개")
                else:
                    logger.error(f"❌ 이미지 파일이 존재하지 않음: {result_image_path}")
                    st.error(f"이미지를 찾을 수 없습니다: {relative_path}")

def display_detail_page_generation_button_with_multi_selection(max_selections: int):
    """다중 선택된 이미지들로 상세페이지 생성 버튼 표시"""
    logger.debug("🛠️ 다중 선택 상세페이지 생성 버튼 표시")
    
    selected_key = 'selected_combined_results'
    selected_image_paths = st.session_state.get(selected_key, [])
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        if selected_image_paths:
            button_text = f"📄 상세페이지 생성 ({len(selected_image_paths)}개 이미지 포함)"
            
            if st.button(
                button_text,
                use_container_width=True, 
                type="primary",
                key="generate_detail_page_with_multi_selection"
            ):
                logger.debug(f"🛠️ 다중 선택 상세페이지 생성 버튼 클릭: {len(selected_image_paths)}개")
                handle_detail_page_generation_with_multi_selection(selected_image_paths)
        else:
            st.button(
                "📄 상세페이지 생성",
                use_container_width=True, 
                disabled=True,
                key="generate_detail_page_with_multi_selection_disabled"
            )
            st.caption("⚠️ 먼저 이미지를 선택해주세요")

def handle_detail_page_generation_with_multi_selection(selected_image_paths: List[str]):
    """다중 선택된 이미지들을 포함하여 상세페이지 생성 처리"""
    logger.debug(f"🛠️ 다중 선택 상세페이지 생성 시작: {len(selected_image_paths)}개")
    
    try:
        # config.yaml의 input 변수들 (product_data)
        product_data = st.session_state.get('processed_data', {}).copy()
        logger.debug(f"🛠️ 상품 데이터: {list(product_data.keys()) if product_data else 'None'}")
        
        # analysis_result에서 differences 추출
        analysis_result = st.session_state.get('analysis_result')
        differences = []
        if analysis_result and analysis_result.get('success') and 'data' in analysis_result:
            differences = analysis_result['data'].get('differences', [])
            logger.debug(f"🛠️ 추출된 차별점: {len(differences)}개")
        else:
            logger.warning("⚠️ 분석 결과에서 차별점을 찾을 수 없습니다")
        
        # 기존 사용자 업로드 이미지 경로 필터링 (backend/data/input/ 제외)
        existing_image_paths = product_data.get('image_path_list', [])
        filtered_paths = [
            path for path in existing_image_paths 
            if not path.startswith('backend/data/input/')
        ]
        
        logger.debug(f"🛠️ 기존 경로: {existing_image_paths}")
        logger.debug(f"🛠️ 필터링된 경로: {filtered_paths}")
        
        # 선택된 이미지들을 추가 (중복 확인)
        for selected_path in selected_image_paths:
            if selected_path not in filtered_paths:
                filtered_paths.append(selected_path)
                logger.debug(f"🛠️ 선택된 이미지 추가: {selected_path}")
            else:
                logger.debug(f"🛠️ 선택된 이미지가 이미 존재함: {selected_path}")
        
        updated_image_paths = filtered_paths
        
        # 상세페이지 생성 API 호출용 데이터 구성
        generation_data = {
            **product_data,  # config.yaml의 input 변수들을 직접 펼쳐서 넘기기
            'image_path_list': updated_image_paths,  # 선택된 이미지들이 포함된 리스트
            'difference': differences,  # analysis_result의 differences를 difference 키로 넘기기
            'selected_image_paths': selected_image_paths  # 선택된 이미지 경로들 (참고용)
        }
        
        logger.debug(f"🛠️ 상세페이지 생성 데이터 구성 완료: {list(generation_data.keys())}")
        logger.debug(f"🛠️ 업데이트된 이미지 경로 수: {len(updated_image_paths)}")
        logger.debug(f"🛠️ 선택된 이미지 수: {len(selected_image_paths)}")
        logger.debug(f"🛠️ 차별점 개수: {len(differences)}")
        
        with st.spinner(f"상세페이지 생성 중... ({len(selected_image_paths)}개 이미지 포함, 30초~1분 소요)"):
            result = generate_detail_page(generation_data)
            
            logger.debug(f"🛠️ 다중 선택 상세페이지 생성 API 응답: {result}")
            
            if result and result.get('success'):
                logger.info(f"✅ 다중 선택 상세페이지 생성 완료 ({len(selected_image_paths)}개 이미지)")
                
                # 결과를 세션에 저장
                detail_result = result.get('data')
                if detail_result:
                    st.session_state.detail_page_result = detail_result
                    logger.debug(f"🛠️ 세션에 저장된 detail_page_result (다중 선택): {list(detail_result.keys()) if detail_result else 'None'}")
                    
                    st.success(f"🎉 상세페이지 생성이 완료되었습니다! ({len(selected_image_paths)}개 이미지 포함)")
                    st.info("📄 결과 페이지로 이동합니다...")
                    
                    # 결과 페이지로 이동
                    time.sleep(1)
                    st.switch_page("pages/result.py")
                else:
                    st.error("❌ 상세페이지 생성 결과 데이터가 없습니다.")
            else:
                error_msg = result.get('error', '알 수 없는 오류') if result else 'API 호출 실패'
                st.error(f"❌ 상세페이지 생성 실패: {error_msg}")
                
    except requests.exceptions.Timeout:
        st.error("❌ 요청 시간 초과. 상세페이지 생성에는 시간이 걸릴 수 있습니다.")
    except Exception as e:
        logger.error(f"❌ 다중 선택 상세페이지 생성 중 오류: {e}")
        st.error(f"❌ 상세페이지 생성 중 오류: {str(e)}")

def display_result_grid(results: List[Dict[str, Any]], project_root: Path, selected_key: str, key_prefix: str):
    """결과 그리드 표시 (공통 함수)"""
    logger.debug(f"🛠️ display_result_grid 호출: {len(results)}개 결과, key_prefix={key_prefix}")
    
    cols_per_row = 3
    for i in range(0, len(results), cols_per_row):
        cols = st.columns(cols_per_row)
        
        for j, result in enumerate(results[i:i+cols_per_row]):
            result_idx = i + j
            with cols[j]:
                relative_path = result['result_image_path']
                result_image_path = project_root / relative_path
                
                logger.debug(f"🛠️ 이미지 {result_idx}: {result.get('title', 'N/A')}")
                logger.debug(f"🛠️ 상대 경로: {relative_path}")
                logger.debug(f"🛠️ 절대 경로: {result_image_path}")
                logger.debug(f"🛠️ 파일 존재: {result_image_path.exists()}")
                
                if result_image_path.exists():
                    # 선택된 이미지인지 확인
                    is_selected = st.session_state[selected_key] == result['result_image_path']
                    
                    # 이미지 표시
                    st.image(str(result_image_path), caption=result.get('title', f'결과 {result_idx + 1}'), width=250)
                    logger.debug(f"✅ 이미지 표시 성공: {result.get('title', 'N/A')}")
                    
                    if is_selected:
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    # 개별 선택 버튼
                    if st.button(
                        "✅ 선택됨" if is_selected else "⭕ 선택",
                        key=f"select_{key_prefix}_{result_idx}",
                        type="primary" if is_selected else "secondary",
                        use_container_width=True
                    ):
                        if is_selected:
                            st.session_state[selected_key] = None
                        else:
                            st.session_state[selected_key] = result['result_image_path']
                        st.rerun()
                    
                    # 결과 정보 요약
                    st.caption(f"타입: {result.get('generation_type', 'N/A')}")
                    if result.get('result_type') == 'composition':
                        st.caption(f"이미지: {result.get('input_images', 'N/A')}개")
                else:
                    logger.error(f"❌ 이미지 파일이 존재하지 않음: {result_image_path}")
                    st.error(f"이미지를 찾을 수 없습니다: {relative_path}")
                    
                    # 대안 경로들 시도
                    alternative_paths = [
                        Path(relative_path),  # 상대 경로 그대로
                        project_root / "backend" / "data" / "output" / Path(relative_path).name,  # output 폴더
                        project_root / Path(relative_path).name,  # 프로젝트 루트에 파일명만
                    ]
                    
                    found_alternative = False
                    for alt_path in alternative_paths:
                        logger.debug(f"🛠️ 대안 경로 시도: {alt_path}")
                        if alt_path.exists():
                            logger.info(f"✅ 대안 경로에서 이미지 발견: {alt_path}")
                            st.image(str(alt_path), caption=f"{result.get('title', f'결과 {result_idx + 1}')} (대안 경로)", width=250)
                            found_alternative = True
                            break
                    
                    if not found_alternative:
                        st.error(f"모든 대안 경로에서도 이미지를 찾을 수 없습니다")
                        logger.error(f"❌ 모든 대안 경로 실패: {[str(p) for p in alternative_paths]}")

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
                handle_detail_page_generation(selected_image)
        else:
            st.button(
                "📄 상세페이지 생성", 
                use_container_width=True, 
                disabled=True,
                key="generate_detail_page_disabled"
            )
            st.caption("⚠️ 먼저 이미지를 선택해주세요")

def display_detail_page_generation_button_with_selection():
    """선택된 이미지를 image_path_list에 포함하여 상세페이지 생성 버튼 표시"""
    logger.debug("🛠️ 선택된 이미지 포함 상세페이지 생성 버튼 표시")
    
    selected_key = 'selected_combined_result'
    selected_image_path = st.session_state.get(selected_key)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        if selected_image_path:
            if st.button(
                "📄 상세페이지 생성 (선택 이미지 포함)", 
                use_container_width=True, 
                type="primary",
                key="generate_detail_page_with_selection"
            ):
                logger.debug(f"🛠️ 선택된 이미지 포함 상세페이지 생성 버튼 클릭: {selected_image_path}")
                handle_detail_page_generation_with_selection(selected_image_path)
        else:
            st.button(
                "📄 상세페이지 생성", 
                use_container_width=True, 
                disabled=True,
                key="generate_detail_page_with_selection_disabled"
            )
            st.caption("⚠️ 먼저 이미지를 선택해주세요")

def handle_detail_page_generation(selected_image_path: str):
    """선택된 이미지로 상세페이지 생성 처리"""
    logger.debug(f"🛠️ 상세페이지 생성 시작: {selected_image_path}")
    
    try:
        # config.yaml의 input 변수들 (product_data)
        product_data = st.session_state.get('processed_data', {})
        logger.debug(f"🛠️ 상품 데이터: {list(product_data.keys()) if product_data else 'None'}")
        
        # analysis_result에서 differences 추출
        analysis_result = st.session_state.get('analysis_result')
        differences = []
        if analysis_result and analysis_result.get('success') and 'data' in analysis_result:
            differences = analysis_result['data'].get('differences', [])
            logger.debug(f"🛠️ 추출된 차별점: {len(differences)}개")
        else:
            logger.warning("⚠️ 분석 결과에서 차별점을 찾을 수 없습니다")
        
        # 상세페이지 생성 API 호출용 데이터 구성
        generation_data = {
            **product_data,  # config.yaml의 input 변수들을 직접 펼쳐서 넘기기
            'difference': differences,  # analysis_result의 differences를 difference 키로 넘기기
            'selected_image_path': selected_image_path  # 선택된 이미지 경로
        }
        
        logger.debug(f"🛠️ 상세페이지 생성 데이터 구성 완료: {list(generation_data.keys())}")
        logger.debug(f"🛠️ 차별점 개수: {len(differences)}")
        logger.debug(f"🛠️ 선택된 이미지: {selected_image_path}")
        
        with st.spinner("상세페이지 생성 중... (30초~1분 소요)"):
            result = generate_detail_page(generation_data)
            
            logger.debug(f"🛠️ 상세페이지 생성 API 응답: {result}")
            
            if result and result.get('success'):
                logger.info("✅ 상세페이지 생성 완료")
                
                # 결과를 세션에 저장 (백엔드 응답 형태에 맞게 수정)
                detail_result = result.get('data')
                if detail_result:
                    st.session_state.detail_page_result = detail_result
                    logger.debug(f"🛠️ 세션에 저장된 detail_page_result: {list(detail_result.keys()) if detail_result else 'None'}")
                    
                    st.success("🎉 상세페이지 생성이 완료되었습니다!")
                    st.info("📄 결과 페이지로 이동합니다...")
                    
                    # 결과 페이지로 이동
                    time.sleep(1)
                    st.switch_page("pages/result.py")
                else:
                    st.error("❌ 상세페이지 생성 결과 데이터가 없습니다.")
            else:
                error_msg = result.get('error', '알 수 없는 오류') if result else 'API 호출 실패'
                st.error(f"❌ 상세페이지 생성 실패: {error_msg}")
                
    except requests.exceptions.Timeout:
        st.error("❌ 요청 시간 초과. 상세페이지 생성에는 시간이 걸릴 수 있습니다.")
    except Exception as e:
        logger.error(f"❌ 상세페이지 생성 중 오류: {e}")
        st.error(f"❌ 상세페이지 생성 중 오류: {str(e)}")

def handle_detail_page_generation_with_selection(selected_image_path: str):
    """선택된 이미지를 image_path_list에 포함하여 상세페이지 생성 처리"""
    logger.debug(f"🛠️ 선택된 이미지 포함 상세페이지 생성 시작: {selected_image_path}")
    
    try:
        # config.yaml의 input 변수들 (product_data)
        product_data = st.session_state.get('processed_data', {}).copy()
        logger.debug(f"🛠️ 상품 데이터: {list(product_data.keys()) if product_data else 'None'}")
        
        # analysis_result에서 differences 추출
        analysis_result = st.session_state.get('analysis_result')
        differences = []
        if analysis_result and analysis_result.get('success') and 'data' in analysis_result:
            differences = analysis_result['data'].get('differences', [])
            logger.debug(f"🛠️ 추출된 차별점: {len(differences)}개")
        else:
            logger.warning("⚠️ 분석 결과에서 차별점을 찾을 수 없습니다")
        
        # 기존 사용자 업로드 이미지 경로 필터링 (backend/data/input/ 제외)
        existing_image_paths = product_data.get('image_path_list', [])
        filtered_paths = [
            path for path in existing_image_paths 
            if not path.startswith('backend/data/input/')
        ]
        
        logger.debug(f"🛠️ 기존 경로: {existing_image_paths}")
        logger.debug(f"🛠️ 필터링된 경로: {filtered_paths}")
        
        # 선택된 이미지를 추가 (중복 확인)
        if selected_image_path not in filtered_paths:
            filtered_paths.append(selected_image_path)
            logger.debug(f"🛠️ 선택된 이미지를 추가: {selected_image_path}")
        else:
            logger.debug("🛠️ 선택된 이미지가 이미 존재함")

        updated_image_paths = filtered_paths
        
        # 상세페이지 생성 API 호출용 데이터 구성
        generation_data = {
            **product_data,  # config.yaml의 input 변수들을 직접 펼쳐서 넘기기
            'image_path_list': updated_image_paths,  # 선택된 이미지가 포함된 리스트
            'difference': differences,  # analysis_result의 differences를 difference 키로 넘기기
            'selected_image_path': selected_image_path  # 선택된 이미지 경로 (참고용)
        }
        
        logger.debug(f"🛠️ 상세페이지 생성 데이터 구성 완료: {list(generation_data.keys())}")
        logger.debug(f"🛠️ 업데이트된 이미지 경로 수: {len(updated_image_paths)}")
        logger.debug(f"🛠️ 이미지 경로들: {updated_image_paths}")
        logger.debug(f"🛠️ 차별점 개수: {len(differences)}")
        
        with st.spinner("상세페이지 생성 중... (선택된 이미지 포함, 30초~1분 소요)"):
            result = generate_detail_page(generation_data)
            
            logger.debug(f"🛠️ 선택된 이미지 포함 상세페이지 생성 API 응답: {result}")
            
            if result and result.get('success'):
                logger.info("✅ 선택된 이미지 포함 상세페이지 생성 완료")
                
                # 결과를 세션에 저장 (백엔드 응답 형태에 맞게 수정)
                detail_result = result.get('data')
                if detail_result:
                    st.session_state.detail_page_result = detail_result
                    logger.debug(f"🛠️ 세션에 저장된 detail_page_result (선택 이미지 포함): {list(detail_result.keys()) if detail_result else 'None'}")
                    
                    st.success("🎉 상세페이지 생성이 완료되었습니다! (선택된 이미지 포함)")
                    st.info("📄 결과 페이지로 이동합니다...")
                    
                    # 결과 페이지로 이동
                    time.sleep(1)
                    st.switch_page("pages/result.py")
                else:
                    st.error("❌ 상세페이지 생성 결과 데이터가 없습니다.")
            else:
                error_msg = result.get('error', '알 수 없는 오류') if result else 'API 호출 실패'
                st.error(f"❌ 상세페이지 생성 실패: {error_msg}")
                
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

    # 🚀 비동기 상품 분석 처리
    handle_async_product_analysis()

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

    # 결합된 결과 (합성 + 분석) 표시
    if 'combined_results' in st.session_state:
        st.markdown("---")
        st.header("🎨 생성된 모든 결과")
        
        results = st.session_state.combined_results
        display_combined_results_selection(results)

    # 또는 composition_results (다중 결과)가 있는 경우
    if 'composition_results' in st.session_state:
        st.markdown("---")
        st.header("🎨 합성 결과들")
        
        results = st.session_state.composition_results
        display_multiple_results_selection(results)

if __name__ == "__main__":
    main()