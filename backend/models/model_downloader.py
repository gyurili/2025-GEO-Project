import os
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from diffusers import DiffusionPipeline
from utils.logger import get_logger

logger = get_logger(__name__)

def download_model(model_id: str, save_dir: str = "/home/ubuntu/2025-GEO-Project/backend/models")
    """
    Hugging Face에서 Stable Diffusion XL (SDXL) 모델을 다운로드하여 지정된 경로에 저장합니다.
    CPU/GPU 환경에 따라 torch_dtype을 설정합니다.

    Args:
        model_id (str): Hugging Face 모델 ID (예: "stabilityai/stable-diffusion-xl-base-1.0").
        save_dir (str, optional): 모델을 저장할 기본 디렉토리 경로.
                                  기본값은 "/home/ubuntu/2025-GEO-Project/backend/models".

    Returns:
        str: 모델이 저장된 최종 경로. 다운로드 또는 저장에 실패하면 None 반환.
    """
    model_name_for_path = model_id.split("/")[-1]
    model_save_path = os.path.join(save_dir, model_name_for_path)

    if os.path.exists(model_save_path) and os.listdir(model_save_path):
        logger.info(f"✅ 모델 {model_id}이(가) 이미 {save_dir}에 존재합니다.")
        return model_save_path

    logger.debug(f"🛠️ 모델 {model_id}를 {save_dir}에 다운로드")

    # GPU체크
    load_kwargs = {}
    if torch.cuda.is_available():
        load_kwargs["torch_dtype"] = torch.float16
        logger.info("✅ GPU를 사용하여 모델을 로드합니다.")
    else: 
        load_kwargs["torch_dtype"] = torch.float32
        logger.info("✅ CPU를 사용하여 모델을 로드합니다.")
    load_kwargs["device_map"] = "auto"

    try:
        pipeline = DiffusionPipeline.from_pretrained(
            model_id,
            **load_kwargs
        )

        pipeline.save_pretrained(model_save_path)
        logger.info(f"✅ 모델 '{model_id}'이(가) '{model_save_path}'에 저장됨")
    except Exception as e:
        logger.error(f"❌ 모델 '{model_id}' 다운로드 및 저장 중 오류 발생: {e}")
        return None
        
# # 모델과 토크나이저 다운로드 및 저장
# model = AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased")
# tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")

# # 모델 저장
# model.save_pretrained(MODEL_DIR)
# tokenizer.save_pretrained(MODEL_DIR)

# print(f"모델과 토크나이저가 {MODEL_DIR}에 저장되었습니다.")

# load_model.py

# from transformers import AutoModelForSequenceClassification, AutoTokenizer

# # 공용 폴더 경로
# MODEL_DIR = "/home/shared/models/distilbert-base-uncased"

# # 모델과 토크나이저 로드
# model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
# tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)

# print("모델과 토크나이저를 공용 폴더에서 불러왔습니다.")