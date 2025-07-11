from fastapi import APIRouter, HTTPException, Request
from backend.image_generator.schemas.input_schema import ImageGenRequest
from backend.image_generator.image_generator_main import image_generator_main
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/image", tags=["Images"])

@router.post("/create", summary="Generate Product Image")
async def generate_image(rqeust: Request, input_schema: ImageGenRequest):
    logger.debug(f"🛠️ {input_schema}")
    
    try:
        product_info = {
            "name": input_schema.name,
            "category": input_schema.category,
            "price": input_schema.price,
            "features": input_schema.features
        }

        result = image_generator_main(
            product=product_info,
            image_path=input_schema.image_path
        )

        if result is False:
            raise HTTPException(status_code=500, detail="이미지 생성 실패")

        return {
            "message": "이미지 생성 성공",
            "image_path": result.get("image_path", "N/A"),
        }

    except Exception as e:
        logger.error(f"❌ 에러 발생: {e}")
        raise HTTPException(status_code=500, detail=f"서버 내부 에러: {str(e)}")