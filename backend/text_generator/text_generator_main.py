import os
import yaml
from datetime import datetime, timedelta, timezone
from utils.logger import get_logger
from backend.text_generator.core.text_generator import generate_html
from backend.page_generator.page_generator_main import page_generator_main  # 삭제 예정

logger = get_logger(__name__)

def text_generator_main():
    with open("config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        logger.info("✅ config.yaml 로드 완료")

    product = config["input"]
    result = generate_html(product)
    
    # 고유 session_id 생성
    KST = timezone(timedelta(hours=9))
    session_id = datetime.now(KST).strftime("%Y%m%d_%H%M%S_%f")[:-3]
    filename = f"draft_{session_id}.html"

    output_path = config["data"]["output_path"]
    os.makedirs(output_path, exist_ok=True)
    
    full_output_path = os.path.join(output_path, filename)

    with open(full_output_path, "w", encoding="utf-8") as f:
            f.write(result["html_text"])
            logger.info(f"✅ HTML 상세페이지 저장 완료: {full_output_path}")
            
    page_generator_main(session_id) # 삭제 예정
            
    return session_id


if __name__ == "__main__":
    text_generator_main()