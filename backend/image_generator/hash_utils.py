import hashlib
import json
import os

from utils.logger import get_logger

logger = get_logger(__name__)

def generate_cache_key(
    product: dict,
    prompt_mode: str,
    seed: int,
    extra: dict = None
) -> str:
    """
    캐시 키를 생성합니다. 입력 데이터를 직렬화하여 MD5 해시로 변환합니다.

    Args:
        product (dict): 상품 정보 (이름, 키워드 등)
        prompt_mode (str): 프롬프트 모드
        seed (int): 랜덤 시드
        extra (dict, optional): 추가 파라미터 (예: width, height 등)

    Returns:
        str: 생성된 해시 키
    """
    data = {
        "product_info": product,
        "image_name": [os.path.basename(image) for image in product.get("image_path_list", [])],
        "prompt_mode": prompt_mode,
        "seed": seed,
        "extra": extra or {}
    }
    raw_string = json.dumps(data, sort_keys=True)
    logger.debug(f"캐시 키 생성 데이터: {json.dumps(data, ensure_ascii=False, sort_keys=True)}")
    return hashlib.md5(raw_string.encode("utf-8")).hexdigest()