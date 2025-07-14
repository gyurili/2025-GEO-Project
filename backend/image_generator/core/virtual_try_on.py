import datetime
import os
import torch
from PIL import Image
from diffusers import AutoPipelineForInpainting, AutoencoderKL, ControlNetModel
from controlnet_aux import MidasDetector
from diffusers.utils import load_image
from huggingface_hub import snapshot_download
from utils.logger import get_logger

logger = get_logger(__name__)

class VirtualTryOnPipeline:
    def __init__(self, model_dir="./backend/models"):
        """
        가상 피팅 파이프라인 초기화
        모든 모델은 "./backend/models" 경로에 다운로드되거나 로드됨
        """
        logger.debug("🛠️ VirtualTryOnPipeline 초기화 시작")
        self.model_dir = model_dir
        os.makedirs(self.model_dir, exist_ok=True)

        self.pipeline = None
        self.vae = None
        self.controlnet = None
        self.midas_detector = None
        logger.info(f"✅ VirtualTryOnPipeline 초기화 완료. 모델은 '{self.model_dir}'에서 로드/저장")
        self._load_models()

    def _download_and_load_models(self, model_name_or_path, subfolder=None, model_class=None, **kwargs):
        """
        모델을 로컬에 다운로드하거나 로드합니다.
        kwargs는 from_pretrained에 전달한 추가 인자입니다.
        """
        local_path = os.path.join(self.model_dir, model_name_or_path.replace("/", "_"))  # 로컬 폴더명 생성

        # 다운로드 확인
        if not os.path.exists(local_path):
            logger.debug(f"🛠️ {model_name_or_path} 모델 다운로드 중...")
            snapshot_download(repo_id=model_name_or_path, local_dir=local_path)
            logger.info(f"✅ {model_name_or_path} 다운로드 완료: {local_path}")
        else:
            logger.info(f"✅ {model_name_or_path} 모델이 이미 존재: {local_path}")
        
        if model_class:
            if subfolder: # 특정 서브폴더가 있는 경우
                return model_class.from_pretrained(os.path.join(local_path, subfolder), **kwargs)
            else: # 서브폴더 없이 바로 로드하는 경우
                return model_class.from_pretrained(local_path, **kwargs)
        return local_path

    def _load_models(self):
        """모든 필요한 모델들을 로컬에서 로드하거나 다운로드 합니다."""
        logger.debug("🛠️ VAE 로딩 시작")
        vae_path = self._download_and_load_models(
            "madebyollin/sdxl-vae-fp16-fix",
            model_class=AutoencoderKL,
            torch_dtype=torch.float16
        )
        self.vae = vae_path
        logger.info("✅ VAE 로딩 완료")

        logger.debug("🛠️ Depth Detector 로딩 시작")
        controlnet_aux_repo_path = self._download_and_load_models("lllyasviel/ControlNet")
        midas_model_dir_for_detector = os.path.join(controlnet_aux_repo_path, "annotator", "ckpts")
        self.midas_detector = MidasDetector.from_pretrained(midas_model_dir_for_detector, model_type="dpt_hybrid")
        logger.info("✅ Depth Detector 로딩 완료")

        logger.debug("🛠️ ControlNet (Depth) 로딩 시작")
        controlnet_depth_path = self._download_and_load_models(
            "diffusers/controlnet-depth-sdxl-1.0",
            model_class=ControlNetModel,
            torch_dtype=torch.float16
        )
        self.controlnet = controlnet_depth_path
        logger.info("✅ ControlNet (Depth) 로딩 완료")

        logger.debug("🛠️ Pipeline 로딩 시작")
        self.pipeline = AutoPipelineForInpainting.from_pretrained(
            "diffusers/stable-diffusion-xl-1.0-inpainting-0.1",
            vae=self.vae, # 로드된 VAE 객체 전달
            controlnet=self.controlnet, # 로드된 ControlNet 객체 전달
            torch_dtype=torch.float16,
            variant="fp16",
            use_safetensors=True
        ).to("cuda")
        logger.info("✅ Pipeline 로딩 완료")

        logger.debug("🛠️ IP-Adapter 모델 로딩 시작")
        ip_adapter_repo_path = self._download_and_load_models("h94/IP-Adapter")
        ip_adapter_model_path = os.path.join(ip_adapter_repo_path, "sdxl_models", "ip-adapter_sdxl.bin")
        self.pipeline.load_ip_adapter(
            ip_adapter_repo_path,
            subfolder="sdxl_models",
            weight_name="ip-adapter_sdxl.bin",
            low_cpu_mem_usage=True
        )
        self.pipeline.set_ip_adapter_scale(2.0)
        logger.info("✅ IP-Adapter 모델 로딩 완료")

        logger.debug("🛠️ LoRA 로딩 시작")
        lora_path = self._download_and_load_models(
            "Norod78/weird-fashion-show-outfits-sdxl-lora",
            model_class=None,
        )
        self.pipeline.load_lora_weights(lora_path, weight_name='sdxl-WeirdOutfit-Dreambooh.safetensors')
        logger.info("✅ LoRA 로딩 완료")
        logger.info("✅ 모든 모델 로딩 및 준비 완료.")

    def try_on(self, image_path, ip_image_path, mask_image_path, prompt, negative_prompt,
               width=512, height=768, controlnet_conditioning_scale=0.7,
               strength=0.99, guidance_scale=7.5, num_inference_steps=100, seed=None):
        """
        가상 피팅을 실행하고 결과 이미지를 반환합니다.
        """
        logger.debug("🛠️ 입력 이미지 로딩")
        image = load_image(image_path).convert("RGB")
        ip_image = load_image(ip_image_path).convert("RGB")
        mask_image = load_image(mask_image_path)

        logger.debug("🛠️ ControlNet 제어 이미지 생성")
        control_image_depth = self.midas_detector(image)

        if seed is None:
            now = datetime.datetime.now()
            seed = int(now.strftime("%Y%m%d%H%M%S"))
        generator = torch.manual_seed(seed)
        logger.debug(f"🛠️ 날짜 시드: {seed}")

        logger.debug(f"🛠️ 이미지 생성 시작")
        final_image = self.pipeline(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            image=image,
            mask_image=mask_image,
            ip_adapter_image=ip_image,
            control_image=control_image_depth,
            controlnet_conditioning_scale=controlnet_conditioning_scale,
            strength=strength,
            guidance_scale=guidance_scale,
            num_inference_steps=num_inference_steps,
            generator=generator,
        ).images[0]
        logger.info(f"✅ 이미지 생성 완료")
        return final_image


# try: 
#     logger.debug("🛠️ 이미지 로딩")
#     image = load_image('/home/user/2025-GEO-Project/backend/data/output/model_removed_bg.png').convert("RGB")
#     ip_image = load_image('/home/user/2025-GEO-Project/backend/data/output/greendress_removed_bg.png').convert("RGB")
#     mask_image= load_image('/home/user/2025-GEO-Project/backend/data/input/model_mask3.png')

#     logger.debug("🛠️ Depth Detector 로딩")
#     midas_detector = MidasDetector.from_pretrained("lllyasviel/ControlNet")
#     control_image_depth = midas_detector(image)

#     logger.debug("🛠️ VAE 로딩")
#     vae = AutoencoderKL.from_pretrained("madebyollin/sdxl-vae-fp16-fix", torch_dtype=torch.float16)

#     logger.debug("🛠️ ControlNet 로딩")
#     controlnet = ControlNetModel.from_pretrained(
#         "diffusers/controlnet-depth-sdxl-1.0",
#         torch_dtype=torch.float16
#     )

#     logger.debug("🛠️ Pipeline 로딩")
#     pipeline = AutoPipelineForInpainting.from_pretrained(
#         "diffusers/stable-diffusion-xl-1.0-inpainting-0.1",
#         vae=vae,
#         torch_dtype=torch.float16,
#         variant="fp16",
#         use_safetensors=True
#     ).to("cuda")

#     logger.debug("🛠️ ControlNet 주입")
#     pipeline.controlnet = controlnet

#     logger.debug("🛠️ IP-Adapter 주입")
#     pipeline.load_ip_adapter("h94/IP-Adapter", subfolder="sdxl_models", weight_name="ip-adapter_sdxl.bin", low_cpu_mem_usage=True)
#     pipeline.set_ip_adapter_scale(2.0)

#     logger.debug("🛠️ LoRA 주입")
#     pipeline.load_lora_weights('Norod78/weird-fashion-show-outfits-sdxl-lora', weight_name='sdxl-WeirdOutfit-Dreambooh.safetensors')

#     now = datetime.datetime.now()
#     seed = int(now.strftime("%Y%m%d%H%M%S"))
#     generator = torch.manual_seed(seed)
#     logger.debug(f"🛠️ 날짜 시드: {seed}")
    
#     logger.debug(f"🛠️ 이미지 생성 시작")
#     final_image = pipeline(
#         prompt="photorealistic, perfect body, beautiful skin, realistic skin, natural skin, a man wearing blue suit.",
#         negative_prompt="ugly, bad quality, bad anatomy, deformed body, deformed hands, deformed feet, deformed face, deformed clothing, deformed skin, bad skin, leggings, tights, stockings",
#         width=512,
#         height=768,
#         image=image,
#         mask_image=mask_image,
#         ip_adapter_image=ip_image,
#         control_image=control_image_depth,
#         controlnet_conditioning_scale=0.7,
#         strength=0.99,
#         guidance_scale=7.5,
#         num_inference_steps=100,
#         generator=generator,
#     ).images[0]
#     logger.info(f"✅ 이미지 생성 완료")
#     final_image.save("final_image.png")
# except Exception as e:
#     logger.warning(f"❌ 에러 발생: {e}")