import os
import sys
import yaml
from backend.text_generator.text_generator_main import text_generator_main
from backend.page_generator.page_generator_main import page_generator_main
from utils.logger import get_logger

logger = get_logger(__name__)

def load_config(config_path: str):
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            logger.info("✅ config.yaml 로드 완료")
            return config
    except FileNotFoundError:
        raise FileNotFoundError("❌ config.yaml 파일을 찾을 수 없습니다.")
    except yaml.YAMLError as e:
        raise ValueError(f"❌ config.yaml 파싱 오류: {e}")

def main():
    # config 로드
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    config_path = os.path.join(project_root, "config.yaml")
    config = load_config(config_path)

    # HTML 상세페이지 텍스트 생성
    logger.info("🛠️ 텍스트 상세페이지 생성 시작")
    session_id = text_generator_main(config)

    # HTML → 이미지 페이지 생성
    logger.info("🛠️ 최종 상세페이지 생성 시작")
    page_generator_main(config, session_id)

    logger.info(f"✅ 전체 파이프라인 완료: session_id = {session_id}")


if __name__ == "__main__":
    main()