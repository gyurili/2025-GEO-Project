from fastapi import APIRouter, HTTPException, Request
from backend.image_generator.schemas.input_schema import ImageGenRequest
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/image", tags=["Images"])

@router.post("/create")
async def generate_image(rqeust: Request, input_schema: ImageGenRequest):
    logger.debug(f"🛠️ {input_schema}")
    return