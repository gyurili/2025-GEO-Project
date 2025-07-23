import yaml
import os
import sys
import torch
from pathlib import Path

# 프로젝트 루트 경로 설정
script_dir = Path(__file__).parent.absolute()
backend_models_dir = script_dir / "backend" / "models"
backend_models_dir.mkdir(parents=True, exist_ok=True)

print(f"✅ 모델 저장 경로 설정: {backend_models_dir}")

# 작업 디렉토리 변경
os.chdir(script_dir)

# backend를 Python path에 추가
backend_path = script_dir / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from utils.logger import get_logger

# ⭐ 환경 변수로 기본 모델 저장 경로 변경
os.environ["MODEL_SAVE_DIR"] = str(backend_models_dir)

# model_handler import 후 기본값 패치
import backend.models.model_handler as model_handler

# get_model_pipeline 함수의 기본값을 backend/models로 변경
original_func = model_handler.get_model_pipeline

def patched_get_model_pipeline(*args, **kwargs):
    if 'save_dir' not in kwargs:
        kwargs['save_dir'] = str(backend_models_dir)
    return original_func(*args, **kwargs)

model_handler.get_model_pipeline = patched_get_model_pipeline

from backend.image_generator.image_generator_main import ImgGenPipeline

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

        logger.debug("🛠️ 이미지 생성기 시작")
        image_generator = ImgGenPipeline()  # 클래스 변수 선언

        image_dict1 = image_generator.generate_image(
            product=product,
            seed=42,
        )
        if image_dict1:
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

    except Exception as e:
        logger.error(f"❌ 에러 발생: {e}")