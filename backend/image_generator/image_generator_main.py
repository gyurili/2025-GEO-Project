import yaml
import os
import sys
import datetime
import torch
from PIL import Image

from utils.logger import get_logger
from .core.image_loader import ImageLoader
from .core.background_handler import Txt2ImgGenerator, BackgroundHandler, Img2ImgGenerator
from .core.prompt_builder import generate_prompts
from backend.models.model_handler import get_model_pipeline

'''
TODO: 상품명, 카테고리, 특징, 이미지패스, 상품링크, 차별점을 바탕으로 이미지 재구성
TODO: 이미지를 임시로 데이터 아웃풋에 저장 이후 삭제
'''

logger = get_logger(__name__)

def image_generator_main(
    product: dict,
    image_path: str, 
    prompt_mode: str = "human",
    model_id: str = "SG161222/RealVisXL_V4.0",
    model_type: str = "diffusion",
    ip_adapter_scale: float = 0.5,
    num_inference_steps: int = 99,
    guidance_scale: float = 7.5,
    output_dir_path: str = "backend/data/output/",
    background_image_path: str = None,
)-> dict | bool:
    """
    이미지 제너레이터 메인
    """
    # 1. 이미지 로더
    logger.debug(f"🛠️ 이미지 로드 시작")
    image_loader = ImageLoader()
    loaded_image, filename = image_loader.load_image(image_path=image_path, target_size=None)

    if loaded_image is None:
        logger.error("❌ 이미지 로드에 실패했습니다. 처리를 중단합니다.")
        return False

    logger.info("✅ 이미지 로드 성공.")

    # 2. 배경 제거
    logger.debug(f"🛠️ 배경 제거 시작")
    background_handler = BackgroundHandler()

    processed_image = background_handler.remove_background(
        input_image=loaded_image,
        original_filename=filename,
    )

    if processed_image is None:
        logger.error("❌ 배경 제거에 실패했습니다. 처리를 중단합니다.")
        return False

    logger.info("✅ 배경 제거 및 저장 성공.")

    # 3. 프롬프트 생성
    logger.debug("🛠️ 프롬프트 생성 시작")
    prompts = generate_prompts(product, mode=prompt_mode)

    if prompts:
        logger.info("✅ 프롬프트 생성 완료")
    else:
        logger.error("❌ 프롬프트 생성 실패")

    # 4. 모델 파이프라인 생성
    logger.debug(f"🛠️ 모델 다운로드 및 로드 시작")
    pipeline = get_model_pipeline(
        model_id=model_id, 
        model_type=model_type,
        use_ip_adapter=True,
        ip_adapter_config={
            "repo_id": "h94/IP-Adapter",
            "subfolder": "sdxl_models",
            "weight_name": "ip-adapter_sdxl.bin",
            "scale": ip_adapter_scale
        }
    )
    if pipeline:
        logger.info(f"✅ 모델 다운로드 및 로드 완료")
    else:
        logger.error("❌ 모델 다운로드 또는 로드 실패.")

    # 시각 기반 랜덤시드 생성 년월일시분초
    now = datetime.datetime.now()
    seed = int(now.strftime("%Y%m%d%H%M%S"))
    generator = torch.manual_seed(seed)
    logger.debug(f"🛠️ 날짜 시드: {seed}")

    # 5. 제품 이미지 생성하기
    logger.debug("🛠️ 모델 파이프라인으로 이미지 생성 시작")
    try:
        img_2_img_gen = Img2ImgGenerator(pipeline)
        gen_image, image_path = img_2_img_gen.generate_img(
            prompt=prompts["background_prompt"],
            reference_image=processed_image,
            filename=filename,
            negative_prompt=prompts["negative_prompt"],
            size=(512, 512),
            generator=generator,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
        )
        logger.info("✅ 이미지 생성 성공")
    except Exception as e:
        logger.error(f"❌ 이미지 생성 중 에러 발생: {e}")
        return False

    return {
        "image": gen_image,
        "image_path": image_path
    }