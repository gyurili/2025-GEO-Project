import yaml
import os
import torch

from utils.logger import get_logger
from backend.image_generator.image_generator_main import image_generator_main, vton_generator_main, ImgGenPipeline
from backend.image_generator.background_handler import BackgroundHandler
from backend.image_generator.image_loader import ImageLoader

logger = get_logger(__name__)

if __name__ == "__main__":
    try:
        logger.debug("🛠️ 테스트 시작")

        # ----------------------------------------------
        # 1. 제품이미지만 있는 경우에서 이미지에서 생성하는 버전
        logger.debug("🛠️ config.yaml 로드 시작")
        with open("config.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            logger.info("✅ config.yaml 로드 완료")
        
        product = config["input"]
        image_path = product["ip_image_path"]

        logger.debug("🛠️ 이미지 생성기 시작")
        image_generator = ImgGenPipeline()
        image_dict1 = image_generator.generate_image(
            product=product,
            image_path=image_path,
        )
        if image_dict1["image"]:
            logger.info("✅ 최종 이미지 생성 완료")
        else:
            logger.error("❌ 최종 이미지 생성 실패")

        image_dict2 = image_generator.generate_vton(
            product['model_image_path'],
            product['ip_image_path'],
            product['mask_image_path'],
        )
        if image_dict2["image"]:
            logger.info("✅ 최종 이미지 생성 완료")
        else:
            logger.error("❌ 최종 이미지 생성 실패")


        # # ----------------------------------------------
        # # 2. 모델 이미지에 제품 이미지를 착용하는 vton버전
        # logger.debug("🛠️ vton 생성 시작")
        # result = vton_generator_main(
        #     model_image_path="/home/user/2025-GEO-Project/backend/data/input/andrew-heald-Da7luWG-oGQ-unsplash_removed_bg.png",
        #     ip_image_path="/home/user/2025-GEO-Project/backend/data/input/footwear.jpg",
        #     mask_image_path="/home/user/2025-GEO-Project/backend/data/input/andrew-heald-Da7luWG-oGQ-unsplash_mask_shoes.jpg",
        #     seed=42
        # )
        # logger.info("✅ vton 생성 완료")


        # # ----------------------------------------------
        # # 3. 이미지 누끼 따기 및 마스크 만들기용
        # img_loader = ImageLoader()
        # img, filename = img_loader.load_image("/home/user/2025-GEO-Project/backend/data/input/andrew-heald-Da7luWG-oGQ-unsplash.jpg")
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