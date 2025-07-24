import os
import asyncio
from fastapi import FastAPI, APIRouter, Body, Form, Query
from fastapi.responses import JSONResponse, FileResponse

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from typing import Dict, Any, Optional, List
import sys
from pathlib import Path

# 로거 임포트 추가
from backend.input_handler.core.input_main import InputHandler
from backend.input_handler.schemas.input_schema import ProductInputSchema
from backend.input_handler.core.image_composer import ImageComposer

from utils.logger import get_logger
from backend.competitor_analysis.competitor_main import competitor_main
from backend.image_generator.image_generator_main import ImgGenPipeline
from backend.text_generator.text_generator_main import text_generator_main
from backend.page_generator.page_generator_main import page_generator_main

logger = get_logger(__name__)

input_router = APIRouter(prefix="/input", tags=["input"])
process_router = APIRouter(prefix="/process")
output_router = APIRouter(prefix="/output")

img_gen_pipeline = ImgGenPipeline()

# InputHandler 인스턴스 생성 (의존성 주입)
def get_input_handler() -> InputHandler:
    """InputHandler 인스턴스 반환"""
    logger.debug("🛠️ InputHandler 인스턴스 생성 시작")
    try:
        handler = InputHandler()
        logger.info("✅ InputHandler 인스턴스 생성 완료")
        return handler
    except Exception as e:
        logger.error(f"❌ InputHandler 인스턴스 생성 실패: {e}")
        raise

# ImageComposer 인스턴스 생성 (의존성 주입)
def get_image_composer() -> ImageComposer:
    """ImageComposer 인스턴스 반환"""
    logger.debug("🛠️ ImageComposer 인스턴스 생성 시작")
    try:
        composer = ImageComposer()
        logger.info("✅ ImageComposer 인스턴스 생성 완료")
        return composer
    except Exception as e:
        logger.error(f"❌ ImageComposer 인스턴스 생성 실패: {e}")
        raise


@input_router.post("/process", response_model=Dict[str, Any])
async def process_product_input(
    name: str = Form(..., description="상품명"),
    category: str = Form(..., description="카테고리"),
    price: int = Form(..., description="가격"),
    brand: str = Form(..., description="브랜드"),
    features: str = Form(..., description="상품 특징"),
    css_type: int = Form(..., description="CSS 타입"),
    image: Optional[UploadFile] = File(None, description="상품 이미지"),
    handler: InputHandler = Depends(get_input_handler)
):
    """
    상품 입력 데이터 처리 (단일 이미지)
    - 폼 데이터 검증
    - 이미지 업로드 처리
    - config.yaml 생성
    - product_input 딕셔너리 반환
    """
    logger.debug("🛠️ 상품 입력 데이터 처리 시작")
    logger.debug(f"🛠️ 요청 데이터: name={name}, category={category}, price={price}, brand={brand}")
    
    try:
        # 폼 데이터 구성
        logger.debug("🛠️ 폼 데이터 구성 중")
        form_data = {
            "name": name,
            "category": category,
            "price": price,
            "brand": brand,
            "features": features,
            "css_type": css_type
        }
        logger.debug(f"🛠️ 폼 데이터 구성 완료: {form_data}")
        
        # 입력 처리
        logger.debug("🛠️ InputHandler를 통한 상품 입력 처리 시작")
        uploaded_files = [image] if image else None
        product_input = handler.process_form_input(form_data, uploaded_files)
        logger.info("✅ 상품 입력 처리 완료")
        
        response = {
            "success": True,
            "message": "상품 입력 처리 완료",
            "data": product_input
        }
        logger.debug(f"🛠️ 응답 데이터 준비 완료: {len(str(response))} bytes")
        return response
        
    except Exception as e:
        logger.error(f"❌ 상품 입력 처리 실패: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"상품 입력 처리 중 오류 발생: {str(e)}"
        )


@input_router.post("/process-multiple", response_model=Dict[str, Any])
async def process_product_input_multiple(
    name: str = Form(..., description="상품명"),
    category: str = Form(..., description="카테고리"),
    price: int = Form(..., description="가격"),
    brand: str = Form(..., description="브랜드"),
    features: str = Form(..., description="상품 특징"),
    css_type: int = Form(..., description="CSS 타입"),
    images: List[UploadFile] = File(..., description="상품 이미지들 (다중)"),
    handler: InputHandler = Depends(get_input_handler)
):
    """
    상품 입력 데이터 처리 (다중 이미지)
    - 폼 데이터 검증
    - 다중 이미지 업로드 처리
    - config.yaml 생성
    - product_input 딕셔너리 반환
    """
    logger.debug("🛠️ 다중 이미지 상품 입력 데이터 처리 시작")
    logger.debug(f"🛠️ 요청 데이터: name={name}, category={category}, price={price}, brand={brand}")
    logger.debug(f"🛠️ 업로드된 이미지 수: {len(images)}")
    
    try:
        # 이미지 파일명 로그
        image_names = [img.filename for img in images if img.filename]
        logger.debug(f"🛠️ 업로드된 이미지 파일명: {image_names}")
        
        # 폼 데이터 구성
        logger.debug("🛠️ 폼 데이터 구성 중")
        form_data = {
            "name": name,
            "category": category,
            "price": price,
            "brand": brand,
            "features": features,
            "css_type": css_type
        }
        logger.debug(f"🛠️ 폼 데이터 구성 완료: {form_data}")
        
        # 입력 처리
        logger.debug("🛠️ InputHandler를 통한 다중 이미지 상품 입력 처리 시작")
        product_input = handler.process_form_input(form_data, images)
        logger.info("✅ 다중 이미지 상품 입력 처리 완료")
        
        response = {
            "success": True,
            "message": "다중 이미지 상품 입력 처리 완료",
            "data": product_input
        }
        logger.debug(f"🛠️ 응답 데이터 준비 완료: {len(str(response))} bytes")
        return response
        
    except Exception as e:
        logger.error(f"❌ 다중 이미지 상품 입력 처리 실패: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"다중 이미지 상품 입력 처리 중 오류 발생: {str(e)}"
        )


@input_router.post("/process-json", response_model=Dict[str, Any])
async def process_product_input_json(
    product_data: ProductInputSchema,
    handler: InputHandler = Depends(get_input_handler)
):
    """
    상품 입력 데이터 처리 (JSON, 이미지 없음)
    - JSON 데이터 검증
    - config.yaml 생성 (이미지 없이)
    - product_input 딕셔너리 반환
    """
    logger.debug("🛠️ JSON 상품 입력 데이터 처리 시작")
    logger.debug(f"🛠️ 요청 데이터: name={product_data.name}, category={product_data.category}")
    
    try:
        # 폼 데이터 구성
        logger.debug("🛠️ JSON 데이터를 폼 데이터로 변환 중")
        form_data = product_data.dict()
        logger.debug(f"🛠️ 변환된 폼 데이터: {form_data}")
        
        # 입력 처리 (이미지 없음)
        logger.debug("🛠️ InputHandler를 통한 JSON 상품 입력 처리 시작")
        product_input = handler.process_form_input(form_data, uploaded_files=None)
        logger.info("✅ JSON 상품 입력 처리 완료")
        
        response = {
            "success": True,
            "message": "JSON 상품 입력 처리 완료",
            "data": product_input
        }
        logger.debug(f"🛠️ 응답 데이터 준비 완료: {len(str(response))} bytes")
        return response
        
    except Exception as e:
        logger.error(f"❌ JSON 상품 입력 처리 실패: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"JSON 상품 입력 처리 중 오류 발생: {str(e)}"
        )


@input_router.post("/validate", response_model=Dict[str, Any])
async def validate_product_input(
    product_data: ProductInputSchema
):
    """
    상품 입력 데이터 검증만 수행
    """
    logger.debug("🛠️ 상품 입력 데이터 검증 시작")
    logger.debug(f"🛠️ 검증할 데이터: name={product_data.name}, category={product_data.category}")
    
    try:
        validated_data = product_data.dict()
        logger.info("✅ 상품 데이터 검증 완료")
        
        response = {
            "success": True,
            "message": "상품 데이터 검증 완료",
            "data": validated_data
        }
        logger.debug(f"🛠️ 검증 응답 데이터 준비 완료")
        return response
        
    except Exception as e:
        logger.error(f"❌ 상품 데이터 검증 실패: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"상품 데이터 검증 실패: {str(e)}"
        )


@input_router.get("/config", response_model=Dict[str, Any])
async def get_config(
    handler: InputHandler = Depends(get_input_handler)
):
    """
    현재 config.yaml 설정 반환
    """
    logger.debug("🛠️ config.yaml 설정 로드 시작")
    
    try:
        config = handler.load_config()
        logger.info("✅ config.yaml 설정 로드 완료")
        
        response = {
            "success": True,
            "message": "설정 로드 완료",
            "data": config
        }
        logger.debug(f"🛠️ 설정 데이터 응답 준비 완료")
        return response
        
    except Exception as e:
        logger.error(f"❌ 설정 파일 로드 실패: {e}")
        raise HTTPException(
            status_code=404,
            detail=f"설정 파일 로드 실패: {str(e)}"
        )


@input_router.get("/product", response_model=Dict[str, Any])
async def get_product_input(
    handler: InputHandler = Depends(get_input_handler)
):
    """
    config.yaml에서 product_input 딕셔너리 반환
    """
    logger.debug("🛠️ config.yaml에서 상품 입력 데이터 로드 시작")
    
    try:
        product_input = handler.get_product_input_dict()
        logger.info("✅ 상품 입력 데이터 로드 완료")
        
        response = {
            "success": True,
            "message": "상품 입력 데이터 로드 완료",
            "data": product_input
        }
        logger.debug(f"🛠️ 상품 데이터 응답 준비 완료")
        return response
        
    except Exception as e:
        logger.error(f"❌ 상품 입력 데이터 로드 실패: {e}")
        raise HTTPException(
            status_code=404,
            detail=f"상품 입력 데이터 로드 실패: {str(e)}"
        )


@input_router.post("/config/validate", response_model=Dict[str, Any])
async def validate_config(
    handler: InputHandler = Depends(get_input_handler)
):
    """
    현재 config.yaml 유효성 검증
    """
    logger.debug("🛠️ config.yaml 유효성 검증 시작")
    
    try:
        is_valid = handler.validate_existing_config()
        
        if is_valid:
            logger.info("✅ 설정 파일 검증 완료 - 유효함")
        else:
            logger.warning("⚠️ 설정 파일 검증 완료 - 유효하지 않음")
        
        response = {
            "success": True,
            "message": "설정 파일 검증 완료",
            "data": {"is_valid": is_valid}
        }
        logger.debug(f"🛠️ 검증 결과 응답 준비 완료: is_valid={is_valid}")
        return response
        
    except Exception as e:
        logger.error(f"❌ 설정 파일 검증 실패: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"설정 파일 검증 실패: {str(e)}"
        )


@input_router.get("/health")
async def health_check():
    """
    API 상태 확인
    """
    logger.debug("🛠️ Input Handler API 상태 확인 시작")
    
    try:
        response = {
            "success": True,
            "message": "Input Handler API 정상 작동 중",
            "service": "input_handler"
        }
        logger.info("✅ Input Handler API 상태 확인 완료 - 정상")
        return response
        
    except Exception as e:
        logger.error(f"❌ API 상태 확인 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"API 상태 확인 실패: {str(e)}"
        )

@input_router.post("/compose")
async def compose_image(
    composition_data: Dict[str, Any],
    composer: ImageComposer = Depends(get_image_composer)
):
    """
    이미지 합성 API (다중 상품 이미지 → 단일 결과)
    """
    logger.debug("🛠️ 이미지 합성 API 호출")
    
    # user_images와 user_image 둘 다 지원 (하위 호환성)
    user_images = composition_data.get('user_images', [])
    if not user_images and 'user_image' in composition_data:
        user_images = [composition_data['user_image']]
        composition_data['user_images'] = user_images
    
    logger.debug(f"🛠️ 합성 데이터: {list(composition_data.keys())}")
    logger.debug(f"🛠️ 상품 이미지 수: {len(user_images)}")
    
    try:
        # 필수 데이터 확인
        required_fields = ['user_images', 'target_image', 'generation_options']
        missing_fields = [field for field in required_fields if field not in composition_data]
        
        if missing_fields:
            logger.error(f"❌ 필수 필드 누락: {missing_fields}")
            raise HTTPException(
                status_code=400,
                detail=f"필수 필드가 누락되었습니다: {missing_fields}"
            )
        
        # 이미지 합성 실행
        logger.debug("🛠️ ImageComposer를 통한 이미지 합성 시작")
        result = composer.compose_images(composition_data)
        
        if result:
            logger.info(f"✅ 이미지 합성 완료 ({result.get('product_images_count', 1)}개 상품)")
            response = {
                "success": True,
                "message": f"이미지 합성이 완료되었습니다 ({result.get('product_images_count', 1)}개 상품)",
                "data": result
            }
            return response
        else:
            logger.error("❌ 이미지 합성 실패")
            raise HTTPException(
                status_code=500,
                detail="이미지 합성에 실패했습니다"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 이미지 합성 API 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"이미지 합성 중 오류 발생: {str(e)}"
        )

@input_router.get("/image-health")
async def health_check():
    """
    이미지 생성 API 상태 확인
    """
    logger.debug("🛠️ 이미지 생성 API 상태 확인")
    
    try:
        response = {
            "success": True,
            "message": "Image Generator API 정상 작동 중",
            "service": "image_generator"
        }
        logger.info("✅ 이미지 생성 API 상태 확인 완료")
        return response
        
    except Exception as e:
        logger.error(f"❌ API 상태 확인 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"API 상태 확인 실패: {str(e)}"
        )

# ---- 1. process 라우터: 차별점+후보이미지 ----
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
    logger.debug(f"🛠️ 입력 product 타입: {type(product)}")
    logger.debug(f"🛠️ 입력 product 키: {list(product.keys()) if isinstance(product, dict) else 'NOT_DICT'}")
    
    try:
        # 병렬 작업 실행
        logger.debug("🛠️ 차별점 분석 및 이미지 생성 병렬 작업 시작")
        competitor_task = competitor_main(product)
        img_gen_task = asyncio.to_thread(
            img_gen_pipeline.generate_image, product
        )
        
        # gather 결과 수신
        results = await asyncio.gather(competitor_task, img_gen_task)
        diff_result = results[0]  # competitor_main 결과
        candidate_images_result = results[1]  # img_gen_pipeline.generate_image 결과
        
        logger.debug(f"🛠️ diff_result 타입: {type(diff_result)}")
        logger.debug(f"🛠️ diff_result 내용: {diff_result}")
        logger.debug(f"🛠️ candidate_images_result 타입: {type(candidate_images_result)}")
        logger.debug(f"🛠️ candidate_images_result 내용: {candidate_images_result}")

        # 차별점 product dict에 추가 (안전한 처리)
        if isinstance(diff_result, dict) and 'differences' in diff_result:
            product['differences'] = diff_result['differences']
            logger.debug(f"🛠️ 차별점 추가 완료: {len(product['differences'])}개")
        elif isinstance(diff_result, dict):
            logger.warning(f"⚠️ diff_result가 딕셔너리이지만 'differences' 키가 없음: {diff_result}")
            product['differences'] = []
        else:
            logger.warning(f"⚠️ diff_result가 예상과 다른 형태: {type(diff_result)} - {diff_result}")
            product['differences'] = []

        # 후보 이미지 처리 (안전한 처리)
        try:
            if candidate_images_result and isinstance(candidate_images_result, dict):
                # generate_image() 반환값: {"image_paths": [path1, path2, ...]}
                image_paths = candidate_images_result.get("image_paths", [])
                if image_paths:
                    product['candidate_images'] = [image_paths]  # 리스트 안에 리스트 형태
                    logger.debug(f"🛠️ 후보 이미지 처리 완료: {len(image_paths)}개 이미지")
                    logger.debug(f"🛠️ 이미지 경로들: {image_paths}")
                else:
                    product['candidate_images'] = [[]]
                    logger.warning("⚠️ image_paths가 비어있음")
            elif candidate_images_result and isinstance(candidate_images_result, list):
                # 혹시 리스트 형태로 반환되는 경우 대비
                product['candidate_images'] = [candidate_images_result]
                logger.debug(f"🛠️ 후보 이미지 처리 완료 (리스트): {len(candidate_images_result)}개 이미지")
            else:
                logger.warning(f"⚠️ candidate_images_result가 예상과 다른 형태: {type(candidate_images_result)} - {candidate_images_result}")
                product['candidate_images'] = [[]]
        except Exception as img_error:
            logger.error(f"❌ 후보 이미지 처리 중 오류: {img_error}")
            import traceback
            logger.error(f"❌ 스택 트레이스: {traceback.format_exc()}")
            product['candidate_images'] = [[]]

        logger.info("✅ 상품입력/차별점/이미지 생성 병렬 처리 완료")
        logger.debug(f"🛠️ 최종 product 키: {list(product.keys())}")
        
        return {
            "success": True,
            "data": product
        }
        
    except Exception as e:
        logger.error(f"❌ receive_product_info 예외: {e}")
        logger.error(f"❌ 예외 타입: {type(e)}")
        import traceback
        logger.error(f"❌ 스택 트레이스: {traceback.format_exc()}")
        return {"success": False, "error": str(e)}

# ---- 3. output 라우터: 상세페이지 생성 ----
@output_router.post(
    "/create-page",
    summary="상세페이지 생성",
    description="선택된 이미지 및 분석 데이터를 기반으로 텍스트 생성과 HTML 상세페이지를 생성하며, session_id를 반환합니다."
)
def generate_detail_page(
    product: Dict[str, Any] = Body(...)
) -> Dict[str, Any]:
    """
    차별점/선택이미지 포함 product dict → 텍스트/상세페이지 생성 + session_id 추가
    """
    logger.debug("🛠️ generate_detail_page 진입")
    try:
        # text_generator_main은 product 딕셔너리 전체를 반환하고, session_id가 추가됨
        updated_product = text_generator_main(product)
        session_id = updated_product.get("session_id")
        
        if not session_id:
            logger.error("❌ session_id가 생성되지 않았습니다")
            return {"success": False, "error": "session_id 생성 실패"}
        
        logger.debug(f"🛠️ 생성된 session_id: {session_id}")
        
        # page_generator_main에 업데이트된 product 전달
        page_generator_main(updated_product)
        
        logger.info(f"✅ 상세페이지 생성 완료 (session_id={session_id})")
        return {"success": True, "data": updated_product}
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