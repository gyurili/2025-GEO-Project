import asyncio
from backend.competitor_analysis.core.competitor_main import competitor_main
from backend.text_generator.text_generator_main import text_generator_main
from backend.page_generator.page_generator_main import page_generator_main
from utils.logger import get_logger
from utils.config import load_config

logger = get_logger(__name__)

def main():
    config = load_config()
    product = config["input"]
    output_path = config["data"]["output_path"]

    logger.info("🛠️ 차별점 생성 시작")
    differences = asyncio.run(competitor_main(product))

    logger.info("🛠️ 텍스트 상세페이지 생성 시작")
    session_id = text_generator_main(product, differences, output_path)

    logger.info("🛠️ 최종 상세페이지 생성 시작")
    page_generator_main(product, session_id)

    logger.info(f"✅ 전체 파이프라인 완료: session_id = {session_id}")

if __name__ == "__main__":
    main()
