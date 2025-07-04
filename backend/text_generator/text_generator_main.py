import yaml
import os
from core.text_generator import generate_html
from utils.logger import get_logger

logger = get_logger(__name__)

def text_generator_main():
    with open("config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        logger.info("✅ config.yaml 로드 완료")

    product = config["input"]
    result = generate_html(product)

    output_path = config["data"]["output_path"]

    with open(os.path.join(output_path, "result-css.html"), "w", encoding="utf-8") as f:
        f.write(result["html_text"])
        logger.info(f"📁 HTML 상세페이지 저장 완료: {output_path}/result-css.html")


if __name__ == "__main__":
    text_generator_main()