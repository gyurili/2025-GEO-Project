import os
import sys
from backend.text_generator.text_generator_main import text_generator_main
from backend.page_generator.page_generator_main import page_generator_main
from utils.logger import get_logger
from utils.config import load_config 

logger = get_logger(__name__)

def main():
    config = load_config()

    logger.info("🛠️ 텍스트 상세페이지 생성 시작")
    session_id = text_generator_main(config)

    logger.info("🛠️ 최종 상세페이지 생성 시작")
    page_generator_main(config, session_id)

    logger.info(f"✅ 전체 파이프라인 완료: session_id = {session_id}")


if __name__ == "__main__":
    main()