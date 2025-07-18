import yaml
import os
import sys
import datetime
import torch
from PIL import Image
from diffusers.utils import load_image

from utils.logger import get_logger
from .image_loader import ImageLoader
from .background_handler import BackgroundHandler
from .prompt_builder import generate_prompts
from backend.models.model_handler import get_model_pipeline, get_vton_pipeline

'''
TODO: 전체 리팩토링
'''

logger = get_logger(__name__)

class ImgGenPipeline:
    def __init__(self):
        logger.debug("🛠️ 이미지 생성기 파이프라인 초기화 시작")

        # 유틸리티 초기화
        self.image_loader = ImageLoader()
        self.background_handler = BackgroundHandler()

        # # Diffusion 모델 파이프라인 로드
        # logger.info("🛠️ Diffusion Pipeline 로딩 시작")
        # self.diffusion_pipeline = get_model_pipeline(
        #     model_id="SG161222/RealVisXL_V5.0", 
        #     model_type="diffusion_text2img",
        #     use_ip_adapter=True,
        #     ip_adapter_config={
        #         "repo_id": "h94/IP-Adapter",
        #         "subfolder": "sdxl_models",
        #         "weight_name": "ip-adapter_sdxl.bin",
        #         "scale": 0.66
        #     }
        # )
        # logger.info("✅ Diffusion Pipeline 로딩 완료")

        # VTON 파이프라인 로드
        logger.debug("🛠️ VTON 파이프라인 및 MidasDetector 로딩 시작")
        self.vton_pipeline, self.midas_detector = get_vton_pipeline(
            pipeline_model="diffusers/stable-diffusion-xl-1.0-inpainting-0.1",
            vae_model="madebyollin/sdxl-vae-fp16-fix",
            controlnet_model="diffusers/controlnet-depth-sdxl-1.0",
            midas_model="lllyasviel/ControlNet",
            ip_adapter_config={
                "repo_id": "h94/IP-Adapter",
                "subfolder": "sdxl_models",
                "weight_name": "ip-adapter_sdxl.bin",
                "scale": 0.75
            },
            lora_config={
                "repo_id": "Norod78/weird-fashion-show-outfits-sdxl-lora",
                "weight_name": "sdxl-WeirdOutfit-Dreambooh.safetensors"
            },
        )
        logger.info("✅ VTON 파이프라인 및 MidasDetector 로딩 완료")

        logger.info("✅ 이미지 생성기 파이프라인 초기화 완료")
    
    def generate_image(self,
            product: dict,
            image_path: str,
            prompt_mode: str = "human",
            output_dir: str = "./backend/data/output/",
            seed: int = 42,
        ) -> dict:
        logger.debug("🛠️ generate_image() 시작")

        # 1. 이미지 로더
        logger.debug(f"🛠️ 이미지 로드 시작")
        loaded_image, filename = self.image_loader.load_image(image_path=image_path, target_size=None)
        if loaded_image is None:
            logger.error("❌ 이미지 로드에 실패했습니다. 처리를 중단합니다.")
            return False
        logger.info("✅ 이미지 로드 성공.")

        # 2. 배경 제거
        logger.debug(f"🛠️ 배경 제거 시작")
        processed_image, save_path = self.background_handler.remove_background(
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

        # RGBA → RGB
        if processed_image.mode != 'RGB':
            # logger.warning("⚠️ processed_image를 RGB로 변환")
            processed_image = processed_image.convert("RGB")

        logger.info(f"랜덤 시드: {seed}")
        generator = torch.manual_seed(seed)

        # 4. 이미지 생성
        logger.debug("🛠️ 모델 파이프라인으로 이미지 생성 시작")
        try:
            result_image = self.diffusion_pipeline(
                prompt=prompts["background_prompt"],
                negative_prompt=prompts["negative_prompt"],
                ip_adapter_image=processed_image,
                height=512, width=512,
                num_inference_steps=99,
                guidance_scale=7.5,
                num_images_per_prompt=1,
                generator=generator,
            ).images[0]
            logger.info("✅ 이미지 생성 성공")
        except Exception as e:
            logger.error(f"❌ 이미지 생성 중 에러 발생: {e}")
            return False

        os.makedirs(output_dir, exist_ok=True)
        name_without_ext, _ = os.path.splitext(filename)
        save_path = os.path.join(output_dir, f"{name_without_ext}_gen.png")
        result_image.save(save_path)
        logger.info(f"✅ 이미지가 {save_path}에 생성되었습니다.")

        logger.debug("✅ generate_image() 완료")
        return {"image": result_image, "image_path": save_path}

    def generate_vton(self,
        model_image_path: str, 
        ip_image_path: str, 
        mask_image_path: str, 
        output_dir="./backend/data/output",
        seed: int = 42,
        ) -> dict:
        logger.debug("🛠️ generate_vton() 시작")

        # 1. 의류 이미지 로드
        logger.debug(f"🛠️ 이미지 로드 시작")
        model_image = load_image(model_image_path).convert("RGB")
        loaded_image, filename = self.image_loader.load_image(image_path=ip_image_path, target_size=None)
        mask_image = load_image(mask_image_path)
        logger.info("✅ 이미지 로드 완료")

        # 2. 배경 제거
        logger.debug(f"🛠️ 의류 이미지 배경 제거 시작")
        ip_image, removed_bg_path = self.background_handler.remove_background(
            input_image=loaded_image,
            original_filename=filename,
        )
        if ip_image is None:
            logger.error("❌ 배경 제거 실패")
            return False
        logger.info(f"✅ 배경 제거 완료: {removed_bg_path}")

        # Depth 생성
        logger.debug("🛠️ Depth 제어 이미지 생성 시작")
        depth_image = self.midas_detector(model_image).resize((512, 768)).convert("RGB")

        logger.info(f"랜덤 시드: {seed}")
        generator = torch.manual_seed(seed)

        # 3. VTON 실행
        logger.debug("🛠️ vton 파이프라인 실행 시작")
        result_image = self.vton_pipeline(
            prompt=(
                "A full-body photo of the model wearing the selected clothing item. "
                "Preserve the exact design, fabric texture, material shine, seams, and colors of the clothing. "
                "Ensure natural fit and realistic lighting."
            ),
            negative_prompt=(
                "blurry, unrealistic, distorted body, misaligned clothing, missing fabric details, flat colors, "
                "incorrect texture, artifacts, bad anatomy, deformed hands, deformed face"
            ),
            width=512,
            height=768,
            image=model_image,
            mask_image=mask_image,
            ip_adapter_image=ip_image,
            control_image=depth_image,
            controlnet_conditioning_scale=0.7,
            strength=0.99,
            guidance_scale=7.5,
            num_inference_steps=100,
            generator=generator
        ).images[0]
        logger.info("✅ 이미지 생성 완료")

        os.makedirs(output_dir, exist_ok=True)
        name_without_ext, _ = os.path.splitext(filename)
        save_path = os.path.join(output_dir, f"{name_without_ext}_vton.png")
        result_image.save(save_path)
        logger.info(f"✅ 이미지가 {save_path}에 생성되었습니다.")

        logger.info("✅ generate_vton() 완료")
        return {"image": result_image, "image_path": save_path}