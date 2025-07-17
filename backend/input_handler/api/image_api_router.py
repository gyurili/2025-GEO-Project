from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any
import sys
from pathlib import Path

# 로거 임포트 추가
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from utils.logger import get_logger

from ..core.image_composer import ImageComposer

# 로거 설정
logger = get_logger(__name__)

router = APIRouter(prefix="/api/image", tags=["image"])

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

@router.post("/compose")
async def compose_image(
    composition_data: Dict[str, Any],
    composer: ImageComposer = Depends(get_image_composer)
):
    """
    이미지 합성 API
    - 선택된 이미지들과 요청사항을 바탕으로 이미지 합성
    """
    logger.debug("🛠️ 이미지 합성 API 호출")
    logger.debug(f"🛠️ 합성 데이터: {list(composition_data.keys())}")
    
    try:
        # 필수 데이터 확인
        required_fields = ['user_image', 'target_image', 'generation_options']
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
            logger.info("✅ 이미지 합성 완료")
            response = {
                "success": True,
                "message": "이미지 합성이 완료되었습니다",
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
        # HTTPException은 그대로 재발생
        raise
    except Exception as e:
        logger.error(f"❌ 이미지 합성 API 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"이미지 합성 중 오류 발생: {str(e)}"
        )

@router.get("/health")
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