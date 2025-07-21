import os
import asyncio
from fastapi import FastAPI, APIRouter, Body, Form, Query
from fastapi.responses import JSONResponse, FileResponse
from typing import Dict, Any, List

from utils.logger import get_logger
from backend.competitor_analysis.competitor_main import competitor_main
from backend.image_generator.image_generator_main import ImgGenPipeline
from backend.text_generator.text_generator_main import text_generator_main
from backend.page_generator.page_generator_main import page_generator_main

logger = get_logger(__name__)
app = FastAPI()

process_router = APIRouter(prefix="/process")
image_router = APIRouter(prefix="/image")
output_router = APIRouter(prefix="/output")

img_gen_pipeline = ImgGenPipeline()

# ---- 1. input 라우터: 차별점+후보이미지 ----
@process_router.post(
    "/analyze-product",
    summary="상품 분석 및 이미지 생성",
    description="상품 정보를 받아 경쟁사 리뷰 분석 및 차별점 도출, 그리고 후보 이미지(최대 2개) 생성을 병렬로 처리합니다."
)
async def receive_product_info(
    product: Dict[str, Any] = Body(...)
) -> Dict[str, Any]:
    """
    상품 dict 입력 → 차별점 도출 + 후보 이미지(최대 2개) 생성 → 상태 dict(딕셔너리)에 누적
    """
    logger.debug("🛠️ receive_product_info 진입")
    try:
        competitor_task = competitor_main(product)
        img_gen_task = asyncio.to_thread(
            img_gen_pipeline.generate_image, product, product["image_path_list"]
        )
        diff_result, candidate_images_result = await asyncio.gather(
            competitor_task, img_gen_task
        )

        # 차별점 product dict에 추가
        product['differences'] = diff_result.get('differences', []) if isinstance(diff_result, dict) else diff_result

        # 후보 이미지(리스트, 내부도 리스트!) 추가
        if candidate_images_result:
            image_paths = [res["image_path"] for res in candidate_images_result if "image_path" in res]
            product['candidate_images'] = [image_paths] if image_paths else [[]]
        else:
            product['candidate_images'] = [[]]

        # 선택 이미지도 빈 리스트로 추가(아직 미선택)
        product['selected_image_path'] = []
        logger.info("✅ 상품입력/차별점/이미지 생성 병렬 처리 완료")
        return product
    except Exception as e:
        logger.error(f"❌ receive_product_info 예외: {e}")
        return {"success": False, "error": str(e)}

# ---- 2. image 라우터: 후보 이미지 확인/선택 ----
@image_router.get(
    "/candidates",
    summary="후보 이미지 목록 조회",
    description="이미 분석된 상품 데이터에서 생성된 후보 이미지 리스트를 반환합니다. 항상 2개씩 중첩 리스트로 반환됩니다."
)
async def get_candidate_images(
    product: Dict[str, Any] = Body(...)
) -> Dict[str, Any]:
    """
    후보 이미지(항상 [[img1, img2],[img1, img2]]) 반환 (딕셔너리 상태로 받음)
    """
    logger.debug("🛠️ get_candidate_images 진입")
    candidates = product.get("candidate_images")
    if not candidates or not any(candidates[0]):
        logger.warning("⚠️ 후보 이미지 없음")
        return JSONResponse({"success": False, "error": "No candidate images"}, status_code=404)
    logger.info("✅ 후보 이미지 반환")
    return {"success": True, "candidate_images": candidates}

@image_router.post(
    "/select-image",
    summary="후보 이미지 선택",
    description="사용자가 선택한 이미지 인덱스(1 또는 2)를 상품 딕셔너리에 반영합니다. 선택값은 Form 형식으로 받습니다."
)
async def select_image(
    product: Dict[str, Any] = Body(...),
    selection: int = Form(...)
) -> Dict[str, Any]:
    """
    사용자가 선택한 이미지(1 or 2) 기록 (딕셔너리 상태 업데이트)
    """
    logger.debug(f"🛠️ select_image 진입 - 선택값: {selection}")
    candidates = product.get("candidate_images")
    if not candidates or not any(candidates[0]):
        logger.warning("⚠️ 후보 이미지 없음")
        return {"success": False, "error": "No candidate images"}
    if selection not in [1, 2]:
        logger.warning(f"⚠️ 잘못된 선택값: {selection}")
        return {"success": False, "error": "Invalid selection"}

    selected_image = candidates[selection-1]
    product["selected_image_path"] = selected_image  # 리스트로 저장
    logger.info(f"✅ 이미지 선택 기록: {selected_image}")
    return product

# ---- 3. output 라우터: 상세페이지 생성 ----
@output_router.post(
    "/create-page",
    summary="상세페이지 생성",
    description="선택된 이미지 및 분석 데이터를 기반으로 텍스트 생성과 HTML 상세페이지를 생성하며, session_id를 반환합니다."
)
async def generate_detail_page(
    product: Dict[str, Any] = Body(...)
) -> Dict[str, Any]:
    """
    차별점/선택이미지 포함 product dict → 텍스트/상세페이지 생성 + session_id 추가
    """
    logger.debug("🛠️ generate_detail_page 진입")
    try:
        output_path = "backend/data/result"
        session_id = text_generator_main(product, output_path)
        page_generator_main(product, session_id)
        product["session_id"] = session_id
        logger.info(f"✅ 상세페이지 생성 완료 (session_id={session_id})")
        return product
    except Exception as e:
        logger.error(f"❌ generate_detail_page 예외: {e}")
        return {"success": False, "error": str(e)}

@output_router.get(
    "/path",
    summary="생성된 상세페이지 경로 조회",
    description="session_id를 통해 생성된 상세페이지의 HTML과 PNG 파일 경로를 반환합니다."
)
async def get_detail_page(
    product: Dict[str, Any] = Body(...)
):
    """
    session_id로 결과 파일(html+png) 경로 반환
    """
    session_id = product["session_id"]
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

@output_router.get(
    "/download",
    summary="상세페이지 파일 다운로드",
    description="session_id와 파일 타입(html 또는 png)을 기반으로 생성된 상세페이지 결과물을 다운로드합니다."
)
async def download_detail_file(
    product: Dict[str, Any] = Body(...),
    file_type: str = Query(..., description="html 또는 png")
):
    """
    session_id 기반 상세페이지 파일 다운로드 (html/png)
    """
    session_id = product["session_id"]
    result_dir = "backend/data/result"
    ext = ".html" if file_type == "html" else ".png"
    file_path = os.path.join(result_dir, f"page_{session_id}{ext}")
    if not os.path.isfile(file_path):
        return JSONResponse({"success": False, "error": f"{file_type} 파일 없음"}, status_code=404)
    return FileResponse(file_path, filename=os.path.basename(file_path))

# ---- 앱 라우터 등록 ----
app.include_router(process_router)
app.include_router(image_router)
app.include_router(output_router)