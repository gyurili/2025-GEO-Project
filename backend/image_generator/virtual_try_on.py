import datetime
import os
import torch
from PIL import Image
from controlnet_aux import MidasDetector
from diffusers.utils import load_image
from utils.logger import get_logger

logger = get_logger(__name__)


def run_virtual_tryon(
    pipeline,
    midas_detector,
    model_image_path: str,
    ip_image_path: str,
    mask_image_path: str,
    prompt: str,
    negative_prompt: str,
    width: int = 512,
    height: int = 768,
    controlnet_conditioning_scale: float = 0.7,
    strength: float = 0.99,
    guidance_scale: float = 7.5,
    num_inference_steps: int = 100,
    seed: int = None,
):
    """
    준비된 VTON 파이프라인을 사용해 가상 피팅 이미지를 생성합니다.

    Args:
        pipeline: get_vton_pipeline()으로 준비된 파이프라인
        midas_detector: get_vton_pipeline()으로 준비된 MidasDetector
        model_image_path (str): 모델 이미지 경로
        ip_image_path (str): 의상 이미지 경로
        mask_image_path (str): 마스크 이미지 경로
        prompt (str): 긍정 프롬프트
        negative_prompt (str): 부정 프롬프트
        width (int): 생성 이미지 너비
        height (int): 생성 이미지 높이
        controlnet_conditioning_scale (float): ControlNet 반영 비율
        strength (float): Inpainting strength
        guidance_scale (float): CFG scale
        num_inference_steps (int): 생성 스텝 수
        seed (int): 시드 (None이면 현재 시간)

    Returns:
        PIL.Image.Image: 생성된 가상 피팅 이미지
    """
    logger.debug("🛠️ 입력 이미지 로딩 시작")
    model_image = load_image(model_image_path).convert("RGB")
    ip_image = load_image(ip_image_path).convert("RGB")
    mask_image = load_image(mask_image_path)
    logger.info("✅ 입력 이미지, 의상 이미지, 마스크 로딩 완료")

    logger.debug("🛠️ Depth 제어 이미지 생성 시작")
    control_image_depth = midas_detector(model_image).resize((width, height)).convert("RGB")
    logger.info("✅ Depth 제어 이미지 생성 완료")

    if seed is None:
        now = datetime.datetime.now()
        seed = int(now.strftime("%Y%m%d%H%M%S"))
    generator = torch.manual_seed(seed)
    logger.info(f"✅ 시드 설정 완료: {seed}")

    logger.debug("🛠️ 이미지 생성 시작")
    final_image = pipeline(
        prompt=prompt,
        negative_prompt=negative_prompt,
        width=width,
        height=height,
        image=model_image,
        mask_image=mask_image,
        ip_adapter_image=ip_image,
        control_image=control_image_depth,
        controlnet_conditioning_scale=controlnet_conditioning_scale,
        strength=strength,
        guidance_scale=guidance_scale,
        num_inference_steps=num_inference_steps,
        generator=generator,
    ).images[0]
    logger.info("✅ 이미지 생성 완료")

    return final_image