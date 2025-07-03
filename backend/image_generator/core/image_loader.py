import os
import sys
from dotenv import load_dotenv

# .env 로부터 PYTHONPATH 불러와 모듈 검색 경로에 추가
load_dotenv()
sys.path.append(os.getenv("PYTHONPATH"))  # 꼭 import 전에 해야 함

from PIL import Image
# import numpy as np
from utils.logger import get_logger

logger = get_logger(__name__)

def load_image(image_path: str) -> Image.Image:
    """
    저장된 이미지 파일을 로드하여 PIL 객체로 반환
    """
    try:
        img = Image.open(image_path).convert("RGB")
        logger.info(f"✅ 이미지 로딩 성공: {image_path} | 크기 : {img.size}")
        return img
    except Exception as e:
        print(f"{e}")
        return 
        logger.error(f"❌ 이미지 로딩 실패: {image_path} | 에러: {e}")

def preprocess_image(image: Image.Image, target_size=(512, 512)) -> Image.Image:
    """
    ControlNet 등 허깅페이스 기반 모델 입력용 전처리
    """
    image = image.resize(target_size)

    return image

if __name__ == "__main__":
    img = load_image("/home/user/2025-GEO-Project/backend/data/input/test_image.jpg")
    print(img.size)
    img = preprocess_image(img)
    print(img.size)