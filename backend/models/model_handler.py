import os
import torch
from dotenv import load_dotenv
from transformers import AutoModel, AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from diffusers import (
    AutoPipelineForInpainting,
    AutoPipelineForText2Image,
    ControlNetModel,
    StableDiffusionPipeline,
    AutoencoderKL
)
from controlnet_aux import MidasDetector
from peft import PeftModel
from utils.logger import get_logger

logger = get_logger(__name__)

load_dotenv()

MODEL_LOADERS = {
    "diffusion_pipeline": AutoPipelineForInpainting,
    "diffusion_text2img": AutoPipelineForText2Image,
    "vae": AutoencoderKL,
    "controlnet": ControlNetModel,
    "casual_lm": AutoModelForCausalLM,
    "encoder": AutoModel,
}

def download_model(
        model_id: str, 
        model_type: str = "diffusion_text2img",
        save_dir: str = "./backend/models",
        use_4bit: bool = False
    ):
    """
    Hugging Face에서 모델을 다운로드하여 지정된 경로에 저장
    모델 유형에 따라 확장 가능하도록 설계
    CPU/GPU 환경에 따라 torch_dtype을 설정

    Args:
        model_id (str): Hugging Face 모델 ID (예: "stabilityai/stable-diffusion-xl-base-1.0").
        model_type (str): 모델 유형 (예: "diffusion_text2img", "causal_lm", "encoder" 등).
        save_dir (str, optional): 모델을 저장할 기본 디렉토리 경로.
                                  기본값은 "./backend/models".

    Returns:
        str: 모델이 저장된 최종 경로. 다운로드 또는 저장에 실패하면 None 반환.
    """
    if model_type not in MODEL_LOADERS:
        logger.error(f"❌ 지원하지 않는 모델 유형: {model_type}")
        return None

    model_name_for_path = model_id.split("/")[-1]
    model_save_path = os.path.join(save_dir, model_name_for_path)

    if os.path.exists(model_save_path) and os.listdir(model_save_path):
        logger.info(f"✅ 모델 {model_id}이(가) 이미 {save_dir}에 존재")
        return model_save_path

    logger.debug(f"🛠️ 모델 {model_id}를 {save_dir}에 다운로드 시작")

    token = os.getenv("HF_TOKEN")
    if token is None:
        logger.warning("⚠️ Hugging Face API 토큰(HF_TOKEN)이 .env에 정의되어 있지 않습니다.")

    # GPU체크
    load_kwargs = {}
    if torch.cuda.is_available():
        load_kwargs["torch_dtype"] = torch.float16
        logger.info("✅ GPU를 사용하여 모델을 다운로드")
    else: 
        load_kwargs["torch_dtype"] = torch.float32
        logger.info("✅ CPU를 사용하여 모델을 다운로드")
        
    if model_type == "casual_lm" and use_4bit:
        load_kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16
        )

    try:
        loader_cls = MODEL_LOADERS[model_type]
        model = loader_cls.from_pretrained(model_id, token=token, **load_kwargs)
        model.save_pretrained(model_save_path)
        logger.info(f"✅ {model_type} 모델 '{model_id}' 저장 완료: {model_save_path}")
        return model_save_path

    except Exception as e:
        logger.error(f"❌ 모델 다운로드 실패 ({model_id}): {e}")
        return None


def load_model(
        model_path: str,
        model_type: str = "diffusion_text2img",
        use_4bit: bool = False
    ):
    """
    저장된 모델 디렉토리에서 모델을 불러옵니다.

    Args:
        model_path (str): 사전에 저장된 모델 디렉토리 경로
        model_type (str): 모델 유형 ("diffusion_text2img", "causal_lm", "encoder" 등)

    Returns:
        model: 로드된 모델 객체. 실패 시 None 반환
    """
    if not os.path.exists(model_path):
        logger.error(f"❌ 모델 경로 '{model_path}'가 존재하지 않습니다.")
        return None

    if model_type not in MODEL_LOADERS:
        logger.error(f"❌ 지원하지 않는 model_type: {model_type}")
        return None

    load_kwargs = {}
    if torch.cuda.is_available():
        load_kwargs["torch_dtype"] = torch.float16
        logger.info("✅ GPU를 사용하여 모델을 로드")
    else: 
        load_kwargs["torch_dtype"] = torch.float32
        logger.info("✅ CPU를 사용하여 모델을 로드")

    if model_type == "diffusion_text2img" or model_type == "diffusion_pipeline":
        load_kwargs["device_map"] = "balanced"
    elif model_type == "controlnet":
        load_kwargs["device_map"] = "cuda"
    elif model_type == "casual_lm" and use_4bit:
        load_kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16
        )
    else:
        load_kwargs["device_map"] = "auto"

    try:
        model = MODEL_LOADERS[model_type].from_pretrained(model_path, **load_kwargs)
        logger.info(f"✅ 모델이 '{model_path}'에서 로드")
        return model
    except Exception as e:
        logger.error(f"❌ 모델 로딩 중 오류 발생: {e}")
        return None


def get_model_pipeline(
        model_id: str,
        model_type: str = "diffusion_text2img",
        use_ip_adapter: bool = True,
        ip_adapter_config: dict = None,
        lora_path: str = None,
        use_4bit: bool = False,
        save_dir: str = "./backend/models"
    ):
    """
    Hugging Face 모델을 다운로드 및 로드하여 파이프라인 객체를 반환합니다.
    필요한 경우 IP-Adapter를 자동으로 주입합니다.

    이 함수는 다음을 수행합니다:
    1. download_model()을 사용해 지정된 모델을 다운로드합니다.
    2. load_model()을 통해 로컬 모델 디렉토리에서 모델을 로드합니다.
    3. 옵션에 따라 IP-Adapter를 주입하여 모델 기능을 확장합니다.

    Args:
        model_id (str): Hugging Face 모델 ID (예: "stabilityai/stable-diffusion-xl-base-1.0").
        model_type (str, optional): 모델 유형. 기본값은 "diffusion_text2img".
            - 지원되는 값: "diffusion_text2img", "diffusion_pipeline", "vae", "controlnet" 등.
        use_ip_adapter (bool, optional): True일 경우 IP-Adapter를 로드하고 주입합니다. 기본값은 True.
        ip_adapter_config (dict, optional): IP-Adapter 설정 값.
            - 예시:
                {
                    "repo_id": "h94/IP-Adapter",
                    "subfolder": "sdxl_models",
                    "weight_name": "ip-adapter_sdxl.bin",
                    "scale": 0.8
                }

    Returns:
        model_pipeline (object): 로드된 모델 파이프라인 객체.
            - IP-Adapter가 활성화된 경우, image_proj_model 속성을 포함.
        None: 모델 다운로드 또는 로드 실패 시 None 반환.

    Raises:
        Exception: IP-Adapter 로딩 중 발생한 예외는 warning으로 로깅됩니다.
    """    
    model_path = download_model(model_id=model_id, model_type=model_type, save_dir=save_dir, use_4bit=use_4bit)
    
    if model_path is None:
        logger.error("❌ 모델 경로가 None입니다. 로딩을 중단합니다.")
        return None

    model_pipeline = load_model(model_path=model_path, model_type=model_type, use_4bit=use_4bit)

    # LoRA 어댑터 연결
    if lora_path and model_type == "casual_lm":
        try:
            model_pipeline = PeftModel.from_pretrained(model_pipeline, lora_path, local_files_only=True)
            model_pipeline.eval()
            logger.info(f"✅ LLM용 LoRA 어댑터 적용 완료: {lora_path}")
        except Exception as e:
            logger.error(f"❌ LoRA 어댑터 로딩 실패: {e}")
            return None

    # IP-Adapter 주입 (옵션)
    if use_ip_adapter and not hasattr(model_pipeline, "image_proj_model"):
        try:
            adapter_config = ip_adapter_config or {
                "repo_id": "h94/IP-Adapter",
                "subfolder": "sdxl_models",
                "weight_name": "ip-adapter_sdxl.bin",
                "scale": 0.7,
            }
            model_pipeline.load_ip_adapter(
                adapter_config["repo_id"],
                subfolder=adapter_config["subfolder"],
                weight_name=adapter_config["weight_name"],
            )
            model_pipeline.set_ip_adapter_scale(adapter_config["scale"])
            model_pipeline.enable_vae_tiling()
            model_pipeline.enable_attention_slicing()
            model_pipeline.enable_xformers_memory_efficient_attention()
            logger.info("✅ IP-Adapter 주입 및 메모리 최적화 옵션 적용 완료")
        except Exception as e:
            logger.warning(f"⚠️ IP-Adapter 주입 및 메모리 최적화 옵션 적용 실패: {e}")
            
    return model_pipeline


def get_vton_pipeline(
    pipeline_model: str = "diffusers/stable-diffusion-xl-1.0-inpainting-0.1",
    vae_model: str = "madebyollin/sdxl-vae-fp16-fix",
    controlnet_model: str = "diffusers/controlnet-depth-sdxl-1.0",
    midas_model: str = "lllyasviel/ControlNet",
    ip_adapter_config: dict = {
        "repo_id": "h94/IP-Adapter",
        "subfolder": "sdxl_models",
        "weight_name": "ip-adapter_sdxl.bin",
        "scale": 0.8
    },
    lora_config: dict = {
        "repo_id": "Norod78/weird-fashion-show-outfits-sdxl-lora",
        "weight_name": "sdxl-WeirdOutfit-Dreambooh.safetensors"
    },
):
    """
    Stable Diffusion 기반 VTON 파이프라인을 한 번에 준비합니다.
    (다운로드 + 로드 + 주입 + IP-Adapter + LoRA 적용)

    Args:
        pipeline_model (str): Inpainting 파이프라인 모델 ID
        vae_model (str): VAE 모델 ID
        controlnet_model (str): ControlNet 모델 ID
        ip_adapter_config (dict): IP-Adapter 설정 {repo_id, subfolder, weight_name, scale}
        lora_config (dict): LoRA 설정 {repo_id, weight_name}
        save_dir (str): 모델 저장 기본 경로

    Returns:
        pipeline: GPU 로드 완료된 최종 파이프라인
    """
    logger.debug("🛠️ vton 파이프라인 구성요소 다운로드 및 로딩 시작")

    # 다운로드
    logger.debug("🛠️ 파이프라인 다운로드 시작")
    pipeline_path = download_model(pipeline_model, model_type="diffusion_pipeline")
    vae_path = download_model(vae_model, model_type="vae")
    controlnet_path = download_model(controlnet_model, model_type="controlnet")

    if not all([pipeline_path, vae_path, controlnet_path]):
        logger.error("❌ 다운로드 실패: 하나 이상의 모델이 준비되지 않음")
        return None

    # 로드
    logger.debug("🛠️ 파이프라인 로드 시작")
    vae = AutoencoderKL.from_pretrained(vae_path, torch_dtype=torch.float16)
    pipeline = AutoPipelineForInpainting.from_pretrained(
        pipeline_path,
        vae=vae,
        torch_dtype=torch.float16,
        use_safetensors=True
    ).to("cuda")
    controlnet = ControlNetModel.from_pretrained(controlnet_path, torch_dtype=torch.float16)

    # 주입
    logger.debug("🛠️ 구성요소 주입 시작")
    pipeline.controlnet = controlnet

    # 메모리 최적화/ 속도 희생
    # pipeline.enable_attention_slicing()
    pipeline.enable_vae_tiling()

    # IP-Adapter 적용
    try:
        pipeline.load_ip_adapter(
            ip_adapter_config["repo_id"],
            subfolder=ip_adapter_config.get("subfolder", "sdxl_models"),
            weight_name=ip_adapter_config["weight_name"]
        )
        pipeline.set_ip_adapter_scale(ip_adapter_config.get("scale", 0.8))
        logger.info("✅ IP-Adapter 적용 완료")
    except Exception as e:
        logger.warning(f"⚠️ IP-Adapter 적용 실패: {e}")

    # LoRA 적용
    try:
        pipeline.load_lora_weights(
            lora_config["repo_id"],
            weight_name=lora_config["weight_name"]
        )
        logger.info("✅ LoRA 적용 완료")
    except Exception as e:
        logger.warning(f"⚠️ LoRA 적용 실패: {e}")

    midas_detector = MidasDetector.from_pretrained(midas_model)

    return pipeline, midas_detector