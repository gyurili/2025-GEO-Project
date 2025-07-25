import os
import sys
from PIL import Image
import requests
from io import BytesIO
from utils.logger import get_logger

logger = get_logger(__name__)

class ImageLoader:
    """
    이미지 파일을 로컬 경로 또는 URL에서 로드하고, 필요시 리사이즈하는 기능을 제공하는 클래스
    """
    def __init__(self):
        """
        ImageLoader 클래스의 생성자
        클래스 인스턴스가 생성될 때 초기화작업 수행
        """
        logger.debug("🛠️ ImageLoader 초기화 시작")
        logger.info("✅ ImageLoader 초기화 완료")
    
    def load_image(
        self, 
        image_path: str, 
        target_size: tuple = None
    ) -> tuple[Image.Image, str]:
        """
        주어진 경로(로컬 파일 또는 URL)의 이미지를 로드하고
        RGB 포맷으로 변환하고, 필요시 지정된 크기로 리사이즈
        
        Args:
            image_path (str): 로드할 이미지 파일의 경로 또는 URL
            target_size (tuple, opitional): 이미지를 리사이즈할 튜플(width, height), None이면 원본 사이즈. 기본값은 None
        
        Returns:
            PIL.Image.Image: 로드되고 처리된 이미지 객체.
                             오류 발생시 None을 반환.
            str: 파일명
        """
        image = None
        filename = None

        # 1. 이미지 로드
        try:
            if image_path.startswith(("http://", "https://")):
                logger.debug(f"🛠️ URL 이미지 로드 시도: {image_path}")
                response = requests.get(image_path)
                response.raise_for_status()
                image = Image.open(BytesIO(response.content)).convert("RGB")
                filename = os.path.basename(image_path)
                logger.info(f"✅ URL 이미지 로드 완료")
            else:
                logger.debug(f"🛠️ 로컬 이미지 로드 시도: {image_path}")
                image = Image.open(image_path).convert("RGB")
                filename = os.path.basename(image_path)
                logger.info(f"✅ 로컬 이미지 로드 완료: {image_path}")
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 네트워크 오류: URL '{image_path}'에서 이미지 로드 실패 - {e}")
            return None, None
        except FileNotFoundError:
            logger.error(f"❌ 파일을 찾을 수 없음: '{image_path}'")
            return None, None
        except Exception as e:
            logger.error(f"❌ 이미지 로드 중 일반 오류: {e}")
            return None, None
        

        # 2. 리사이즈 (필요한 경우)
        if target_size:
            try:
                if not (isinstance(target_size, tuple) and len(target_size) == 2):
                    raise ValueError("target_size는 (width, height) 형태의 튜플이어야 합니다.")
                if not all(isinstance(dim, int) and dim > 0 for dim in target_size):
                    raise ValueError("target_size의 각 값은 양의 정수여야 합니다.")
                image = image.resize(target_size, Image.LANCZOS)
                logger.debug(f"✅ 이미지 리사이즈 완료: {image.size}")
            except ValueError as ve:
                logger.error(f"❌ 잘못된 리사이즈 인자: {ve}")
                return None, None
            except Exception as e:
                logger.error(f"❌ 이미지 리사이즈 실패: {e}")
                return None, None

        return image, filename