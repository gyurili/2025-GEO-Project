import os
from datetime import datetime, timedelta, timezone
from utils.logger import get_logger
from utils.config import load_config
from backend.text_generator.text_generator import generate_openai, generate_hf

logger = get_logger(__name__)


def text_generator_main(product: dict):
    config = load_config()
    result_path = config["data"]["result_path"]
    
    engine = product.get("engine", "openai")
    if engine == "openai":
        result = generate_openai(product)
    else:
        result = generate_hf(product)
    
    logger.debug(f"🛠️ 파일명 생성 시작")
    KST = timezone(timedelta(hours=9))
    session_id = datetime.now(KST).strftime("%Y%m%d_%H%M%S_%f")[:-3]
    filename = f"page_{session_id}.html"

    os.makedirs(result_path, exist_ok=True)
    full_result_path = os.path.join(result_path, filename)

    try:
        with open(full_result_path, "w", encoding="utf-8") as f:
            f.write(result["html_text"])
            logger.info(f"✅ HTML 상세페이지 저장 완료: {full_result_path}")
    except Exception as e:
        raise RuntimeError(f"❌ HTML 저장 실패: {e}")
    
    product["session_id"] = session_id
    return product