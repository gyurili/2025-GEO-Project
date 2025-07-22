from fastapi import FastAPI, APIRouter, Body, Form
from fastapi.responses import JSONResponse, FileResponse
from typing import Dict, Any, Optional, List
import asyncio

from utils.logger import get_logger
logger = get_logger(__name__)

from backend.competitor_analysis.competitor_main import competitor_main
from backend.image_generator.image_generator_main import image_generator_main, vton_generator_main
from backend.text_generator.text_generator_main import text_generator_main
from backend.page_generator.page_generator_main import page_generator_main

app = FastAPI()

input_router = APIRouter(prefix="/input")
image_router = APIRouter(prefix="/image")
output_router = APIRouter(prefix="/output")

# ---- 전역 상태 (데모/PoC용, 실서비스는 세션·DB 추천) ----
latest_image_gen_result: Dict[str, Optional[List[str]]] = {"candidate_images": None}
selected_image_idx: Optional[int] = None
latest_diff_result: Optional[Dict[str, Any]] = None
latest_detail_page_html: Optional[str] = None
latest_detail_page_path: str = "backend/data/result/detail_page.html"
latest_product: Optional[Dict[str, Any]] = None

# ---- 비동기 이미지 생성 ----
async def async_diffusion_gen(product: dict) -> str:
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, lambda: image_generator_main(
        product, product["image_path"], prompt_mode="human"
    ))
    return result["image_path"] if result and result.get("image_path") else None

async def async_vton_gen(product: dict) -> str:
    model_image_path = product.get("model_image_path", "backend/data/input/model.jpg")
    mask_image_path = product.get("mask_image_path", None)
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, lambda: vton_generator_main(
        model_image_path, product["image_path"], mask_image_path
    ))
    return result["image_path"] if result and result.get("image_path") else None

# ---- 1. input 라우터 ----
@input_router.post("/")
async def receive_product_info(
    req: Dict[str, Any] = Body(...)
) -> Dict[str, Any]:
    """
    상품 dict(JSON Body) 받아 Diffusion+VTON 후보 이미지 각 1장 및 차별점 분석 병렬 처리
    """
    logger.debug("🛠️ receive_product_info 진입 - dict/Body 기반")
    global latest_image_gen_result, latest_diff_result, latest_product

    product = req["input"]
    latest_product = product
    try:
        competitor_task = competitor_main(product)
        diffusion_task = async_diffusion_gen(product)
        vton_task = async_vton_gen(product)

        diff_result, img1, img2 = await asyncio.gather(
            competitor_task, diffusion_task, vton_task
        )
        candidate_images = [img for img in [img1, img2] if img]

        latest_image_gen_result["candidate_images"] = candidate_images
        latest_diff_result = diff_result

        logger.info("✅ 상품 입력/차별점/후보 이미지 2종 병렬 처리 완료")
        return {
            "success": True,
            "diff_result": diff_result,
            "image_gen_result": {"candidate_images": candidate_images}
        }
    except Exception as e:
        logger.error(f"❌ receive_product_info 처리 중 예외: {e}")
        return {"success": False, "error": str(e)}

# ---- 2. image 라우터 (후보 이미지 조회/선택) ----
@image_router.get("/")
async def get_candidate_images() -> Dict[str, Any]:
    """
    후보 이미지 2장 경로 반환
    """
    logger.debug("🛠️ get_candidate_images 진입")
    candidates = latest_image_gen_result.get("candidate_images")
    if not candidates:
        logger.warning("⚠️ 후보 이미지 없음")
        return JSONResponse({"success": False, "error": "No candidate images"}, status_code=404)
    logger.info("✅ 후보 이미지 2개 반환 성공")
    return {"success": True, "candidates": candidates}

@image_router.post("/")
async def select_image(selection: int = Form(...)) -> Dict[str, Any]:
    """
    사용자가 선택한 후보 이미지(1,2) 기록 (FormData: selection=1 or 2)
    """
    logger.debug(f"🛠️ select_image 진입 - 선택값: {selection}")
    global selected_image_idx
    candidates = latest_image_gen_result.get("candidate_images")
    if not candidates:
        logger.warning("⚠️ 후보 이미지 없음 - 선택 기록 실패")
        return {"success": False, "error": "No candidate images"}
    if selection not in [1, 2]:
        logger.warning(f"⚠️ 잘못된 선택값: {selection}")
        return {"success": False, "error": "Invalid selection"}
    selected_image_idx = selection - 1
    selected_path = candidates[selected_image_idx]
    logger.info(f"✅ 이미지 선택 기록: {selected_path}")
    return {"success": True, "selected_image": selected_path}

# ---- 3. output 라우터 (상세페이지 생성/조회) ----
@output_router.post("/")
async def generate_detail_page() -> Dict[str, Any]:
    """
    차별점, 선택이미지 기반 텍스트 생성 및 상세페이지 생성 (전체 파이프라인)
    """
    logger.debug("🛠️ generate_detail_page 진입")
    global latest_detail_page_html, latest_detail_page_path, latest_product

    try:
        product = latest_product
        if not product:
            logger.error("❌ 상품 정보 없음")
            return {"success": False, "error": "상품 정보 없음"}

        # 차별점 분석 (다시 필요하면 실행)
        differences = []
        if latest_diff_result:
            differences = latest_diff_result.get("differences", [])
        if not differences:
            differences = await competitor_main(product)

        # 텍스트 상세페이지 생성
        output_path = "backend/data/output"
        session_id = text_generator_main(product, differences, output_path)

        # 최종 상세페이지 생성
        page_generator_main(product, session_id)

        # 선택 이미지
        candidates = latest_image_gen_result.get("candidate_images")
        selected_image = None
        if candidates and selected_image_idx is not None:
            selected_image = candidates[selected_image_idx]

        msg = f"상세페이지 전체 생성 완료 (session_id={session_id})"
        logger.info(f"✅ {msg}")
        return {
            "success": True,
            "session_id": session_id,
            "differences": differences,
            "selected_image": selected_image,
            "msg": msg
        }
    except Exception as e:
        logger.error(f"❌ generate_detail_page 예외: {e}")
        return {"success": False, "error": str(e)}

@output_router.get("/")
async def get_detail_page():
    """
    최종 상세페이지 HTML 반환 (파일이 없으면 404)
    """
    logger.debug("🛠️ get_detail_page 진입")
    try:
        return FileResponse(
            latest_detail_page_path,
            media_type="text/html"
        )
    except FileNotFoundError:
        logger.warning("⚠️ 상세페이지 파일 없음")
        return JSONResponse({"success": False, "error": "상세페이지 없음"}, status_code=404)

# ---- 앱 라우터 등록 ----
app.include_router(input_router)
app.include_router(image_router)
app.include_router(output_router)