from diffusers import AutoPipelineForInpainting, AutoencoderKL, ControlNetModel
from controlnet_aux import MidasDetector
from diffusers.utils import load_image
import datetime
import torch
from PIL import Image
from utils.logger import get_logger

logger = get_logger(__name__)

try: 
    logger.debug("🛠️ 이미지 로딩")
    image = load_image('/home/user/2025-GEO-Project/backend/data/output/model_removed_bg.png').convert("RGB")
    ip_image = load_image('/home/user/2025-GEO-Project/backend/data/output/greendress_removed_bg.png').convert("RGB")
    mask_image= load_image('/home/user/2025-GEO-Project/backend/data/input/model_mask3.png')

    logger.debug("🛠️ Depth Detector 로딩")
    midas_detector = MidasDetector.from_pretrained("lllyasviel/ControlNet")
    control_image_depth = midas_detector(image)

    logger.debug("🛠️ VAE 로딩")
    vae = AutoencoderKL.from_pretrained("madebyollin/sdxl-vae-fp16-fix", torch_dtype=torch.float16)

    logger.debug("🛠️ ControlNet 로딩")
    controlnet = ControlNetModel.from_pretrained(
        "diffusers/controlnet-depth-sdxl-1.0",
        torch_dtype=torch.float16
    )

    logger.debug("🛠️ Pipeline 로딩")
    pipeline = AutoPipelineForInpainting.from_pretrained(
        "diffusers/stable-diffusion-xl-1.0-inpainting-0.1",
        vae=vae,
        torch_dtype=torch.float16,
        variant="fp16",
        use_safetensors=True
    ).to("cuda")

    logger.debug("🛠️ ControlNet 주입")
    pipeline.controlnet = controlnet

    logger.debug("🛠️ IP-Adapter 주입")
    pipeline.load_ip_adapter("h94/IP-Adapter", subfolder="sdxl_models", weight_name="ip-adapter_sdxl.bin", low_cpu_mem_usage=True)
    pipeline.set_ip_adapter_scale(2.0)

    logger.debug("🛠️ LoRA 주입")
    pipeline.load_lora_weights('Norod78/weird-fashion-show-outfits-sdxl-lora', weight_name='sdxl-WeirdOutfit-Dreambooh.safetensors')

    now = datetime.datetime.now()
    seed = int(now.strftime("%Y%m%d%H%M%S"))
    generator = torch.manual_seed(seed)
    logger.debug(f"🛠️ 날짜 시드: {seed}")
    
    logger.debug(f"🛠️ 이미지 생성 시작")
    final_image = pipeline(
        prompt="photorealistic, perfect body, beautiful skin, realistic skin, natural skin, a man wearing blue suit.",
        negative_prompt="ugly, bad quality, bad anatomy, deformed body, deformed hands, deformed feet, deformed face, deformed clothing, deformed skin, bad skin, leggings, tights, stockings",
        width=512,
        height=768,
        image=image,
        mask_image=mask_image,
        ip_adapter_image=ip_image,
        control_image=control_image_depth,
        controlnet_conditioning_scale=0.7,
        strength=0.99,
        guidance_scale=7.5,
        num_inference_steps=100,
        generator=generator,
    ).images[0]
    logger.info(f"✅ 이미지 생성 완료")
    final_image.save("final_image.png")
except Exception as e:
    logger.warning(f"❌ 에러 발생: {e}")

# def virtual_try_on(img, clothing, mask_img, prompt, negative_prompt, ip_scale=1.0, strength=0.99, guidance_scale=7.5, steps=100):
#     pipeline.set_ip_adapter_scale(ip_scale)
#     images = pipeline(
#         prompt=prompt,
#         negative_prompt=negative_prompt,
#         image=img,
#         mask_image=mask_img,
#         ip_adapter_image=clothing,
#         strength=strength,
#         guidance_scale=guidance_scale,
#         num_inference_steps=steps,
#     ).images
#     return images[0]

# result = virtual_try_on(img=image, 
#                         clothing=ip_image,
#                         mask_img=mask_image,
#                         prompt="photorealistic, perfect body, beautiful skin, realistic skin, natural skin",
#                         negative_prompt="ugly, bad quality, bad anatomy, deformed body, deformed hands, deformed feet, deformed face, deformed clothing, deformed skin, bad skin, leggings, tights, stockings")

# result.save("test.png")