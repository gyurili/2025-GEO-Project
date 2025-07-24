import os
import shutil
from PIL import Image
from typing import Optional, Tuple, List, Union
import uuid
import io
import sys
from pathlib import Path

# 로거 임포트 추가
sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.logger import get_logger

# 로거 설정
logger = get_logger(__name__)

class ImagePreprocessor:
    """이미지 전처리 클래스"""
    
    def __init__(self, 
                 max_size: Tuple[int, int] = (1024, 1024),
                 max_file_size: int = 5 * 1024 * 1024,  # 5MB
                 allowed_formats: list = None):
        logger.debug("🛠️ ImagePreprocessor 인스턴스 초기화 시작")
        
        self.max_size = max_size
        self.max_file_size = max_file_size
        self.allowed_formats = allowed_formats or ['JPEG', 'PNG', 'JPG', 'WEBP']
        
        logger.debug(f"🛠️ 이미지 처리 설정: 최대크기={max_size}, 최대파일크기={max_file_size//1024//1024}MB")
        logger.debug(f"🛠️ 허용 포맷: {self.allowed_formats}")
        logger.info("✅ ImagePreprocessor 인스턴스 초기화 완료")
        
    def validate_image(self, image_path: str) -> bool:
        """이미지 유효성 검증"""
        logger.debug(f"🛠️ 이미지 유효성 검증 시작: {image_path}")
        
        try:
            # 파일 존재 확인
            if not os.path.exists(image_path):
                logger.error(f"❌ 이미지 파일이 존재하지 않습니다: {image_path}")
                return False
            
            # 파일 크기 검증
            file_size = os.path.getsize(image_path)
            logger.debug(f"🛠️ 파일 크기 확인: {file_size:,} bytes ({file_size//1024//1024:.1f}MB)")
            
            if file_size > self.max_file_size:
                logger.error(f"❌ 이미지 파일 크기가 너무 큽니다: {file_size:,} bytes (허용: {self.max_file_size//1024//1024}MB)")
                return False
            
            # 이미지 포맷 및 크기 검증
            logger.debug("🛠️ 이미지 포맷 및 크기 검증 시작")
            with Image.open(image_path) as img:
                logger.debug(f"🛠️ 이미지 정보: 포맷={img.format}, 크기={img.size}, 모드={img.mode}")
                
                if img.format not in self.allowed_formats:
                    logger.error(f"❌ 지원하지 않는 이미지 포맷: {img.format} (허용: {self.allowed_formats})")
                    return False
                
                # 이미지 크기 검증
                if img.size[0] > self.max_size[0] * 2 or img.size[1] > self.max_size[1] * 2:
                    logger.warning(f"⚠️ 이미지 크기가 매우 큽니다: {img.size} (권장 최대: {self.max_size[0]*2}x{self.max_size[1]*2})")
                    
            logger.info(f"✅ 이미지 유효성 검증 완료: {os.path.basename(image_path)}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 이미지 검증 중 오류 발생: {e}")
            return False
    
    def validate_image_from_bytes(self, image_bytes: bytes) -> bool:
        """바이트 데이터로부터 이미지 유효성 검증"""
        logger.debug(f"🛠️ 바이트 데이터 이미지 유효성 검증 시작: {len(image_bytes)} bytes")
        
        try:
            # 파일 크기 검증
            if len(image_bytes) > self.max_file_size:
                logger.error(f"❌ 이미지 파일 크기가 너무 큽니다: {len(image_bytes):,} bytes (허용: {self.max_file_size//1024//1024}MB)")
                return False
            
            # 이미지 포맷 및 크기 검증
            logger.debug("🛠️ 바이트 데이터 이미지 포맷 및 크기 검증 시작")
            with Image.open(io.BytesIO(image_bytes)) as img:
                logger.debug(f"🛠️ 이미지 정보: 포맷={img.format}, 크기={img.size}, 모드={img.mode}")
                
                if img.format not in self.allowed_formats:
                    logger.error(f"❌ 지원하지 않는 이미지 포맷: {img.format} (허용: {self.allowed_formats})")
                    return False
                
                # 이미지 크기 검증
                if img.size[0] > self.max_size[0] * 2 or img.size[1] > self.max_size[1] * 2:
                    logger.warning(f"⚠️ 이미지 크기가 매우 큽니다: {img.size} (권장 최대: {self.max_size[0]*2}x{self.max_size[1]*2})")
                    
            logger.info(f"✅ 바이트 데이터 이미지 유효성 검증 완료")
            return True
            
        except Exception as e:
            logger.error(f"❌ 바이트 데이터 이미지 검증 중 오류 발생: {e}")
            return False
    
    def resize_image(self, image_path: str, output_path: str) -> bool:
        """이미지 리사이징"""
        logger.debug(f"🛠️ 이미지 리사이징 시작: {os.path.basename(image_path)} -> {os.path.basename(output_path)}")
        
        try:
            with Image.open(image_path) as img:
                original_size = img.size
                original_mode = img.mode
                logger.debug(f"🛠️ 원본 이미지: 크기={original_size}, 모드={original_mode}")
                
                # RGB 모드로 변환 (투명도 제거)
                if img.mode in ('RGBA', 'LA'):
                    logger.debug("🛠️ 투명도 제거 및 RGB 변환 시작")
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    logger.debug(f"🛠️ {img.mode} -> RGB 모드 변환")
                    img = img.convert('RGB')
                
                # 비율 유지하면서 리사이징
                img.thumbnail(self.max_size, Image.Resampling.LANCZOS)
                new_size = img.size
                logger.debug(f"🛠️ 리사이징 완료: {original_size} -> {new_size}")
                
                # 품질 최적화하여 저장
                logger.debug("🛠️ 이미지 저장 시작 (JPEG, 품질=85)")
                img.save(output_path, 'JPEG', quality=85, optimize=True)
                
                # 저장된 파일 크기 확인
                saved_size = os.path.getsize(output_path)
                logger.debug(f"🛠️ 저장된 파일 크기: {saved_size:,} bytes ({saved_size//1024:.1f}KB)")
                
                logger.info(f"✅ 이미지 리사이징 완료: {os.path.basename(output_path)}")
                return True
                
        except Exception as e:
            logger.error(f"❌ 이미지 리사이징 중 오류 발생: {e}")
            return False
    
    def resize_image_from_bytes(self, image_bytes: bytes, output_path: str) -> bool:
        """바이트 데이터로부터 이미지 리사이징"""
        logger.debug(f"🛠️ 바이트 데이터 이미지 리사이징 시작: {len(image_bytes)} bytes -> {os.path.basename(output_path)}")
        
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                original_size = img.size
                original_mode = img.mode
                logger.debug(f"🛠️ 원본 이미지: 크기={original_size}, 모드={original_mode}")
                
                # RGB 모드로 변환 (투명도 제거)
                if img.mode in ('RGBA', 'LA'):
                    logger.debug("🛠️ 투명도 제거 및 RGB 변환 시작")
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    logger.debug(f"🛠️ {img.mode} -> RGB 모드 변환")
                    img = img.convert('RGB')
                
                # 비율 유지하면서 리사이징
                img.thumbnail(self.max_size, Image.Resampling.LANCZOS)
                new_size = img.size
                logger.debug(f"🛠️ 리사이징 완료: {original_size} -> {new_size}")
                
                # 품질 최적화하여 저장
                logger.debug("🛠️ 이미지 저장 시작 (JPEG, 품질=85)")
                img.save(output_path, 'JPEG', quality=85, optimize=True)
                
                # 저장된 파일 크기 확인
                saved_size = os.path.getsize(output_path)
                logger.debug(f"🛠️ 저장된 파일 크기: {saved_size:,} bytes ({saved_size//1024:.1f}KB)")
                
                logger.info(f"✅ 바이트 데이터 이미지 리사이징 완료: {os.path.basename(output_path)}")
                return True
                
        except Exception as e:
            logger.error(f"❌ 바이트 데이터 이미지 리사이징 중 오류 발생: {e}")
            return False
    
    def process_image(self, uploaded_file, output_dir: str) -> Optional[str]:
        """업로드된 이미지 전처리 (Streamlit 또는 FastAPI UploadFile 지원)"""
        logger.debug(f"🛠️ 단일 이미지 처리 시작: {getattr(uploaded_file, 'name', getattr(uploaded_file, 'filename', 'unknown'))}")
        logger.debug(f"🛠️ 출력 디렉토리: {output_dir}")
        
        try:
            # 출력 디렉토리 생성
            os.makedirs(output_dir, exist_ok=True)
            logger.debug(f"🛠️ 출력 디렉토리 생성 완료: {output_dir}")
            
            # 최종 파일명 생성
            final_filename = f"product_{uuid.uuid4().hex}.jpg"
            final_path = os.path.join(output_dir, final_filename)
            logger.debug(f"🛠️ 최종 파일 경로: {final_path}")
            
            # FastAPI UploadFile인지 Streamlit 업로드 파일인지 확인
            if hasattr(uploaded_file, 'read'):
                # FastAPI UploadFile
                logger.debug("🛠️ FastAPI UploadFile 감지")
                try:
                    # 파일 포인터를 처음으로 되돌리기
                    uploaded_file.file.seek(0)
                    image_bytes = uploaded_file.file.read()
                    logger.debug(f"🛠️ FastAPI UploadFile 바이트 읽기 완료: {len(image_bytes)} bytes")
                except Exception as read_error:
                    logger.error(f"❌ FastAPI UploadFile 읽기 실패: {read_error}")
                    return None
                
                # 바이트 데이터 유효성 검증
                if not self.validate_image_from_bytes(image_bytes):
                    logger.warning("⚠️ FastAPI UploadFile 이미지 유효성 검증 실패")
                    return None
                
                # 바이트 데이터에서 직접 리사이징
                if self.resize_image_from_bytes(image_bytes, final_path):
                    relative_path = os.path.relpath(final_path, 
                        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(final_path)))))
                    logger.info(f"✅ FastAPI UploadFile 이미지 처리 완료: {relative_path}")
                    return relative_path
                else:
                    logger.warning("⚠️ FastAPI UploadFile 이미지 리사이징 실패")
                    return None
                    
            elif hasattr(uploaded_file, 'getbuffer'):
                # Streamlit 업로드 파일
                logger.debug("🛠️ Streamlit 업로드 파일 감지")
                
                # 임시 파일 저장
                temp_filename = f"temp_{uuid.uuid4().hex}.jpg"
                temp_path = os.path.join(output_dir, temp_filename)
                logger.debug(f"🛠️ 임시 파일 경로: {temp_path}")
                
                # Streamlit 업로드 파일 저장
                logger.debug("🛠️ Streamlit 업로드 파일 저장 시작")
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                file_size = os.path.getsize(temp_path)
                logger.debug(f"🛠️ 임시 파일 저장 완료: {file_size:,} bytes")
                
                # 이미지 유효성 검증
                logger.debug("🛠️ 이미지 유효성 검증 시작")
                if not self.validate_image(temp_path):
                    logger.warning("⚠️ Streamlit 이미지 유효성 검증 실패, 임시 파일 삭제")
                    os.remove(temp_path)
                    return None
                
                # 이미지 리사이징 및 최적화
                logger.debug("🛠️ 이미지 리사이징 및 최적화 시작")
                if self.resize_image(temp_path, final_path):
                    # 임시 파일 삭제
                    os.remove(temp_path)
                    logger.debug("🛠️ 임시 파일 삭제 완료")
                    
                    # 상대 경로 생성
                    relative_path = os.path.relpath(final_path, 
                        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(final_path)))))
                    logger.info(f"✅ Streamlit 단일 이미지 처리 완료: {relative_path}")
                    return relative_path
                else:
                    # 실패시 임시 파일 삭제
                    os.remove(temp_path)
                    logger.warning("⚠️ Streamlit 이미지 리사이징 실패, 임시 파일 삭제")
                    return None
            else:
                logger.error("❌ 지원하지 않는 파일 타입")
                return None
                
        except Exception as e:
            logger.error(f"❌ 이미지 처리 중 오류 발생: {e}")
            return None
    
    def copy_existing_image(self, source_path: str, output_dir: str) -> Optional[str]:
        """기존 이미지 복사 및 전처리"""
        logger.debug(f"🛠️ 기존 이미지 복사 및 전처리 시작: {source_path}")
        
        try:
            # 이미지 유효성 검증
            logger.debug("🛠️ 기존 이미지 유효성 검증 시작")
            if not self.validate_image(source_path):
                logger.warning("⚠️ 기존 이미지 유효성 검증 실패")
                return None
            
            # 출력 디렉토리 생성
            os.makedirs(output_dir, exist_ok=True)
            logger.debug(f"🛠️ 출력 디렉토리 생성 완료: {output_dir}")
            
            # 최종 파일명 생성
            final_filename = f"product_{uuid.uuid4().hex}.jpg"
            final_path = os.path.join(output_dir, final_filename)
            logger.debug(f"🛠️ 최종 파일 경로: {final_path}")
            
            # 이미지 리사이징 및 최적화
            logger.debug("🛠️ 기존 이미지 리사이징 및 최적화 시작")
            if self.resize_image(source_path, final_path):
                logger.info(f"✅ 기존 이미지 복사 및 전처리 완료: {os.path.basename(final_path)}")
                return final_path
            else:
                logger.warning("⚠️ 기존 이미지 리사이징 실패")
                return None
                
        except Exception as e:
            logger.error(f"❌ 이미지 복사 중 오류 발생: {e}")
            return None
    
    def process_multiple_images(self, uploaded_files, output_dir: str) -> List[str]:
        """여러 업로드된 이미지 전처리 (Streamlit 또는 FastAPI UploadFile 모두 지원)"""
        logger.debug(f"🛠️ 다중 이미지 처리 시작: {len(uploaded_files)}개 파일")
        logger.debug(f"🛠️ 출력 디렉토리: {output_dir}")
        
        try:
            # 출력 디렉토리 생성
            os.makedirs(output_dir, exist_ok=True)
            logger.debug(f"🛠️ 출력 디렉토리 생성 완료: {output_dir}")
            
            processed_paths = []
            success_count = 0
            fail_count = 0
            
            for i, uploaded_file in enumerate(uploaded_files):
                file_name = getattr(uploaded_file, 'name', getattr(uploaded_file, 'filename', f'file_{i}'))
                logger.debug(f"🛠️ 이미지 {i+1}/{len(uploaded_files)} 처리 시작: {file_name}")
                
                try:
                    # 최종 파일명 생성
                    final_filename = f"product_{uuid.uuid4().hex}_{i}.jpg"
                    final_path = os.path.join(output_dir, final_filename)
                    
                    # FastAPI UploadFile인지 Streamlit 업로드 파일인지 확인
                    if hasattr(uploaded_file, 'read'):
                        # FastAPI UploadFile
                        logger.debug(f"🛠️ 이미지 {i+1}: FastAPI UploadFile 감지")
                        try:
                            # 파일 포인터를 처음으로 되돌리기
                            uploaded_file.file.seek(0)
                            image_bytes = uploaded_file.file.read()
                            logger.debug(f"🛠️ 이미지 {i+1} 바이트 읽기 완료: {len(image_bytes)} bytes")
                        except Exception as read_error:
                            logger.error(f"❌ 이미지 {i+1} 읽기 실패: {read_error}")
                            fail_count += 1
                            continue
                        
                        # 바이트 데이터에서 직접 리사이징
                        if self.resize_image_from_bytes(image_bytes, final_path):
                            relative_path = os.path.relpath(final_path, 
                                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(final_path)))))
                            processed_paths.append(relative_path)
                            success_count += 1
                            logger.info(f"✅ 이미지 {i+1} 처리 완료: {relative_path}")
                        else:
                            fail_count += 1
                            logger.warning(f"⚠️ 이미지 {i+1} 리사이징 실패")
                            
                    elif hasattr(uploaded_file, 'getbuffer'):
                        # Streamlit 업로드 파일
                        logger.debug(f"🛠️ 이미지 {i+1}: Streamlit 업로드 파일 감지")
                        
                        # 임시 파일 저장
                        temp_filename = f"temp_{uuid.uuid4().hex}_{i}.jpg"
                        temp_path = os.path.join(output_dir, temp_filename)
                        
                        # Streamlit 업로드 파일 저장
                        with open(temp_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        file_size = os.path.getsize(temp_path)
                        logger.debug(f"🛠️ 이미지 {i+1} 임시 저장 완료: {file_size:,} bytes")
                        
                        # 이미지 유효성 검증
                        if not self.validate_image(temp_path):
                            os.remove(temp_path)
                            logger.warning(f"⚠️ 이미지 {i+1} 처리 실패: 유효성 검증 실패")
                            fail_count += 1
                            continue
                        
                        # 이미지 리사이징 및 최적화
                        if self.resize_image(temp_path, final_path):
                            # 상대 경로로 변환
                            relative_path = os.path.relpath(final_path, 
                                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(final_path)))))
                            processed_paths.append(relative_path)
                            success_count += 1
                            logger.info(f"✅ 이미지 {i+1} 처리 완료: {relative_path}")
                        else:
                            fail_count += 1
                            logger.warning(f"⚠️ 이미지 {i+1} 리사이징 실패")
                        
                        # 임시 파일 삭제
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                    else:
                        fail_count += 1
                        logger.error(f"❌ 이미지 {i+1} 처리 실패: 지원하지 않는 파일 타입")
                        continue
                        
                except Exception as img_error:
                    fail_count += 1
                    logger.error(f"❌ 이미지 {i+1} 처리 중 오류: {img_error}")
                    continue
            
            # 최종 결과 로그
            total_count = len(uploaded_files)
            logger.info(f"✅ 다중 이미지 처리 완료: 총 {total_count}개 중 {success_count}개 성공, {fail_count}개 실패")
            
            if success_count == 0:
                logger.warning("⚠️ 모든 이미지 처리 실패")
            elif fail_count > 0:
                logger.warning(f"⚠️ 일부 이미지 처리 실패: {fail_count}개")
                
            return processed_paths
            
        except Exception as e:
            logger.error(f"❌ 다중 이미지 처리 중 오류 발생: {e}")
            return []