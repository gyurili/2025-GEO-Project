import os
import yaml
from datetime import datetime, timedelta, timezone
from utils.logger import get_logger
from backend.text_generator.core.text_generator import generate_html

logger = get_logger(__name__)


def text_generator_main(config):
    product = config["input"]
    result = generate_html(product)
    
    logger.debug(f"🛠️ 파일명 생성 시작")
    KST = timezone(timedelta(hours=9))
    session_id = datetime.now(KST).strftime("%Y%m%d_%H%M%S_%f")[:-3]
    filename = f"draft_{session_id}.html"

    output_path = config["data"]["output_path"]
    os.makedirs(output_path, exist_ok=True)
    
    full_output_path = os.path.join(output_path, filename)

    try:
        with open(full_output_path, "w", encoding="utf-8") as f:
            f.write(result["html_text"])
            logger.info(f"✅ HTML 상세페이지 저장 완료: {full_output_path}")
    except Exception as e:
        raise RuntimeError(f"❌ HTML 저장 실패: {e}")
            
    return session_id