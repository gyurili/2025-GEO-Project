from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, List
import sys
from pathlib import Path

# 로거 임포트 추가
sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.logger import get_logger

from ..core.input_main import InputHandler
from ..schemas.input_schema import ProductInputSchema

# 로거 설정
logger = get_logger(__name__)

router = APIRouter(prefix="/api/input", tags=["input"])


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


@router.post("/process", response_model=Dict[str, Any])
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


@router.post("/process-multiple", response_model=Dict[str, Any])
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


@router.post("/process-json", response_model=Dict[str, Any])
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


@router.post("/validate", response_model=Dict[str, Any])
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


@router.get("/config", response_model=Dict[str, Any])
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


@router.get("/product", response_model=Dict[str, Any])
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


@router.post("/config/validate", response_model=Dict[str, Any])
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


@router.get("/health")
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