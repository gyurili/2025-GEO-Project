import yaml
import os
import torch

from utils.logger import get_logger
from backend.image_generator.image_generator_main import image_generator_main, vton_generator_main

from backend.image_generator.background_handler import BackgroundHandler
from backend.image_generator.image_loader import ImageLoader

logger = get_logger(__name__)

if __name__ == "__main__":
    try:
        logger.debug("🛠️ 테스트 시작")

        # ----------------------------------------------
        # 1. 제품이미지만 있는 경우에서 이미지에서 생성하는 버전
        # logger.debug("🛠️ config.yaml 로드 시작")
        # with open("config.yaml", "r", encoding="utf-8") as f:
        #     config = yaml.safe_load(f)
        #     logger.info("✅ config.yaml 로드 완료")
        
        # product = config["input"]
        # image_path = product["image_path"]

        # 제품 정보만으로 마스킹을 구별하는지 확인을 위한 시험용 함수
        # from backend.image_generator.core.prompt_builder import classify_product
        # classify_product(product)

        # logger.debug("🛠️ 이미지 생성기 시작")
        # image = image_generator_main(
        #     product=product, 
        #     image_path=image_path,
        #     model_id="SG161222/RealVisXL_V4.0",
        #     ip_adapter_scale=0.55,
        #     num_inference_steps=99,
        #     guidance_scale=7.5,
        # )

        # if image["image"]:
        #     logger.info("✅ 최종 이미지 생성 완료")
        # else:
        #     logger.error("❌ 최종 이미지 생성 실패")


        # ----------------------------------------------
        # 2. 모델 이미지에 제품 이미지를 착용하는 vton버전
        logger.debug("🛠️ vton 생성 시작")
        result = vton_generator_main(
            model_image_path="/home/user/2025-GEO-Project/backend/data/output/a_man_posing_wearing_a_parakeet_t-shirt_removed_bg.png",
            ip_image_path="/home/user/2025-GEO-Project/backend/data/input/suit.jpg",
            mask_image_path="/home/user/2025-GEO-Project/backend/data/input/a_man_posing_wearing_a_parakeet_t-shirt_mask_upperbody.jpg",
        )
        logger.info("✅ vton 생성 완료")


        # # ----------------------------------------------
        # # 3. 이미지 누끼 따기 및 마스크 만들기용
        # img_loader = ImageLoader()
        # img, filename = img_loader.load_image("/home/user/2025-GEO-Project/backend/data/input/a_man_posing_wearing_a_parakeet_t-shirt.webp")
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