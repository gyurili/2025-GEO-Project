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
            
            output_image = remove(input_image, alpha_matting=True, bgcolor=(0, 0, 0, 0))
            
            os.makedirs(output_dir, exist_ok=True)

            # 파일명과 확장자 분리 (예: 'cake', '.jpg')
            name_without_ext, _ = os.path.splitext(original_filename)
            # 새 확장자를 붙여 최종 파일명 생성 (예: 'cake_removed_bg.png')
            filename = f"{name_without_ext}_removed_bg.png"

            save_path = os.path.join(output_dir, filename)
            output_image.save(save_path)

            logger.info(f"✅ 배경 제거 완료. 결과 이미지가 {output_dir}에 저장되었습니다.")
            return output_image
        except Exception as e:
            logger.error(f"❌ 배경 제거 중 오류 발생: {e}")
            return None

    def add_color_background(
            self, 
            foreground_image: Image.Image, 
            color: tuple, 
            original_filename: str, 
            output_dir: str = "backend/data/output"
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

    def add_image_background(
            self, 
            foreground_image: Image.Image, 
            background_image: Image.Image, # 배경 이미지 객체를 직접 받음
            original_filename: str, # 전경 이미지의 원본 파일명
            background_filename: str, # 배경 이미지의 베이스 파일명 (예: "texture.jpg")
            output_dir: str = "backend/data/output"
        ) -> Image.Image:
        """
        투명 배경을 가진 이미지에 다른 이미지 객체를 배경으로 추가합니다.

        Args:
            foreground_image (PIL.Image.Image): 배경을 추가할 전경 이미지 객체 (RGBA 모드).
            background_image (PIL.Image.Image): 배경으로 사용할 이미지 객체 (RGB 또는 RGBA 모드).
            original_filename (str): 전경 이미지의 원본 파일명 (출력 파일명 생성에 사용).
            background_filename (str): 배경 이미지의 베이스 파일명 (예: "texture.jpg").
                                        출력 파일명 생성에 사용됩니다.
            output_dir (str, optional): 결과 이미지를 저장할 디렉토리 경로.
                                        기본값은 'backend/data/output/'.

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

            # 배경 이미지를 전경 이미지 크기에 맞게 리사이즈
            background_image = background_image.resize(foreground_image.size, Image.LANCZOS).convert('RGB')

            # 최종 이미지 생성
            final_image = Image.new('RGB', foreground_image.size)
            final_image.paste(background_image, (0, 0))
            final_image.paste(foreground_image, (0, 0), foreground_image)

            os.makedirs(output_dir, exist_ok=True)

            name_without_ext, _ = os.path.splitext(original_filename)
            bg_name_without_ext, _ = os.path.splitext(background_filename)
            filename = f"{name_without_ext}_bg_with_{bg_name_without_ext}.png"
            
            save_path = os.path.join(output_dir, filename)
            final_image.save(save_path)

            logger.info(f"✅ 이미지 배경 추가 완료. 결과 이미지가 {save_path}에 저장되었습니다.")
            return final_image
        except Exception as e:
            logger.error(f"❌ 이미지 배경 추가 중 오류 발생: {e}")
            return None