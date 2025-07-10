import os
import sys
from PIL import Image
from rembg import remove

from utils.logger import get_logger
from .image_loader import ImageLoader

logger = get_logger(__name__)

"""
TODO: rembg의 파라미터 확인 후에 배경제거가 잘 되는 것으로 수정 필요
"""

class BackgroundHandler:
    """
    이미지에서 배경을 제거하거나, 단색 또는 이미지 배경을 추가하는 기능을 제공하는 클래스
    'rembg' 라이브러리를 활용하여 이미지의 배경을 제거
    """
    def __init__(self):
        """
        BackgroundHandler 클래스의 생성자
        """
        logger.debug("🛠️ BackgroundHandler 초기화 시작")
        logger.info("✅ BackgroundHandler 초기화 완료")

    def remove_background(
            self, 
            input_image: Image.Image, 
            original_filename: str, 
            output_dir: str = "backend/data/output/"
        ) -> Image.Image:
        """
        'rembg' 라이브러리를 사용하여 입력 이미지(PIL.Image.Image)에서 배경을 제거,
        투명 배경을 가진 PNG 이미지로 저장

        Args:
            input_image (PIL.Image.Image): 배경을 제거할 제품 이미지 객체 (RGB 또는 RGBA 모드)
            original_filename (str): 이미지 파일명 (출력 파일명 생성에 사용).
            output_dir (str, optional): 배경이 제거된 이미지를 저장할 경로. 기본 경로는 'backend/data/output/'에 저장
        
        Returns:
            PIL.Image.Image: 배경이 제거된 이미지 객체 (RGBA 모드)
                             오류 발생시 None 반환
        """
        logger.debug(f"🛠️ 배경 제거 시작")
        try:
            if input_image is None:
                logger.error(f"❌ 배경 제거를 위한 입력 이미지 객체가 None입니다.")
                return None
            
            output_image = remove(input_image, 
                                  alpha_matting=True, 
                                  bgcolor=(0, 0, 0, 0),
                                  alpha_matting_foreground_threshold=255,
                                  alpha_matting_background_threshold=0,
                                  alpha_matting_erode_size=100)

            # if output_image.getbbox():
            #     logger.debug("🛠️ 제거된 배경에 맞게 사이즈 조정")
            #     output_image = output_image.crop(output_image.getbbox())
            # else:
            #     logger.warning("⚠️ 배경 제거 후 이미지가 비어있습니다. 원본 이미지가 투명 배경이 아닌지 확인하세요.")
            #     return None
            
            os.makedirs(output_dir, exist_ok=True)

            # 파일명과 확장자 분리 (예: 'cake', '.jpg')
            name_without_ext, _ = os.path.splitext(original_filename)
            # 새 확장자를 붙여 최종 파일명 생성 (예: 'cake_removed_bg.png')
            filename = f"{name_without_ext}_removed_bg.png"

            save_path = os.path.join(output_dir, filename)
            output_image.save(save_path)

            logger.info(f"✅ 배경 제거 완료. 결과 이미지가 {save_path}에 저장되었습니다.")
            return output_image
        except Exception as e:
            logger.error(f"❌ 배경 제거 중 오류 발생: {e}")
            return None

    def add_color_background(
            self, 
            foreground_image: Image.Image, 
            color: tuple, 
            original_filename: str, 
            output_dir: str = "backend/data/output",
        ) -> Image.Image:
        """
        투명 배경을 가진 이미지에 단색 배경을 추가합니다.

        Args:
            foreground_image (PIL.Image.Image): 배경을 추가할 전경 이미지 객체 (RGBA 모드).
            color (tuple): 추가할 배경의 RGB 색상 튜플 (예: (255, 255, 255) for white).
            original_filename (str): 원본 이미지 파일명 (출력 파일명 생성에 사용).
            output_dir (str, optional): 결과 이미지를 저장할 디렉토리 경로.
                                        기본값은 'backend/data/output/'.

        Returns:
            PIL.Image.Image: 단색 배경이 추가된 이미지 객체 (RGB 모드). 오류 발생시 None 반환.
        """
        logger.debug(f"🛠️ 단색 배경 추가 시작. 색상(RGB): {color}")
        try:
            if foreground_image is None:
                logger.error(f"❌ 단색 배경 추가를 위한 전경 이미지 객체가 None입니다.")
                return None

            if foreground_image.mode != 'RGBA':
                logger.warning("⚠️ 전경 이미지가 RGBA 모드가 아닙니다. 투명도 정보가 손실될 수 있습니다.")
                foreground_image = foreground_image.convert('RGBA')
            
            # 단색 배경 이미지 생성
            background = Image.new('RGB', foreground_image.size, color)

            # 최종 이미지 생성
            final_image = Image.new('RGB', foreground_image.size)
            final_image.paste(background, (0, 0))
            final_image.paste(foreground_image, (0, 0), foreground_image)

            os.makedirs(output_dir, exist_ok=True)

            name_without_ext, _ = os.path.splitext(original_filename)
            color_name = "_".join(map(str, color)) if isinstance(color, tuple) else str(color) # 색상 이름을 파일명에 포함
            filename = f"{name_without_ext}_{color_name}_bg.png"
            
            save_path = os.path.join(output_dir, filename)
            final_image.save(save_path)

            logger.info(f"✅ 단색 배경 추가 완료. 결과 이미지가 {save_path}에 저장되었습니다.")
            return final_image
        except Exception as e:
            logger.error(f"❌ 단색 배경 추가 중 오류 발생: {e}")
            return None

    def create_mask_from_alpha(
            self,
            transparent_image: Image.Image,
            original_filename: str,
            output_dir: str = "backend/data/output/"
        ) -> Image.Image:
        """
        투명 배경 이미지에서 alpha 채널을 기반으로 inpainting용 마스크를 생성
        (제품 영역은 검정, 배경은 흰색)

        Args:
            transparent_image (PIL.Image.Image): 배경이 제거된 RGBA 이미지
            original_filename (str): 원본 파일명
            output_dir (str): 저장 경로

        Returns:
            PIL.Image.Image: 마스크 이미지 (mode=L), 배경은 흰색(255), 제품은 검정(0)
        """
        try:
            logger.debug("🛠️ 마스크 이미지 생성 시작")

            if transparent_image.mode != 'RGBA':
                transparent_image = transparent_image.convert("RGBA")

            # alpha 채널 추출 (투명도 → 제품은 불투명, 배경은 투명)
            alpha = transparent_image.getchannel("A")

            # 마스크 생성: 배경(투명, alpha=0)은 흰색(255), 제품(불투명, alpha>0)은 검정(0)
            mask = alpha.point(lambda p: 255 if p == 0 else 0).convert("L")

            # 저장
            os.makedirs(output_dir, exist_ok=True)
            name_without_ext, _ = os.path.splitext(original_filename)
            filename = f"{name_without_ext}_mask.png"
            save_path = os.path.join(output_dir, filename)
            mask.save(save_path)

            logger.info(f"✅ 마스크 이미지 생성 완료: {save_path}")
            return mask

        except Exception as e:
            logger.error(f"❌ 마스크 생성 중 오류 발생: {e}")
            return None


    def add_image_background(
            self, 
            foreground_image: Image.Image, 
            background_image: Image.Image, # 배경 이미지 객체를 직접 받음
            original_filename: str, # 전경 이미지의 원본 파일명
            background_filename: str, # 배경 이미지의 베이스 파일명 (예: "texture.jpg")
            output_dir: str = "backend/data/output",
            position: tuple = (0.5, 0.55), 
            max_scale: float = 0.5,
        ) -> Image.Image:
        """
        배경 이미지에 제품 이미지를 비율 기반 위치에 삽입합니다.
        제품 이미지가 배경보다 클 경우 자동 리사이즈/크롭.

        Args:
            foreground_image (PIL.Image.Image): 배경을 추가할 전경 이미지 객체 (RGBA 모드).
            background_image (PIL.Image.Image): 배경으로 사용할 이미지 객체 (RGB 또는 RGBA 모드).
            original_filename (str): 전경 이미지의 원본 파일명 (출력 파일명 생성에 사용).
            background_filename (str): 배경 이미지의 베이스 파일명 (예: "texture.jpg").
                                        출력 파일명 생성에 사용됩니다.
            output_dir (str, optional): 결과 이미지를 저장할 디렉토리 경로.
                                        기본값은 'backend/data/output/'.
            position (tuple): (0.0~1.0, 0.0~1.0) (width, height) 기준으로 배치할 상대 좌표.
            max_scale (float): 제품 이미지의 최대 크기를 배경의 몇 %로 제한할지.

        Returns:
            PIL.Image.Image: 이미지 배경이 추가된 이미지 객체 (RGB 모드). 오류 발생시 None 반환.
        """
        logger.debug(f"🛠️ 이미지 배경 추가 시작. 배경 이미지: {background_filename}")
        try:
            if foreground_image is None:
                logger.error(f"❌ 이미지 배경 추가를 위한 전경 이미지 객체가 None입니다.")
                return None
            if foreground_image.mode != 'RGBA':
                logger.warning("⚠️ 전경 이미지가 RGBA 모드가 아닙니다. 투명도 정보가 손실될 수 있습니다.")
                foreground_image = foreground_image.convert('RGBA')
            
            if background_image is None:
                logger.error(f"❌ 이미지 배경 추가를 위한 배경 이미지 객체가 None입니다.")
                return None
            if background_image.mode != 'RGBA':
                logger.warning("⚠️ 배경 이미지가 RGBA 모드가 아닙니다. 투명도 정보가 손실될 수 있습니다.")
                background_image = background_image.convert('RGBA')

            fg_w, fg_h = foreground_image.size
            bg_w, bg_h = background_image.size

            scale_w = max_scale * bg_w / fg_w
            scale_h = max_scale * bg_h / fg_h
            scale_factor = min(scale_w, scale_h, 1.0)

            # 제품 이미지가 배경보다 큰 경우 리사이즈
            if scale_factor < 1.0:
                logger.warning(f"⚠️ 제품 이미지 크기가 배경보다 큽니다. 리사이즈를 진행합니다.")
                new_size = (int(fg_w * scale_factor), int(fg_h * scale_factor))
                foreground_image = foreground_image.resize(new_size, Image.LANCZOS)
                logger.debug(f"✅ 제품 이미지 리사이즈 완료. 새 크기: {foreground_image.size}")

            x_ratio, y_ratio = position
            x = int(bg_w * x_ratio - foreground_image.width / 2)
            y = int(bg_h * y_ratio - foreground_image.height / 2)

            # 최종 이미지 생성
            final_image = background_image.copy()
            final_image.paste(foreground_image, (x, y), foreground_image)

            os.makedirs(output_dir, exist_ok=True)

            name_without_ext, _ = os.path.splitext(original_filename)
            bg_name_without_ext, _ = os.path.splitext(background_filename)
            filename = f"{name_without_ext}_on_{bg_name_without_ext}.png"
            
            save_path = os.path.join(output_dir, filename)
            final_image.save(save_path)

            logger.info(f"✅ 이미지 배경 추가 완료. 결과 이미지가 {save_path}에 저장되었습니다.")
            return final_image

        except Exception as e:
            logger.error(f"❌ 이미지 배경 추가 중 오류 발생: {e}")
            return None


class Txt2ImgGenerator:
    def __init__(self, pipeline):
        logger.debug("🛠️ Txt2ImgGenerator 초기화 시작")
        self.pipeline = pipeline  # DiffusionPipeline
        logger.info("✅ Txt2ImgGenerator 초기화 완료")

    def generate_background(
            self, 
            prompt: str,
            negative_prompt: str = None,
            size=(1024, 1024),
            num_inference_steps: int = 50, # 샘플링 단계 수
            guidance_scale: float = 7.5, # 안내 척도 (CFG Scale)
        ) -> Image.Image:
        """
        주어진 프롬프트를 사용하여 배경 이미지를 생성합니다.

        Args:
            prompt (str): 이미지를 생성할 긍정 프롬프트.
            negative_prompt (str, optional): 이미지에 포함하고 싶지 않은 요소를 정의하는 부정 프롬프트.
                                            기본값은 None.
            size (tuple, optional): 생성할 이미지의 크기 (width, height). 기본값은 (1024, 1024).
            num_inference_steps (int, optional): 이미지 생성에 사용할 샘플링 단계 수.
                                                값이 높을수록 품질은 좋아지지만 시간이 오래 걸릴 수 있습니다.
                                                기본값은 50.
            guidance_scale (float, optional): Classifier-Free Guidance (CFG) 척도.
                                            프롬프트에 얼마나 충실하게 이미지를 생성할지 조절합니다.
                                            값이 높을수록 프롬프트에 더 충실하지만, 다양성이 줄어들 수 있습니다.
                                            기본값은 7.5.

        Returns:
            PIL.Image.Image: 생성된 이미지 객체. 오류 발생 시 None 반환.
        """
        try:
            logger.debug(f"🛠️ 프롬프트로 배경 생성: {prompt}")
            image = self.pipeline(
                prompt=prompt,
                negative_prompt=negative_prompt,
                height=size[1], 
                width=size[0],
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                num_images_per_prompt=1
            ).images[0]
            logger.info(f"✅ 배경 이미지 생성 완료")
            save_path = "backend/data/output/txt2img.png"
            image.save(save_path)
            logger.info(f"✅ 배경 이미지가 {save_path}에 생성되었습니다.")
            return image, save_path
        except Exception as e:
            logger.error(f"❌ 텍스트-이미지 생성 중 오류 발생: {e}")
            return None


class Img2ImgGenerator:
    def __init__(self, pipeline):
        logger.debug("🛠️ Img2ImgGenerator 초기화 시작")
        self.pipeline = pipeline  # DiffusionPipeline
        logger.info("✅ Img2ImgGenerator 초기화 완료")

    def generate_img(
            self, 
            prompt: str,
            reference_image: Image.Image,
            negative_prompt: str = None,
            size=(1024, 1024),
            num_inference_steps: int = 100, # 샘플링 단계 수
            guidance_scale: float = 5.0, # 안내 척도 (CFG Scale)
        ) -> tuple[Image.Image, str]:
        """
        주어진 이미지와 마스크 이미지, 프롬프트를 이용하여 이미지를 생성합니다.

        Args:
            prompt (str): 이미지를 생성할 긍정 프롬프트.
            reference_image (PIL.Image.Image): 기반이 되는 이미지
            mask_image (PIL.Image.Image): 재생성할 곳을 표시하는 마스크 이미지
            negative_prompt (str, optional): 이미지에 포함하고 싶지 않은 요소를 정의하는 부정 프롬프트.
                                            기본값은 None.
            size (tuple, optional): 생성할 이미지의 크기 (width, height). 기본값은 (1024, 1024).
            num_inference_steps (int, optional): 이미지 생성에 사용할 샘플링 단계 수.
                                                값이 높을수록 품질은 좋아지지만 시간이 오래 걸릴 수 있습니다.
                                                기본값은 4.
            guidance_scale (float, optional): Classifier-Free Guidance (CFG) 척도.
                                            프롬프트에 얼마나 충실하게 이미지를 생성할지 조절합니다.
                                            값이 높을수록 프롬프트에 더 충실하지만, 다양성이 줄어들 수 있습니다.
                                            기본값은 0.5.

        Returns:
            PIL.Image.Image: 생성된 이미지 객체. 오류 발생 시 None 반환.
            str: 생성된 이미지 저장 경로. 오류 발생 시 None 반환
        """
        # RGBA → RGB
        if reference_image.mode != 'RGB':
            logger.warning("⚠️ reference_image를 RGB로 변환")
            reference_image = reference_image.convert("RGB")

        try:
            logger.debug(f"🛠️ IPAdapter 이미지 생성 시작: {prompt}")
            image = self.pipeline(
                prompt=prompt,
                ip_adapter_image=reference_image,
                negative_prompt=negative_prompt,
                height=size[1], 
                width=size[0],
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                num_images_per_prompt=1
            ).images[0]
            logger.info(f"✅ 이미지 생성 완료")
            
            save_path = "backend/data/output/img2img.png"
            image.save(save_path)
            logger.info(f"✅ 이미지가 {save_path}에 생성되었습니다.")
            return image, save_path
        except Exception as e:
            logger.error(f"❌ 텍스트-이미지 생성 중 오류 발생: {e}")
            return None