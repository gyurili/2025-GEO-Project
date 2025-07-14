import yaml
import os
import torch

from utils.logger import get_logger
from backend.image_generator.image_generator_main import image_generator_main
from backend.image_generator.core.virtual_try_on import VirtualTryOnPipeline
from utils.logger import get_logger

logger = get_logger(__name__)

if __name__ == "__main__":
    try:
        logger.debug("🛠️ 테스트 시작")
        # 모델을 저장할 기본 폴더 지정
        MODEL_BASE_DIR = "backend/models"
        
        # 가상 피팅 파이프라인 초기화 (모든 모델 로드/다운로드)
        # 이 단계에서 모든 모델이 MODEL_BASE_DIR에 다운로드됩니다.
        virtual_try_on_system = VirtualTryOnPipeline(model_dir=MODEL_BASE_DIR)

        # 가상 피팅 실행
        result_image = virtual_try_on_system.try_on(
            image_path='/home/user/2025-GEO-Project/backend/data/output/model_removed_bg.png',
            ip_image_path='/home/user/2025-GEO-Project/backend/data/output/greendress_removed_bg.png',
            mask_image_path='/home/user/2025-GEO-Project/backend/data/input/model_mask3.png',
            prompt="photorealistic, perfect body, beautiful skin, realistic skin, natural skin, a woman wearing a green dress with elegant details, flowing fabric, realistic folds, high fashion", # 프롬프트 강화
            negative_prompt="ugly, bad quality, bad anatomy, deformed body, deformed hands, deformed feet, deformed face, deformed clothing, deformed skin, bad skin, leggings, tights, stockings, flat clothing, blurry textures, unnatural fabric, poor lighting",
            width=512,
            height=512,
            strength=0.99,
            guidance_scale=7.5,
            num_inference_steps=100
        )

        result_image.save("final_vton.png")
        logger.info("✅최종 결과 이미지가 'final_vton.png'로 저장되었습니다.")

    except Exception as e:
        logger.error(f"❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()

# 이전 결과물
# if __name__ == "__main__":
#     try: 
#         # 1. config 로딩
#         logger.debug("🛠️ config.yaml 로드 시작")
#         with open("config.yaml", "r", encoding="utf-8") as f:
#             config = yaml.safe_load(f)
#             logger.info("✅ config.yaml 로드 완료")
        
#         product = config["input"]
#         image_path = product["image_path"]

#         # 2. 이미지 생성 메인
#         logger.debug("🛠️ 이미지 생성기 시작")
#         image = image_generator_main(
#             product=product, 
#             image_path=image_path,
#             model_id="SG161222/RealVisXL_V4.0",
#             ip_adapter_scale=0.55,
#             num_inference_steps=99,
#             guidance_scale=7.5,
#         )

#         if image["image"]:
#             logger.info("✅ 최종 이미지 생성 완료")
#         else:
#             logger.error("❌ 최종 이미지 생성 실패")
#     except Exception as e:
#         logger.error(f"❌ 실행 중 에러 발생: {e}")