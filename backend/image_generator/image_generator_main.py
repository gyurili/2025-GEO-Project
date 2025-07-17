import yaml
import os
import sys
import datetime
import torch
from PIL import Image

from utils.logger import get_logger
from .image_loader import ImageLoader
from diffusers.utils import load_image
from .background_handler import BackgroundHandler, Img2ImgGenerator
from .prompt_builder import generate_prompts
from .virtual_try_on import run_virtual_tryon
from backend.models.model_handler import get_model_pipeline, get_vton_pipeline

'''
TODO: 전체 리팩토링
'''

logger = get_logger(__name__)

def image_generator_main(
    product: dict,
    image_path: str, 
    prompt_mode: str = "human",
    model_id: str = "SG161222/RealVisXL_V4.0",
    model_type: str = "diffusion_text2img",
    ip_adapter_scale: float = 0.5,
    num_inference_steps: int = 99,
    guidance_scale: float = 7.5,
    output_dir_path: str = "./backend/data/output/",
    background_image_path: str = None,
    seed: int = None,
)-> dict | bool:
    """
    제품 이미지를 기반으로 AI 이미지 생성 파이프라인을 실행합니다.

    주요 단계:
    1. 이미지 로드:
       - 입력 경로(`image_path`)에서 원본 이미지를 로드.
    2. 배경 제거:
       - 배경 제거 후 결과 이미지 저장.
    3. 프롬프트 생성:
       - 상품 정보를 기반으로 GEO/SEO 최적화된 프롬프트 생성.
    4. 모델 파이프라인 로드:
       - Hugging Face에서 지정된 diffusion 모델 로드.
       - IP-Adapter를 사용하여 참고 이미지 기반 생성 강화.
    5. 시드 설정:
       - 생성 시 랜덤성 제어를 위해 시드 설정.
    6. 이미지 생성:
       - Img2Img 방식으로 이미지 생성.
       - 생성된 이미지는 지정 경로에 저장.

    Args:
        product (dict): 상품명, 카테고리, 특징 등 제품 정보.
        image_path (str): 입력 이미지 경로.
        prompt_mode (str): 프롬프트 생성 모드 (기본값: "human").
        model_id (str): 모델 식별자 (기본값: "SG161222/RealVisXL_V4.0").
        model_type (str): 모델 타입 (예: "diffusion_text2img").
        ip_adapter_scale (float): IP-Adapter 적용 강도 (0.0~1.0).
        num_inference_steps (int): 이미지 생성 시 inference 스텝 수.
        guidance_scale (float): CFG 스케일 (프롬프트 준수 정도).
        output_dir_path (str): 생성 이미지 저장 디렉토리.
        background_image_path (str): (옵션) 별도 배경 이미지 경로.
        seed (int): 시드 (None이면 현재 시간)

    Returns:
        dict: 생성된 이미지(`PIL.Image`)와 저장 경로.
        bool: 실패 시 False 반환.
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

    processed_image, save_path = background_handler.remove_background(
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
    if seed is None:
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


def vton_generator_main(
    model_image_path: str,
    ip_image_path:str,
    mask_image_path:str,
    seed:int = None,
):
    """
    Virtual Try-On (VTON) 기능을 통해 모델 이미지에 의류를 합성합니다.

    이 함수는 다음 단계를 수행합니다:
    1. 의류 이미지 로드:
        - ip_image_path에서 의류 이미지를 불러옵니다.
    2. 배경 제거:
        - 의류 이미지의 배경을 제거하여 합성에 적합한 형태로 만듭니다.
    3. VTON 파이프라인 준비:
        - get_vton_pipeline()을 사용하여 Stable Diffusion 기반 파이프라인을 구성합니다.
        - IP-Adapter 및 LoRA 모델이 주입됩니다.
    4. 합성 실행:
        - run_virtual_tryon()을 호출하여 모델 이미지와 의류 이미지를 합성합니다.
        - ControlNet 기반으로 자연스러운 합성 이미지를 생성합니다.
    5. 결과 저장:
        - 생성된 이미지를 `backend/data/output/`에 PNG 형식으로 저장합니다.

    Args:
        model_image_path (str): 모델(사람) 이미지의 파일 경로.
        ip_image_path (str): 의류 이미지 파일 경로.
        mask_image_path (str): 합성할 영역의 마스크 이미지 경로.
        seed (int): 랜덤시드. 미지정시 시간기반지정

    Returns:
        dict: {
            "image": PIL.Image,  # 생성된 합성 이미지
            "image_path": str    # 저장된 이미지 파일 경로
        }
        처리 실패 시 False 반환.
    """
    # 1. 의류 이미지 로드
    logger.debug(f"🛠️ 이미지 로드 시작")
    image_loader = ImageLoader()
    loaded_image, filename = image_loader.load_image(image_path=ip_image_path, target_size=None)

    if loaded_image is None:
        logger.error("❌ IP 이미지 로드 실패 → 종료")
        return False
    logger.info("✅ IP 이미지 로드 완료")

    # 2. 배경 제거
    logger.debug(f"🛠️ 배경 제거 시작")
    background_handler = BackgroundHandler()

    ip_image, removed_bg_path = background_handler.remove_background(
        input_image=loaded_image,
        original_filename=filename,
    )

    if ip_image is None:
        logger.error("❌ 배경 제거 실패 → 종료")
        return False
    logger.info(f"✅ 배경 제거 완료 → 임시 저장 경로: {removed_bg_path}")

    # 3. VTON 파이프라인 로드
    logger.debug("🛠️ vton 파이프라인 불러오기 시작")
    pipeline, midas_detector = get_vton_pipeline(
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
    logger.info("✅ vton 파이프라인 불러오기 완료")

    # 4. VTON 실행
    logger.debug("🛠️ vton 실행 시작")
    try:
        result_image = run_virtual_tryon(
            pipeline=pipeline,
            midas_detector=midas_detector,
            model_image_path=model_image_path,
            ip_image_path=removed_bg_path,
            mask_image_path=mask_image_path,
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
            controlnet_conditioning_scale=0.7,
            strength=0.99,
            guidance_scale=7.5,
            num_inference_steps=100,
            seed=seed
        )
    except Exception as e:
        logger.error(f"❌ VTON 처리 중 오류 발생: {e}")
        return False

    # 5. 결과 저장
    name_without_ext, _ = os.path.splitext(filename)
    save_path = f"backend/data/output/{name_without_ext}_vton.png"
    result_image.save(save_path)
    logger.info(f"✅ 이미지가 {save_path}에 생성되었습니다.")

    return {
        "image": result_image,
        "image_path": save_path
    }



class ImgGenPipeline:
    def __init__(self, seed: int = 42):
        logger.debug("🛠️ 이미지 생성기 파이프라인 초기화 시작")
        self.seed = seed
        logger.info(f"랜덤 시드: {self.seed}")
        self.generator = torch.manual_seed(self.seed)
        self.image_loader = ImageLoader()
        self.background_handler = BackgroundHandler()
        self.diffusion_pipeline = get_model_pipeline(
            model_id="SG161222/RealVisXL_V4.0", 
            model_type="diffusion_text2img",
            use_ip_adapter=True,
            ip_adapter_config={
                "repo_id": "h94/IP-Adapter",
                "subfolder": "sdxl_models",
                "weight_name": "ip-adapter_sdxl.bin",
                "scale": 0.66
            }
        )        
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

        logger.info("✅ 이미지 생성기 파이프라인 초기화 완료")
    
    def generate_image(self,
            product: dict,
            image_path: str,
            prompt_mode: str = "human",
            output_dir: str = "./backend/data/output/",
        ) -> dict:
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
                generator=self.generator,
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
        return {"image": result_image, "image_path": save_path}

    def generate_vton(self,
        model_image_path: str, 
        ip_image_path: str, 
        mask_image_path: str, 
        output_dir="./backend/data/output",
        ) -> dict:
        # 1. 의류 이미지 로드
        logger.debug(f"🛠️ 이미지 로드 시작")
        model_image = load_image(model_image_path).convert("RGB")
        loaded_image, filename = self.image_loader.load_image(image_path=ip_image_path, target_size=None)
        mask_image = load_image(mask_image_path)
        logger.info("✅ IP 이미지 로드 완료")

        # 2. 배경 제거
        logger.debug(f"🛠️ 배경 제거 시작")
        ip_image, removed_bg_path = self.background_handler.remove_background(
            input_image=loaded_image,
            original_filename=filename,
        )

        if ip_image is None:
            logger.error("❌ 배경 제거 실패")
            return False
        logger.info(f"✅ 배경 제거 완료: {removed_bg_path}")

        # Depth 생성
        depth_image = self.midas_detector(model_image).resize((512, 768)).convert("RGB")

        # 3. VTON 실행
        logger.debug("🛠️ vton 실행 시작")
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
            image=model_image,
            mask_image=mask_image,
            ip_adapter_image=ip_image,
            control_image=depth_image,
            controlnet_conditioning_scale=0.7,
            strength=0.99,
            guidance_scale=7.5,
            num_inference_steps=100,
            generator=self.generator  # 고정 시드 적용
        ).images[0]

        os.makedirs(output_dir, exist_ok=True)
        name_without_ext, _ = os.path.splitext(filename)
        save_path = os.path.join(output_dir, f"{name_without_ext}_vton.png")
        result_image.save(save_path)
        logger.info(f"✅ 이미지가 {save_path}에 생성되었습니다.")
        return {"image": result_image, "image_path": save_path}