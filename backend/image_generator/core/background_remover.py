import os
from PIL import Image
from rembg import remove

from utils.logger import get_logger
from .image_loader import ImageLoader

logger = get_logger(__name__)
"""
TODO: rembg의 파라미터 확인 후에 배경제거가 잘 되는 것으로 수정 필요
"""

class BackgroundRemover:
    """
    제품 이미지에서 배경을 제거하는 기능을 제공하는 클래스
    'rembg' 라이브러리를 활용하여 이미지의 배경을 투명하게 바꿈
    """
    def __init__(self):
        """
        BackgroundRemover 클래스의 생성자
        """
        logger.debug("🛠️ BackgroundRemover 초기화 시작")
        logger.info("✅ BackgroundRemover 초기화 완료")

    def remove_background(
        self, 
        input_image: Image.Image, 
        original_input_path: str = "backend/data/input/", 
        output_dir: str = "backend/data/output/"
    ) -> Image.Image:
        """
        'rembg' 라이브러리를 사용하여 입력 이미지(PIL.Image.Image)에서 배경을 제거,
        투명 배경을 가진 PNG 이미지로 저장

        Args:
            input_image (PIL.Image.Image): 배경을 제거할 제품 이미지 객체 (RGB 또는 RGBA 모드)
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
            if input_image.mode != 'RGB' and input_image != 'RGBA':
                input_image = input_image.convert('RGB')
                logger.debug("🛠️ 입력 이미지를 RGB 모드로 변환했습니다.")
            
            output_image = remove(input_image, alpha_matting=True, bgcolor=(0, 0, 0, 0))
            
            os.makedirs(output_dir, exist_ok=True)

            base_filename = os.path.basename(original_input_path)
            name_without_ext, _ = os.path.splitext(base_filename)
            filename = f"{name_without_ext}.png"

            save_path = os.path.join(output_dir, filename)
            output_image.save(save_path)

            logger.info(f"✅ 배경 제거 완료. 결과 이미지가 {output_dir}에 저장되었습니다.")
            return output_image
        except Exception as e:
            logger.error(f"❌ 배경 제거 중 오류 발생: {e}")
            return None