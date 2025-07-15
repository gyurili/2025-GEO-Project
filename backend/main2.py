import asyncio
from backend.competitor_analysis.core.competitor_main import competitor_main
from backend.text_generator.text_generator_main import text_generator_main
from backend.page_generator.page_generator_main import page_generator_main
from backend.competitor_analysis.schemas.input_schema import ProductInput
from backend.text_generator.schemas.input_schema import TextGenRequest
from backend.page_generator.schemas.input_schema import PageGenRequest
from utils.logger import get_logger
from utils.config import load_config

logger = get_logger(__name__)

def main():
    config = load_config()
    product = config["input"]
    output_path = config["data"]["output_path"]
    
    logger.info("🛠️ 차별점 생성 시작")
    product_input = ProductInput(**product)
    differences = asyncio.run(competitor_main(product_input)).differences

    logger.info("🛠️ 텍스트 상세페이지 생성 시작")
    textgen_input = TextGenRequest(**product)
    session_id = text_generator_main(textgen_input, differences, output_path)

    logger.info("🛠️ 최종 상세페이지 생성 시작")
    page_input = PageGenRequest(**product)
    page_generator_main(page_input, session_id)

    logger.info(f"✅ 전체 파이프라인 완료: session_id = {session_id}")


if __name__ == "__main__":
    main()