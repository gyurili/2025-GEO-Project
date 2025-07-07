import os
import sys

from utils.logger import get_logger
from .image_loader import ImageLoader
from .background_handler import BackgroundHandler

logger = get_logger(__name__)

def image_generator_main(
    input_image_path: str, 
    output_dir: str = "backend/data/output/",
    background_image_path: str = None,
    config: dict = None
):
    """
    이미지 제너레이터 메인
    """
    logger.debug(f"🛠️ 이미지 처리 시작")

    # 1. 이미지 로더
    image_loader = ImageLoader()
    loaded_image, filename = image_loader.load_image(image_path=input_image_path, target_size=None)

    if loaded_image is None:
        logger.error("❌ 이미지 로드에 실패했습니다. 처리를 중단합니다.")
        return False

    logger.info("✅ 이미지 로드 성공.")

    # 2 배경 제거
    logger.debug(f"🛠️ 배경 제거 시작")
    background_handler = BackgroundHandler()

    processed_image = background_handler.remove_background(
        input_image=loaded_image,
        original_filename=filename,
        output_dir=output_dir
    )

    if processed_image is None:
        logger.error("❌ 배경 제거에 실패했습니다. 처리를 중단합니다.")
        return False

    logger.info("✅ 배경 제거 및 저장 성공.")

    # 3. 단색 배경 추가
    logger.debug(f"🛠️ 단색 배경 추가 시작")
    image_with_color = background_handler.add_color_background(
        foreground_image=processed_image,
        color=(255, 255, 255),
        original_filename=filename,
        output_dir=output_dir
    )

    if image_with_color is None:
        logger.error("❌ 단색 배경 추가에 실패했습니다. 처리를 중단합니다.")
        return False

    logger.info("✅ 단색 배경 추가 및 저장 성공.")

        # 4. 이미지 배경 추가 (선택적 실행)
    if background_image_path:
        logger.debug(f"🛠️ 이미지 배경 추가 시작")
        bg_image, bg_filename = image_loader.load_image(
            image_path=background_image_path,
        )

        if bg_image is None:
            logger.error("❌ 배경 이미지 로드에 실패했습니다. 배경 합성을 건너뜁니다.")
        else:
            image_with_bg = background_handler.add_image_background(
                foreground_image=processed_image,
                background_image=bg_image,
                original_filename=filename,
                background_filename=bg_filename,
                output_dir=output_dir
            )
            if image_with_bg is None:
                logger.error("❌ 이미지 배경 추가에 실패했습니다. 처리를 중단합니다.")
            logger.info("✅ 이미지 배경 추가 및 저장 성공.")
    return True