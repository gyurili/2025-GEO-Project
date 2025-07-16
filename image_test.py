import yaml
import os
import torch

from utils.logger import get_logger
from backend.image_generator.image_generator_main import image_generator_main, vton_generator_main

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
        # 함수 실행
        logger.debug("🛠️ vton 함수 불러오기")
        result = vton_generator_main(
            model_image_path="/home/user/2025-GEO-Project/backend/data/output/model_removed_bg.png",
            ip_image_path="/home/user/2025-GEO-Project/backend/data/input/greendress.jpg",
            mask_image_path="/home/user/2025-GEO-Project/backend/data/input/model_mask3.png",
        )
        logger.info("✅이미지 생성 성공")

    except Exception as e:
        logger.error(f"❌ 에러 발생: {e}")