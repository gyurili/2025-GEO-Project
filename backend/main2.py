import os
import asyncio
from pathlib import Path
from backend.competitor_analysis.competitor_main import competitor_main
from backend.image_generator.image_generator_main import vton_generator_main
from backend.text_generator.text_generator_main import text_generator_main
from backend.page_generator.page_generator_main import page_generator_main
from utils.logger import get_logger
from utils.config import load_config

logger = get_logger(__name__)

def main():
    config = load_config()
    product = config["input"]
    output_path = config["data"]["output_path"]
    result_path = config["data"]["result_path"]

    logger.info("🛠️ 차별점 생성 시작")
    differences = asyncio.run(competitor_main(product))
    product["differences"] = differences
    
    logger.info("🛠️ VTON 이미지 생성 시작")
    vton_image_path = os.path.join(output_path, "suit.png")
    vton_abs_path = Path(vton_image_path).resolve()
    
    if vton_abs_path.exists():
        logger.info("✅ 기존 VTON 이미지가 존재")
    else:
        vton_result = vton_generator_main(
            model_image_path=product["model_image_path"],
            ip_image_path=product["ip_image_path"],
            mask_image_path=product["mask_image_path"],
        )
        vton_abs_path = Path(vton_result["image_path"]).resolve()
    
    product["vton_image_path"] = f"file://{vton_abs_path}"

    logger.info("🛠️ 텍스트 상세페이지 생성 시작")
    session_id = text_generator_main(product, result_path)

    logger.info("🛠️ 최종 상세페이지 생성 시작")
    page_generator_main(product, session_id)

    logger.info(f"✅ 전체 파이프라인 완료: session_id = {session_id}")

if __name__ == "__main__":
    main()