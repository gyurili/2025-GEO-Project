import asyncio
from pathlib import Path
from backend.competitor_analysis.competitor_main import competitor_main
from backend.text_generator.text_generator_main import text_generator_main
from backend.page_generator.page_generator_main import page_generator_main
from utils.logger import get_logger
from utils.config import load_config

logger = get_logger(__name__)

def main():
    config = load_config()
    product = config["input"]
    
    image_paths = product.get("image_path_list", [])
    image_paths = [f"file://{Path(p).resolve()}" for p in image_paths]
    product["image_path_list"] = image_paths

    logger.info(f"🛠️ 입력 이미지 목록: {image_paths}")

    logger.info("🛠️ 차별점 생성 시작")
    differences = asyncio.run(competitor_main(product))
    product["differences"] = differences

    logger.info("🛠️ 텍스트 상세페이지 생성 시작")
    product = text_generator_main(product)

    logger.info("🛠️ 최종 상세페이지 생성 시작")
    page_generator_main(product)

    logger.info(f"✅ 전체 파이프라인 완료: session_id = {product['session_id']}")

if __name__ == "__main__":
    main()
