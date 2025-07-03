import os # 운영체제와 상호작용하는 기능을 제공 (파일 경로 확인 등)
from PIL import Image # Pillow 라이브러리의 Image 모듈 임포트 (이미지 파일을 열고, 조작하고, 저장하는 데 사용)
import numpy as np # NumPy 라이브러리 임포트 (수치 계산, 특히 이미지 데이터를 효율적인 배열로 다룰 때 필수적)
from rembg import remove # rembg 라이브러리에서 배경 제거 기능을 담당하는 remove 함수 임포트
import cv2 # OpenCV 라이브러리 임포트 (컴퓨터 비전 관련 기능 제공, 여기서는 사용되지 않지만 일반적으로 이미지 처리 시 활용)
import requests # HTTP 요청을 보내는 라이브러리 (URL에서 이미지를 다운로드할 때 사용)
from io import BytesIO # 인메모리 바이너리 스트림을 다루는 모듈 (다운로드한 이미지 데이터를 파일처럼 처리할 때 사용)

# 로거 초기화: 애플리케이션의 동작 상태나 오류를 기록하기 위한 로거를 설정합니다.
# `utils.logger` 모듈은 로깅 시스템을 설정하는 사용자 정의 모듈이라고 가정합니다.
from utils.logger import get_logger
logger = get_logger(__name__) # 현재 모듈의 이름을 로거 이름으로 사용합니다.

class ProductBackgroundProcessor:
    """
    제품 이미지의 배경을 제거하고 새로운 배경으로 교체하는 기능을 제공하는 클래스입니다.
    이 클래스는 주로 전자상거래나 광고 분야에서 제품 이미지를 더욱 전문적으로 보이게 하는 데 활용될 수 있습니다.
    """
    def __init__(self):
        """
        ProductBackgroundProcessor 클래스의 생성자입니다.
        클래스 인스턴스가 생성될 때 초기화 작업을 수행합니다.
        현재는 특별한 멤버 변수 초기화 없이 로깅 메시지만 출력합니다.
        """
        logger.debug("🛠️ 제품 배경 처리기 초기화 시작") # 초기화 시작 로그
        logger.info("✅ 초기화 완료") # 초기화 완료 로그

    def _load_image(self, image_path: str, target_size: tuple = None) -> Image.Image:
        """
        주어진 경로(로컬 파일 경로 또는 URL)의 이미지를 로드하고,
        RGB 포맷으로 변환한 후, 필요시 지정된 크기로 리사이즈합니다.

        Args:
            image_path (str): 로드할 이미지 파일의 경로 또는 URL.
            target_size (tuple, optional): 이미지를 리사이즈할 (너비, 높이) 튜플.
                                           None이면 원본 크기를 유지합니다. 기본값은 None.

        Returns:
            PIL.Image.Image: 로드되고 처리된 이미지 객체.
                             오류 발생 시 None을 반환합니다.
        """
        try:
            # 이미지 경로가 'http://' 또는 'https://'로 시작하는지 확인하여 URL인지 판단합니다.
            if image_path.startswith(('http://', 'https://')):
                logger.debug(f"🛠️ URL 이미지 로드 시도: {image_path}")
                # requests 라이브러리를 사용하여 URL에서 이미지 데이터를 다운로드합니다.
                response = requests.get(image_path)
                # HTTP 요청 중 오류(예: 404 Not Found, 500 Internal Server Error) 발생 시 예외를 발생시킵니다.
                response.raise_for_status() 
                # 다운로드된 바이너리 데이터를 BytesIO 객체로 감싸서 PIL.Image.open이 파일처럼 읽을 수 있도록 합니다.
                image = Image.open(BytesIO(response.content)).convert("RGB")
                logger.info(f"✅ URL 이미지 로드 완료: {image_path}")
            else:
                logger.debug(f"🛠️ 로컬 이미지 로드 시도: {image_path}")
                # 로컬 파일 경로에서 이미지를 로드합니다.
                image = Image.open(image_path).convert("RGB")
                logger.info(f"✅ 로컬 이미지 로드 완료: {image_path}")

            # target_size가 지정된 경우 이미지를 해당 크기로 리사이즈합니다.
            if target_size:
                # Image.LANCZOS는 고품질 리사이징 필터로, 이미지 축소 시 계단 현상을 줄여줍니다.
                image = image.resize(target_size, Image.LANCZOS) 
                logger.debug(f"✅ 이미지 리사이즈 완료. 크기: {image.size}")
            return image
        except FileNotFoundError:
            # 지정된 로컬 파일 경로에 이미지가 없을 경우 발생하는 오류를 처리합니다.
            logger.error(f"❌ 오류: 이미지 파일 '{image_path}'을(를) 찾을 수 없습니다.")
            return None
        except requests.exceptions.RequestException as e:
            # URL에서 이미지를 로드하는 중 네트워크 관련 오류(예: 연결 실패, 타임아웃) 발생 시 처리합니다.
            logger.error(f"❌ 오류: URL '{image_path}'에서 이미지 로드 중 네트워크 문제 발생: {e}")
            return None
        except Exception as e:
            # 이미지 로드 또는 처리 중 발생하는 기타 모든 예외를 처리합니다.
            logger.error(f"❌ 오류: 이미지 로드/처리 중 문제 발생: {e}")
            return None

    def remove_product_background(self, input_image_path: str, output_image_path: str = "product_no_bg.png") -> Image.Image:
        """
        `rembg` 라이브러리를 사용하여 입력 이미지에서 배경을 제거하고,
        투명 배경을 가진 PNG 이미지로 저장합니다.

        Args:
            input_image_path (str): 배경을 제거할 제품 이미지 파일의 경로 또는 URL.
            output_image_path (str, optional): 배경이 제거된 이미지를 저장할 경로.
                                               기본값은 "product_no_bg.png"입니다.

        Returns:
            PIL.Image.Image: 배경이 제거된 이미지 객체 (RGBA 모드).
                             오류 발생 시 None을 반환합니다.
        """
        logger.debug(f"🛠️ 배경 제거 시작: {input_image_path}") # 배경 제거 시작 로그
        try:
            # `_load_image` 메서드를 사용하여 입력 이미지를 로드합니다.
            # 이 메서드는 로컬 파일과 URL 모두 처리할 수 있습니다.
            input_image = self._load_image(input_image_path)
            if input_image is None:
                # 이미지 로드에 실패하면 None을 반환하고 함수를 종료합니다.
                logger.error(f"❌ 배경 제거를 위한 이미지 로드 실패: {input_image_path}")
                return None
            
            # rembg의 `remove` 함수를 사용하여 이미지에서 배경을 제거합니다.
            # `alpha_matting=True`: 배경과 객체 경계면을 더 부드럽게 처리하여 자연스러운 결과를 만듭니다.
            # `bgcolor=(0, 0, 0, 0)`: 제거된 배경 영역을 완전 투명(RGBA의 마지막 0은 알파 채널)으로 채웁니다.
            output_image = remove(input_image, alpha_matting=True, bgcolor=(0, 0, 0, 0))
            
            # 결과 이미지를 지정된 경로에 PNG 형식으로 저장합니다.
            # PNG 형식은 투명도(알파 채널)를 지원하므로 배경이 투명하게 유지됩니다.
            output_image.save(output_image_path)
            logger.info(f"✅ 배경 제거 완료. 결과 이미지가 {output_image_path}에 저장되었습니다.") # 성공 로그
            return output_image
        except Exception as e:
            # 배경 제거 과정에서 발생하는 모든 예외를 처리합니다.
            logger.error(f"❌ 배경 제거 중 오류 발생: {e}")
            return None

    def replace_background_with_color(self, product_no_bg_image: Image.Image, color: tuple = (255, 255, 255), output_image_path: str = "product_color_bg.jpg") -> Image.Image:
        """
        투명 배경을 가진 제품 이미지의 배경을 지정된 단색으로 교체합니다.
        주로 제품을 깔끔한 단색 배경에 배치할 때 사용됩니다.

        Args:
            product_no_bg_image (PIL.Image.Image): 배경이 제거된 투명 제품 이미지 (RGBA 모드).
            color (tuple, optional): 배경으로 사용할 RGB 색상 튜플 (예: (255, 255, 255)는 흰색).
                                     기본값은 흰색입니다.
            output_image_path (str, optional): 결과 이미지를 저장할 경로.
                                               기본값은 "product_color_bg.jpg"입니다.

        Returns:
            PIL.Image.Image: 단색 배경이 적용된 이미지 객체 (RGB 모드).
                             오류 발생 시 None을 반환합니다.
        """
        logger.debug(f"🛠️ 단색 배경 교체 시작") # 단색 배경 교체 시작 로그
        try:
            # 제품 이미지의 너비와 높이를 가져옵니다.
            width, height = product_no_bg_image.size
            
            # 지정된 `color`로 새로운 배경 이미지를 생성합니다.
            # `Image.new("RGB", ...)`는 단색의 RGB 이미지를 만듭니다.
            background = Image.new("RGB", (width, height), color)
            
            # 제품 이미지를 배경 위에 합성
            # product_no_bg_image는 RGBA (투명도 채널 포함) 모드여야 합니다.
            if product_no_bg_image.mode != 'RGBA':
                product_no_bg_image = product_no_bg_image.convert('RGBA')

            # `Image.alpha_composite`를 사용하여 배경 이미지 위에 제품 이미지를 합성합니다.
            # 이 함수는 알파 채널(투명도)을 사용하여 두 이미지를 자연스럽게 겹칩니다.
            # 배경 이미지도 RGBA로 변환하여 투명도 정보와 함께 합성될 수 있도록 합니다.
            combined_image = Image.alpha_composite(background.convert('RGBA'), product_no_bg_image)
            
            # 최종 합성된 이미지를 JPG로 저장하기 위해 RGB 모드로 다시 변환합니다.
            # JPG 형식은 투명도를 지원하지 않으므로, 투명도 정보는 이 단계에서 손실됩니다.
            combined_image.convert("RGB").save(output_image_path)
            logger.info(f"✅ 단색 배경 교체 완료. 결과 이미지가 {output_image_path}에 저장되었습니다.") # 성공 로그
            return combined_image.convert("RGB") # RGB 모드 이미지 객체 반환
        except Exception as e:
            # 단색 배경 교체 과정에서 발생하는 모든 예외를 처리합니다.
            logger.error(f"❌ 단색 배경 교체 중 오류 발생: {e}")
            return None

    def replace_background_with_image(self, product_no_bg_image: Image.Image, background_image_path: str, output_image_path: str = "product_custom_bg.jpg") -> Image.Image:
        """
        투명 배경을 가진 제품 이미지의 배경을 다른 이미지 파일로 교체합니다.
        제공된 배경 이미지는 제품 이미지의 크기에 맞춰 자동으로 리사이즈됩니다.

        Args:
            product_no_bg_image (PIL.Image.Image): 배경이 제거된 투명 제품 이미지 (RGBA 모드).
            background_image_path (str): 배경으로 사용할 이미지 파일의 경로 또는 URL.
            output_image_path (str, optional): 결과 이미지를 저장할 경로.
                                               기본값은 "product_custom_bg.jpg"입니다.

        Returns:
            PIL.Image.Image: 커스텀 배경이 적용된 이미지 객체 (RGB 모드).
                             오류 발생 시 None을 반환합니다.
        """
        logger.debug(f"🛠️ 커스텀 이미지 배경 교체 시작") # 커스텀 배경 교체 시작 로그
        try:
            # 제품 이미지의 너비와 높이를 가져옵니다.
            product_width, product_height = product_no_bg_image.size
            
            # `_load_image` 메서드를 사용하여 커스텀 배경 이미지를 로드하고,
            # 제품 이미지와 동일한 크기로 리사이즈합니다.
            background_image = self._load_image(background_image_path, target_size=(product_width, product_height))
            if background_image is None:
                # 배경 이미지 로드에 실패하면 None을 반환하고 함수를 종료합니다.
                logger.error(f"❌ 커스텀 배경 교체를 위한 배경 이미지 로드 실패: {background_image_path}")
                return None
            
            # 제품 이미지가 RGBA 모드인지 확인하고, 아니면 변환합니다.
            if product_no_bg_image.mode != 'RGBA':
                product_no_bg_image = product_no_bg_image.convert('RGBA')
            
            # `Image.alpha_composite`를 사용하여 리사이즈된 배경 이미지 위에 제품 이미지를 합성합니다.
            # 배경 이미지도 RGBA로 변환하여 투명도 정보와 함께 합성될 수 있도록 합니다.
            combined_image = Image.alpha_composite(background_image.convert('RGBA'), product_no_bg_image)
            
            # 최종 합성된 이미지를 JPG로 저장하기 위해 RGB 모드로 다시 변환합니다.
            combined_image.convert("RGB").save(output_image_path)
            logger.info(f"✅ 커스텀 이미지 배경 교체 완료. 결과 이미지가 {output_image_path}에 저장되었습니다.") # 성공 로그
            return combined_image.convert("RGB") # RGB 모드 이미지 객체 반환
        except Exception as e:
            # 커스텀 이미지 배경 교체 과정에서 발생하는 모든 예외를 처리합니다.
            logger.error(f"❌ 커스텀 이미지 배경 교체 중 오류 발생: {e}")
            return None


# 이 아래의 코드는 스크립트가 직접 실행될 때만 동작하는 부분입니다.
# 다른 모듈에서 이 클래스를 임포트하여 사용할 때는 이 부분이 실행되지 않습니다.
if __name__ == "__main__":
    # ProductBackgroundProcessor 클래스의 인스턴스를 생성합니다.
    processor = ProductBackgroundProcessor()
    
    # --- 입력 및 출력 파일 경로 설정 ---
    # 사용자의 test_image.jpg 파일을 제품 이미지로 사용합니다.
    # 이 경로는 실제 파일이 위치한 경로로 정확하게 지정해야 합니다.
    product_image_path = "/home/user/2025-GEO-Project/backend/data/input/test_image.jpg"
    
    # 커스텀 배경으로 사용할 이미지의 경로를 지정합니다.
    # 이전 대화에서 언급된 로컬 파일 경로를 사용합니다.
    # 이 경로에 'music-player-2951399_1280.jpg' 파일이 실제로 존재해야 합니다.
    custom_background_path = "/home/user/2025-GEO-Project/backend/data/input/music-player-2951399_1280.jpg"

    # 각 결과 이미지가 저장될 파일 이름을 정의합니다.
    output_no_bg = "product_with_transparent_bg.png" # 투명 배경 이미지
    output_white_bg = "product_with_white_bg.jpg" # 흰색 배경 이미지
    output_custom_bg = "product_with_custom_bg.jpg" # 커스텀 이미지 배경

    # --- 1. 배경 제거 실험 실행 ---
    # `remove_product_background` 메서드를 호출하여 제품 이미지에서 배경을 제거합니다.
    # 이 메서드는 배경이 제거된 PIL.Image.Image 객체를 반환합니다.
    product_image_no_bg = processor.remove_product_background(product_image_path, output_no_bg)
    
    # 배경 제거가 성공적으로 이루어졌는지 확인합니다.
    if product_image_no_bg:
        # --- 2. 단색(흰색) 배경으로 교체 실험 실행 ---
        # 배경이 제거된 제품 이미지에 흰색 배경을 적용합니다.
        # `color`와 `output_image_path`는 키워드 인자로 명시적으로 전달합니다.
        processor.replace_background_with_color(product_image_no_bg, color=(255, 255, 255), output_image_path=output_white_bg)
        
        # --- 3. 커스텀 이미지 배경으로 교체 실험 실행 ---
        # 배경이 제거된 제품 이미지에 지정된 커스텀 배경 이미지를 적용합니다.
        # `_load_image` 함수가 이제 URL과 로컬 파일 모두 처리하므로, `os.path.exists()` 체크는 필요 없습니다.
        # `output_image_path`는 키워드 인자로 명시적으로 전달합니다.
        processor.replace_background_with_image(product_image_no_bg, custom_background_path, output_image_path=output_custom_bg)
        
    logger.info("✅ 모든 배경 처리 실험 완료.") # 모든 실험 완료 로그
