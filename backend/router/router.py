import os
import asyncio
from fastapi import FastAPI, APIRouter, Body, Form, Query
from fastapi.responses import JSONResponse, FileResponse
from typing import Dict, Any, Optional, List

from utils.logger import get_logger
from backend.competitor_analysis.competitor_main import competitor_main
from backend.image_generator.image_generator_main import ImgGenPipeline
from backend.text_generator.text_generator_main import text_generator_main
from backend.page_generator.page_generator_main import page_generator_main

logger = get_logger(__name__)

app = FastAPI()

input_router = APIRouter(prefix="/input")
image_router = APIRouter(prefix="/image")
output_router = APIRouter(prefix="/output")

# ---- 전역 상태 (PoC용, 실서비스는 세션/DB 권장) ----
latest_product: Optional[Dict[str, Any]] = None
latest_result: Optional[Dict[str, Any]] = None
latest_session_id: Optional[str] = None

# 이미지 생성 파이프라인 인스턴스 (한번만 생성, 속도 최적화)
img_gen_pipeline = ImgGenPipeline()

# ---- 1. input 라우터 ----
@input_router.post("/")
async def receive_product_info(
    product: Dict[str, Any] = Body(...)
) -> Dict[str, Any]:
    """
    상품 dict(JSON Body) 받아 후보 이미지(최대 2개) 생성 + 차별점 분석(병렬)
    반환값: product dict + differences(List[str]) + candidate_images(List[List[str]])
    """
    logger.debug("🛠️ receive_product_info 진입 - 상품 딕셔너리 입력")
    global latest_product, latest_result, latest_session_id

    latest_product = product
    try:
        # 경쟁사 분석 & 이미지 생성 병렬 실행
        competitor_task = competitor_main(product)
        # 이미지 path 리스트로 넘겨주기 (최대 2개)
        img_gen_task = asyncio.to_thread(
            img_gen_pipeline.generate_image, product, product["image_path_list"]
        )

        diff_result, candidate_images_result = await asyncio.gather(
            competitor_task, img_gen_task
        )

        # 차별점 product dict에 추가
        product['differences'] = diff_result.get('differences', []) if isinstance(diff_result, dict) else diff_result

        # 후보 이미지 경로 product dict에 추가
        if candidate_images_result:
            image_paths = [res["image_path"] for res in candidate_images_result if "image_path" in res]
            product['candidate_images'] = [image_paths]
        else:
            product['candidate_images'] = [[]]

        # (선택된 이미지 경로는 아직 없음)
        product['selected_image_path'] = []

        # 결과 보관 (session_id는 아직 X)
        latest_result = product

        logger.info("✅ 상품입력/차별점/이미지 생성 병렬 처리 완료")
        return product
    except Exception as e:
        logger.error(f"❌ receive_product_info 처리 중 예외: {e}")
        return {"success": False, "error": str(e)}

# ---- 2. image 라우터 (후보 이미지 조회/선택) ----
@image_router.get("/")
async def get_candidate_images() -> Dict[str, Any]:
    """
    후보 이미지 리스트 반환 (항상 [ [img1, img2] ] 구조)
    """
    logger.debug("🛠️ get_candidate_images 진입")
    if not latest_result or not latest_result.get("candidate_images"):
        logger.warning("⚠️ 후보 이미지 없음")
        return JSONResponse({"success": False, "error": "No candidate images"}, status_code=404)
    logger.info("✅ 후보 이미지 반환")
    return {"success": True, "candidate_images": latest_result["candidate_images"]}

@image_router.post("/")
async def select_image(selection: int = Form(...)) -> Dict[str, Any]:
    """
    사용자가 선택한 이미지(1 or 2) 기록. selected_image_path에 반영
    """
    logger.debug(f"🛠️ select_image 진입 - 선택값: {selection}")
    global latest_result
    if not latest_result or not latest_result.get("candidate_images"):
        logger.warning("⚠️ 후보 이미지 없음 - 선택 기록 실패")
        return {"success": False, "error": "No candidate images"}
    if selection not in [1, 2]:
        logger.warning(f"⚠️ 잘못된 선택값: {selection}")
        return {"success": False, "error": "Invalid selection"}
    # 항상 단일 묶음만 있음
    selected_image = latest_result["candidate_images"][selection - 1]
    if not selected_image:
        logger.warning("⚠️ 선택된 이미지 경로 없음")
        return {"success": False, "error": "Selected image does not exist"}

    latest_result["selected_image_path"] = selected_image
    logger.info(f"✅ 이미지 선택 기록: {selected_image}")
    return {"success": True, "selected_image_path": latest_result["selected_image_path"]}

# ---- 3. output 라우터 (상세페이지 생성/조회) ----
@output_router.post("/")
async def generate_detail_page() -> Dict[str, Any]:
    """
    차별점, 선택이미지 포함 product dict → 텍스트+상세페이지 생성, session_id 포함 반환
    """
    logger.debug("🛠️ generate_detail_page 진입")
    global latest_result, latest_session_id
    try:
        product = latest_result
        if not product:
            logger.error("❌ 상품 정보 없음")
            return {"success": False, "error": "상품 정보 없음"}

        # 텍스트 상세페이지 생성 (session_id 반환)
        output_path = "backend/data/result"
        session_id = text_generator_main(product, output_path)

        # 상세페이지(HTML+PNG) 생성
        page_generator_main(product, session_id)

        product['session_id'] = session_id  # 반환값에 포함
        latest_result = product
        logger.info(f"✅ 상세페이지 전체 생성 완료 (session_id={session_id})")
        return product
    except Exception as e:
        logger.error(f"❌ generate_detail_page 예외: {e}")
        return {"success": False, "error": str(e)}

@output_router.get("/")
async def get_detail_page(
    session_id: str = Query(..., description="생성된 상세페이지 session_id")
):
    """
    session_id로 결과 파일(html+png) 경로 반환. (프론트는 이 경로로 직접 FileResponse 호출 가능)
    """
    logger.debug(f"🛠️ get_detail_page 진입 - session_id={session_id}")
    result_dir = "backend/data/result"
    html_path = os.path.join(result_dir, f"page_{session_id}.html")
    image_path = os.path.join(result_dir, f"page_{session_id}.png")

    if not os.path.isfile(html_path) or not os.path.isfile(image_path):
        logger.warning(f"⚠️ 결과 파일 없음: {html_path}, {image_path}")
        return JSONResponse({"success": False, "error": "상세페이지 결과 없음"}, status_code=404)
    return {
        "success": True,
        "html_path": html_path,
        "image_path": image_path
    }

@output_router.get("/download")
async def download_detail_file(
    session_id: str = Query(...),
    file_type: str = Query(..., description="html 또는 png")
):
    """
    session_id 기반 상세페이지 파일 다운로드 (html/png)
    """
    result_dir = "backend/data/result"
    ext = ".html" if file_type == "html" else ".png"
    file_path = os.path.join(result_dir, f"page_{session_id}{ext}")

    if not os.path.isfile(file_path):
        return JSONResponse({"success": False, "error": f"{file_type} 파일 없음"}, status_code=404)
    return FileResponse(file_path, filename=os.path.basename(file_path))

# ---- 앱 라우터 등록 ----
app.include_router(input_router)
app.include_router(image_router)
app.include_router(output_router)