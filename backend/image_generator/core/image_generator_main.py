import os
import sys

from utils.logger import get_logger
from .image_loader import ImageLoader
from .background_remover import BackgroundRemover

logger = get_logger(__name__)

def image_generator_main(
    input_image_path: str, 
    output_dir: str = "backend/data/output/",
    config: dict = None
):
    """
    이미지 제너레이터 메인
    """
    logger.debug(f"🛠️ 이미지 처리 시작")

    # 1. 이미지 로더
    image_loader = ImageLoader()
    loaded_image = image_loader.load_image(image_path=input_image_path, target_size=None)

    if loaded_image is None:
        logger.error("❌ 이미지 로드에 실패했습니다. 처리를 중단합니다.")
        return False

    logger.info("✅ 이미지 로드 성공.")

    # 2 배경 제거
    logger.debug(f"🛠️ 배경 제거 시작")
    background_remover = BackgroundRemover()

    processed_image = background_remover.remove_background(
        input_image=loaded_image,
        original_input_path=input_image_path,
        output_dir=output_dir
    )

    if processed_image is None:
        logger.error("❌ 배경 제거에 실패했습니다. 처리를 중단합니다.")
        return False

    logger.info("✅ 배경 제거 및 저장 성공.")
    return True