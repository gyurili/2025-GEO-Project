from diffusers import AutoPipelineForInpainting, AutoencoderKL
from diffusers.utils import load_image
import datetime
import torch
from PIL import Image
from backend.image_generator.core.background_handler import BackgroundHandler

vae = AutoencoderKL.from_pretrained("madebyollin/sdxl-vae-fp16-fix", torch_dtype=torch.float16)

pipeline = AutoPipelineForInpainting.from_pretrained("diffusers/stable-diffusion-xl-1.0-inpainting-0.1",
                                                     vae=vae,
                                                     torch_dtype=torch.float16,
                                                     variant="fp16",
                                                     use_safetensors=True
                                                    ).to("cuda")

pipeline.load_ip_adapter("h94/IP-Adapter", subfolder="sdxl_models", weight_name="ip-adapter_sdxl.bin", low_cpu_mem_usage=True)

image = load_image('https://cdn-uploads.huggingface.co/production/uploads/648a824a8ca6cf9857d1349c/jpFBKqYB3BtAW26jCGJKL.jpeg').convert("RGB")

ip_image = load_image('/home/user/2025-GEO-Project/backend/data/input/suit.jpg').convert("RGB")

mask_image= load_image('/home/user/2025-GEO-Project/backend/data/input/model_mask.png')

pipeline.set_ip_adapter_scale(2.5)
pipeline.load_lora_weights('Rac11m/sd-tryon-model-lora-sdxl', weight_name='pytorch_lora_weights.safetensors')

now = datetime.datetime.now()
seed = int(now.strftime("%Y%m%d%H%M%S"))
generator = torch.manual_seed(seed)
print(f"🛠️ 날짜 시드: {seed}")

final_image = pipeline(
    prompt="photorealistic", # , perfect body, beautiful skin, realistic skin, natural skin
    negative_prompt="ugly, bad quality, bad anatomy, deformed body, deformed hands, deformed feet, deformed face, deformed clothing, deformed skin, bad skin, leggings, tights, stockings",
    image=image,
    mask_image=mask_image,
    ip_adapter_image=ip_image,
    strength=0.99,
    guidance_scale=7.5,
    num_inference_steps=100,
    generator=generator,
).images[0]
final_image.save("final_image.png")

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