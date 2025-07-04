import os
import shutil
from PIL import Image
from typing import Optional, Tuple, List
import uuid
import logging

logger = logging.getLogger(__name__)


class ImagePreprocessor:
    """이미지 전처리 클래스"""
    
    def __init__(self, 
                 max_size: Tuple[int, int] = (1024, 1024),
                 max_file_size: int = 5 * 1024 * 1024,  # 5MB
                 allowed_formats: list = None):
        self.max_size = max_size
        self.max_file_size = max_file_size
        self.allowed_formats = allowed_formats or ['JPEG', 'PNG', 'JPG', 'WEBP']
        
    def validate_image(self, image_path: str) -> bool:
        """이미지 유효성 검증"""
        try:
            if not os.path.exists(image_path):
                logger.error(f"이미지 파일이 존재하지 않습니다: {image_path}")
                return False
            
            # 파일 크기 검증
            file_size = os.path.getsize(image_path)
            if file_size > self.max_file_size:
                logger.error(f"이미지 파일 크기가 너무 큽니다: {file_size} bytes")
                return False
            
            # 이미지 포맷 검증
            with Image.open(image_path) as img:
                if img.format not in self.allowed_formats:
                    logger.error(f"지원하지 않는 이미지 포맷: {img.format}")
                    return False
                
                # 이미지 크기 검증
                if img.size[0] > self.max_size[0] * 2 or img.size[1] > self.max_size[1] * 2:
                    logger.warning(f"이미지 크기가 매우 큽니다: {img.size}")
                    
            return True
            
        except Exception as e:
            logger.error(f"이미지 검증 중 오류 발생: {str(e)}")
            return False
    
    def resize_image(self, image_path: str, output_path: str) -> bool:
        """이미지 리사이징"""
        try:
            with Image.open(image_path) as img:
                # RGB 모드로 변환 (투명도 제거)
                if img.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 비율 유지하면서 리사이징
                img.thumbnail(self.max_size, Image.Resampling.LANCZOS)
                
                # 품질 최적화하여 저장
                img.save(output_path, 'JPEG', quality=85, optimize=True)
                
                logger.info(f"이미지 리사이징 완료: {output_path}")
                return True
                
        except Exception as e:
            logger.error(f"이미지 리사이징 중 오류 발생: {str(e)}")
            return False
    
    def process_image(self, uploaded_file, output_dir: str) -> Optional[str]:
        """업로드된 이미지 전처리"""
        try:
            # 출력 디렉토리 생성
            os.makedirs(output_dir, exist_ok=True)
            
            # 임시 파일 저장
            temp_filename = f"temp_{uuid.uuid4().hex}.jpg"
            temp_path = os.path.join(output_dir, temp_filename)
            
            # Streamlit 업로드 파일 저장
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # 이미지 유효성 검증
            if not self.validate_image(temp_path):
                os.remove(temp_path)
                return None
            
            # 최종 파일명 생성
            final_filename = f"product_{uuid.uuid4().hex}.jpg"
            final_path = os.path.join(output_dir, final_filename)
            
            # 이미지 리사이징 및 최적화
            if self.resize_image(temp_path, final_path):
                # 임시 파일 삭제
                os.remove(temp_path)
                return final_path
            else:
                # 실패시 임시 파일 삭제
                os.remove(temp_path)
                return None
                
        except Exception as e:
            logger.error(f"이미지 처리 중 오류 발생: {str(e)}")
            return None
    
    def copy_existing_image(self, source_path: str, output_dir: str) -> Optional[str]:
        """기존 이미지 복사 및 전처리"""
        try:
            if not self.validate_image(source_path):
                return None
            
            # 출력 디렉토리 생성
            os.makedirs(output_dir, exist_ok=True)
            
            # 최종 파일명 생성
            final_filename = f"product_{uuid.uuid4().hex}.jpg"
            final_path = os.path.join(output_dir, final_filename)
            
            # 이미지 리사이징 및 최적화
            if self.resize_image(source_path, final_path):
                return final_path
            else:
                return None
                
        except Exception as e:
            logger.error(f"이미지 복사 중 오류 발생: {str(e)}")
            return None
    
    def process_multiple_images(self, uploaded_files, output_dir: str) -> List[str]:
        """여러 업로드된 이미지 전처리"""
        try:
            # 출력 디렉토리 생성
            os.makedirs(output_dir, exist_ok=True)
            
            processed_paths = []
            
            for i, uploaded_file in enumerate(uploaded_files):
                # 임시 파일 저장
                temp_filename = f"temp_{uuid.uuid4().hex}_{i}.jpg"
                temp_path = os.path.join(output_dir, temp_filename)
                
                # Streamlit 업로드 파일 저장
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # 이미지 유효성 검증
                if not self.validate_image(temp_path):
                    os.remove(temp_path)
                    logger.warning(f"이미지 {i+1} 처리 실패: 유효성 검증 실패")
                    continue
                
                # 최종 파일명 생성
                final_filename = f"product_{uuid.uuid4().hex}_{i}.jpg"
                final_path = os.path.join(output_dir, final_filename)
                
                # 이미지 리사이징 및 최적화
                if self.resize_image(temp_path, final_path):
                    # 상대 경로로 변환
                    relative_path = os.path.relpath(final_path, 
                        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(temp_path))))))
                    processed_paths.append(relative_path)
                    logger.info(f"이미지 {i+1} 처리 완료: {relative_path}")
                
                # 임시 파일 삭제
                os.remove(temp_path)
            
            return processed_paths
            
        except Exception as e:
            logger.error(f"다중 이미지 처리 중 오류 발생: {str(e)}")
            return []