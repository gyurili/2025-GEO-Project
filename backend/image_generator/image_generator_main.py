import yaml
import os
import sys
import datetime
import torch
import gc
from PIL import Image
from diffusers.utils import load_image

from utils.logger import get_logger
from backend.image_generator.image_loader import ImageLoader
from backend.image_generator.background_handler import BackgroundHandler
from backend.image_generator.prompt_builder import generate_prompts
from backend.image_generator.hash_utils import generate_cache_key
from backend.models.model_handler import get_model_pipeline, get_vton_pipeline

"""
generate_vton는 사용하지 않음
"""

logger = get_logger(__name__)

class ImgGenPipeline:
    """
    이미지 생성 및 가상 착용(VTON) 기능을 제공하는 파이프라인 클래스.

    주요 기능:
    - 이미지 로드 및 배경 제거
    - 텍스트 프롬프트 생성
    - Stable Diffusion 기반 이미지 생성
    - ControlNet 및 IP-Adapter 기반 VTON 기능 제공
    """

    def __init__(self):
        """
        ImgGenPipeline 초기화:
        - 이미지 로더, 배경 제거기 초기화
        - Stable Diffusion Image-to-Image 파이프라인 로드 (IP-Adapter 포함)
        """
        logger.debug("🛠️ 이미지 생성기 파이프라인 초기화 시작")

        # 유틸리티 초기화
        self.image_loader = ImageLoader()
        self.background_handler = BackgroundHandler()

        # Diffusion 모델 파이프라인 로드
        try:
            logger.info("🛠️ Diffusion Pipeline 로딩 시작")
            self.diffusion_pipeline = get_model_pipeline(
                model_id="SG161222/RealVisXL_V5.0",
                model_type="diffusion_text2img",
                use_ip_adapter=True,
                ip_adapter_config={
                    "repo_id": "h94/IP-Adapter",
                    "subfolder": "sdxl_models",
                    "weight_name": "ip-adapter_sdxl.bin",
                    "scale": 0.7
                }
            )
            logger.info("✅ Diffusion Pipeline 로딩 완료")
        except Exception as e:
            logger.error(f"❌ Diffusion Pipeline 로딩 실패: {e}")
            self.diffusion_pipeline = None

        # # VTON 파이프라인 로드
        # try:
        #     logger.debug("🛠️ VTON 파이프라인 및 MidasDetector 로딩 시작")
        #     self.vton_pipeline, self.midas_detector = get_vton_pipeline(
        #         pipeline_model="diffusers/stable-diffusion-xl-1.0-inpainting-0.1",
        #         vae_model="madebyollin/sdxl-vae-fp16-fix",
        #         controlnet_model="diffusers/controlnet-depth-sdxl-1.0",
        #         midas_model="lllyasviel/ControlNet",
        #         ip_adapter_config={
        #             "repo_id": "h94/IP-Adapter",
        #             "subfolder": "sdxl_models",
        #             "weight_name": "ip-adapter_sdxl.bin",
        #             "scale": 0.75
        #         },
        #         lora_config={
        #             "repo_id": "Norod78/weird-fashion-show-outfits-sdxl-lora",
        #             "weight_name": "sdxl-WeirdOutfit-Dreambooh.safetensors"
        #         },
        #     )
        #     logger.info("✅ VTON 파이프라인 및 MidasDetector 로딩 완료")
        # except Exception as e:
        #     logger.error(f"❌ VTON 파이프라인 및 MidasDetector 로딩 실패: {e}")
        #     self.diffusion_pipeline = None

        logger.info("✅ 이미지 생성기 파이프라인 초기화 완료")
    
    def generate_image(self,
            product: dict,
            prompt_mode: str = "human",
            output_dir: str = "./backend/data/output/",
            seed: int = 42,
        ) -> dict:
        """
        product['image_path_list']의 각 이미지를 기반으로 새로운 이미지를 생성합니다.

        Args:
            product (dict): 상품 정보를 담은 딕셔너리 (예: {"name": "셔츠", ...})
            prompt_mode (str): 프롬프트 생성 모드 ("human" 또는 "background"), 기본값 "human"
            output_dir (str): 생성된 이미지를 저장할 디렉토리 경로, 기본값 "./backend/data/output/"
            seed (int): 랜덤 시드 값 (재현성 확보용), 기본값 42

        Returns:
            dict: 생성된 이미지 및 저장 경로를 포함하는 딕셔너리:
                  {"image": PIL.Image, "image_path": str}
                  실패 시 {"image": None, "image_path": None} 반환.
        """
        logger.debug("🛠️ generate_image() 시작")
        result = {"image_paths": []}

        image_path_list = product.get("image_path_list", [])
        if not image_path_list:
            logger.error("❌ 이미지 리스트가 비어 있습니다.")
            return result

        for idx, image_path in enumerate(image_path_list):
            logger.debug(f"🛠️ {idx+1}/{len(image_path_list)}번째 이미지 생성 시작: {image_path}")
            single_result = self._generate_single_image(
                product=product,
                image_path=image_path,
                prompt_mode=prompt_mode,
                output_dir=output_dir,
                seed=seed,
            )
            if single_result["image"]:
                result["image_paths"].append(single_result["image_path"])
                logger.info(f"✅ {idx+1}/{len(image_path_list)}번째 이미지 생성 완료: {single_result['image_path']}")

                # 메모리 해제
                del single_result
                gc.collect()
                torch.cuda.empty_cache()
            else:
                logger.error(f"❌ {idx+1}/{len(image_path_list)}번째 이미지 생성 실패: {image_path}")
        
        logger.info(f"✅ 총 {len(result['image_paths'])}/{len(image_path_list)} 이미지 생성 완료")
        return result


    def _generate_single_image(
        self,
        product: dict,
        image_path: str,
        prompt_mode: str,
        output_dir: str,
        seed: int,
    ) -> dict:
        """
        내부용 단일 이미지 생성 메서드,
        """
        result = {"image": None, "image_path": None}

        try:
            logger.debug(f"🛠️ _generate_single_image() 시작: {image_path}")

            # 0. 캐시 체크
            cache_key = generate_cache_key(product, prompt_mode, seed)
            name_without_ext, _ = os.path.splitext(os.path.basename(image_path))
            os.makedirs(output_dir, exist_ok=True)
            save_path = os.path.join(output_dir, f"{cache_key}_{name_without_ext}.png")

            if os.path.exists(save_path):
                logger.info(f"✅ 캐시 이미지 존재 확인: {save_path}")
                return {"image": Image.open(save_path), "image_path": save_path}

            # 1. 이미지 로더
            logger.debug(f"🛠️ 이미지 로드 시작")
            loaded_image, filename = self.image_loader.load_image(image_path=image_path, target_size=None)
            if loaded_image is None:
                logger.error("❌ 이미지 로드에 실패했습니다. 처리를 중단합니다.")
                return result
            logger.info("✅ 이미지 로드 성공.")

            # 2. 배경 제거
            logger.debug(f"🛠️ 배경 제거 시작")
            processed_image = self.background_handler.remove_background(input_image=loaded_image)
            if processed_image is None:
                logger.error("❌ 배경 제거에 실패했습니다. 처리를 중단합니다.")
                return result
            logger.info("✅ 배경 제거 및 저장 성공.")

            # 3. 프롬프트 생성
            logger.debug("🛠️ 프롬프트 생성 시작")
            prompts = generate_prompts(product, mode=prompt_mode)
            if prompts:
                logger.info("✅ 프롬프트 생성 완료")
            else:
                prompts = {
                    "background_prompt": "",
                    "negative_prompt": "",
                }
                logger.warning("⚠️ 프롬프트 생성 실패. 기본 프롬프트로 실행합니다.")

            # RGBA → RGB
            if processed_image.mode != 'RGB':
                # logger.warning("⚠️ processed_image를 RGB로 변환")
                processed_image = processed_image.convert("RGB")

            logger.info(f"✅ 랜덤 시드: {seed}")
            generator = torch.manual_seed(seed)

            # 4. 이미지 생성
            if not self.diffusion_pipeline:
                logger.error("❌ Diffusion Pipeline이 초기화되지 않았습니다. 처리를 중단합니다.")
                logger.debug(f"🛠️ Pipeline 상태: {type(self.diffusion_pipeline)}")
                return result
            
            logger.debug(f"🛠️ Pipeline 확인됨: {type(self.diffusion_pipeline)}")
            logger.debug("🛠️ 모델 파이프라인으로 이미지 생성 시작")
            
            # 파라미터 디버깅
            logger.debug(f"🛠️ prompt 타입: {type(prompts.get('background_prompt'))}, 내용: {prompts.get('background_prompt', '')[:100]}...")
            logger.debug(f"🛠️ negative_prompt 타입: {type(prompts.get('negative_prompt'))}, 내용: {prompts.get('negative_prompt', '')[:100]}...")
            logger.debug(f"🛠️ ip_adapter_image 타입: {type(processed_image)}, 모드: {processed_image.mode}, 크기: {processed_image.size}")
            logger.debug(f"🛠️ generator 타입: {type(generator)}")
            
            try:
                pipeline_result = self.diffusion_pipeline(
                    prompt=prompts["background_prompt"],        # 생성할 이미지의 주요 텍스트 설명 (이미지 품질과 콘셉트에 직접적 영향)
                    negative_prompt=prompts["negative_prompt"], # 생성 시 배제할 요소(예: 'blurry', 'text', 'logo') → 품질 안정성 향상
                    ip_adapter_image=processed_image,           # IP-Adapter 입력 이미지 (제품 구조, 색상, 특징 반영) → 유사성 높임
                    width=768,                                  # 출력 이미지 가로 크기 (해상도 ↑ 시 품질 ↑, VRAM ↑, 속도 ↓)
                    height=768,                                 # 출력 이미지 세로 크기 (동일하게 해상도 영향)
                    num_inference_steps=25,                     # 디퓨전 스텝 수 (높을수록 디테일 ↑, 속도 ↓, VRAM ↑) → 권장 30~50
                    guidance_scale=5,                           # 프롬프트 강조 강도 (높으면 프롬프트 반영 ↑, 낮으면 창의성 ↑), 너무 높으면 비현실적 아티팩트 발생 가능 (보통 5~8)
                    num_images_per_prompt=1,                    # 한 번의 추론에서 생성할 이미지 개수 (↑시 VRAM 부담 커짐)
                    generator=generator,                        # 랜덤 시드 고정 (재현성 확보) → 동일 설정 시 항상 같은 이미지 생성
                )
                
                logger.debug(f"🛠️ Pipeline 결과 타입: {type(pipeline_result)}")
                if hasattr(pipeline_result, 'images'):
                    logger.debug(f"🛠️ pipeline_result.images 타입: {type(pipeline_result.images)}")
                    logger.debug(f"🛠️ pipeline_result.images 길이: {len(pipeline_result.images) if hasattr(pipeline_result.images, '__len__') else 'N/A'}")
                    if pipeline_result.images and len(pipeline_result.images) > 0:
                        logger.debug(f"🛠️ pipeline_result.images[0] 타입: {type(pipeline_result.images[0])}")
                        
                result_image = pipeline_result.images[0]
                logger.info("✅ 이미지 생성 성공")
            except Exception as e:
                logger.error(f"❌ 이미지 생성 중 에러 발생: {e}")
                logger.debug(f"🛠️ 오류 타입: {type(e)}")
                logger.debug(f"🛠️ processed_image 타입: {type(processed_image)}")
                logger.debug(f"🛠️ processed_image 모드: {processed_image.mode if hasattr(processed_image, 'mode') else 'N/A'}")
                
                # 추가 스택 트레이스 로깅
                import traceback
                logger.debug(f"🛠️ 스택 트레이스:\n{traceback.format_exc()}")
                return result

            result_image.save(save_path)
            logger.info(f"✅ 이미지가 {save_path}에 생성되었습니다.")

            logger.debug("✅ _generate_single_image() 완료")
            return {"image": result_image, "image_path": save_path}

        except Exception as e:
            logger.error(f"❌ _generate_single_image() 실패: {e}")
            return result


    def generate_vton(self,
        model_image_path: str, 
        ip_image_path: str, 
        mask_image_path: str, 
        output_dir="./backend/data/output",
        seed: int = 42,
        ) -> dict:
        """
        Virtual Try-On(VTON): 의류 이미지를 착용한 모델 이미지를 생성합니다.

        Args:
            model_image_path (str): 모델 이미지 경로
            ip_image_path (str): 의류 이미지 경로
            mask_image_path (str): 마스크 이미지 경로
            output_dir (str): 생성된 이미지를 저장할 디렉토리 경로
            seed (int): 랜덤 시드 값 (재현성 확보용), 기본값 42

        Returns:
            dict: 생성된 이미지 및 저장 경로를 포함하는 딕셔너리:
                  {"image": PIL.Image, "image_path": str}
                  실패 시 {"image": None, "image_path": None} 반환.
        """
        logger.debug("🛠️ generate_vton() 시작")
        result = {"image": None, "image_path": None}

        try:
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

            logger.info(f"✅ 랜덤 시드: {seed}")
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


        except Exception as e:
            logger.error(f"❌ generate_vton() 실패: {e}")

        return result