import os
import torch
from dotenv import load_dotenv
from diffusers import DiffusionPipeline, AutoPipelineForText2Image
from transformers import AutoModel, AutoTokenizer, AutoModelForCausalLM
from huggingface_hub import snapshot_download
from utils.logger import get_logger

logger = get_logger(__name__)

load_dotenv()

MODEL_LOADERS = {
    "diffusion": AutoPipelineForText2Image,
    "casual_lm": AutoModelForCausalLM,
    "encoder": AutoModel,
}

def download_model(
        model_id: str, 
        model_type: str = "diffusion",
        save_dir: str = "/home/user/2025-GEO-Project/backend/models"
    ):
    """
    Hugging Face에서 모델을 다운로드하여 지정된 경로에 저장
    모델 유형에 따라 확장 가능하도록 설계
    CPU/GPU 환경에 따라 torch_dtype을 설정

    Args:
        model_id (str): Hugging Face 모델 ID (예: "stabilityai/stable-diffusion-xl-base-1.0").
        model_type (str): 모델 유형 (예: "diffusion", "causal_lm", "encoder" 등).
        save_dir (str, optional): 모델을 저장할 기본 디렉토리 경로.
                                  기본값은 "/home/user/2025-GEO-Project/backend/models".

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

    if model_type == "diffusion":
        pass
    else:
        load_kwargs["device_map"] = "auto"

    try:
        loader_cls = MODEL_LOADERS[model_type]
        model = loader_cls.from_pretrained(model_id, token=token, **load_kwargs)

        model.save_pretrained(model_save_path)
        logger.info(f"✅ 모델 '{model_id}'이(가) '{model_save_path}'에 저장")
        return model_save_path

    except Exception as e:
        logger.error(f"❌ 모델 '{model_id}' 다운로드 및 저장 중 오류 발생: {e}")
        return None


def load_model(
        model_path: str,
        model_type: str = "diffusion"
    ):
    """
    저장된 모델 디렉토리에서 모델을 불러옵니다.

    Args:
        model_path (str): 사전에 저장된 모델 디렉토리 경로
        model_type (str): 모델 유형 ("diffusion", "causal_lm", "encoder" 등)

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

    if model_type == "diffusion":
        load_kwargs["device_map"] = "balanced"
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
        model_type: str = "diffusion",
        use_ip_adapter: bool = True,
        ip_adapter_config: dict = None,
    ):
    model_path = download_model(model_id, model_type)
    if model_path is None:
        logger.error("❌ 모델 경로가 None입니다. 로딩을 중단합니다.")
        return None

    model_pipeline = load_model(model_path, model_type)

    # IP-Adapter 주입 (옵션)
    if use_ip_adapter and not hasattr(model_pipeline, "image_proj_model"):
        try:
            adapter_config = ip_adapter_config or {
                "repo_id": "h94/IP-Adapter",
                "subfolder": "sdxl_models",
                "weight_name": "ip-adapter_sdxl.bin",
                "scale": 0.8,
            }
            model_pipeline.load_ip_adapter(
                adapter_config["repo_id"],
                subfolder=adapter_config["subfolder"],
                weight_name=adapter_config["weight_name"],
            )
            model_pipeline.set_ip_adapter_scale(adapter_config["scale"])
            logger.info("✅ IP-Adapter 자동 주입 완료")
        except Exception as e:
            logger.warning(f"⚠️ IP-Adapter 자동 주입 실패: {e}")
            
    return model_pipeline