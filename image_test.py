import yaml
import os
import torch

from utils.logger import get_logger
from backend.image_generator.image_generator_main import ImgGenPipeline
from backend.image_generator.background_handler import BackgroundHandler
from backend.image_generator.image_loader import ImageLoader

logger = get_logger(__name__)

if __name__ == "__main__":
    try:
        logger.debug("🛠️ 테스트 시작")

        # ----------------------------------------------
        # 1. 이미지 생성기 파이프라인
        logger.debug("🛠️ config.yaml 로드 시작")
        with open("config.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            logger.info("✅ config.yaml 로드 완료")
        
        product = config["input"]
        image_path = product["ip_image_path"]

        logger.debug("🛠️ 이미지 생성기 시작")
        image_generator = ImgGenPipeline()  # 클래스 변수 선언

        image_dict1 = image_generator.generate_image(
            product=product,
            image_path=image_path,
            seed=2,
        )
        if image_dict1["image"]:
            logger.info("✅ 최종 이미지 생성 완료")
        else:
            logger.error("❌ 최종 이미지 생성 실패")

        # image_dict2 = image_generator.generate_vton(
        #     product['model_image_path'],
        #     product['ip_image_path'],
        #     product['mask_image_path'],
        #     seed=42,
        # )
        # if image_dict2["image"]:
        #     logger.info("✅ 최종 이미지 생성 완료")
        # else:
        #     logger.error("❌ 최종 이미지 생성 실패")


        # # ----------------------------------------------
        # # 2. 이미지 누끼 따기 및 마스크 만들기용
        # img_loader = ImageLoader()
        # img, filename = img_loader.load_image("/home/user/2025-GEO-Project/backend/data/input/female_model.avif")
        # bg_handler = BackgroundHandler()
        # processed_image, save_path = bg_handler.remove_background(
        #     input_image=img,
        #     original_filename=filename,
        # )
        # mask_image, mask_path = bg_handler.create_mask_from_alpha(
        #     transparent_image=processed_image,
        #     original_filename=filename
        # )


    except Exception as e:
        logger.error(f"❌ 에러 발생: {e}")