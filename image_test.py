import yaml
import os
import torch

from utils.logger import get_logger
from backend.image_generator.image_generator_main import image_generator_main

logger = get_logger(__name__)

if __name__ == "__main__":
    try: 
        # 1. config 로딩
        logger.debug("🛠️ config.yaml 로드 시작")
        with open("config.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            logger.info("✅ config.yaml 로드 완료")
        
        product = config["input"]
        image_path = product["image_path"]

        # 2. 이미지 생성 메인
        logger.debug("🛠️ 이미지 생성기 시작")
        image = image_generator_main(
            product=product, 
            image_path=image_path,
            model_id="SG161222/RealVisXL_V4.0",
            ip_adapter_scale=0.55,
            num_inference_steps=99,
            guidance_scale=7.5,
        )

        if image["image"]:
            logger.info("✅ 최종 이미지 생성 완료")
        else:
            logger.error("❌ 최종 이미지 생성 실패")
    except Exception as e:
        logger.error(f"❌ 실행 중 에러 발생: {e}")