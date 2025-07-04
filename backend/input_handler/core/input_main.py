import os
import yaml
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from .form_parser import FormParser
from .image_preprocess import ImagePreprocessor

logger = logging.getLogger(__name__)


class InputHandler:
    """입력 처리 메인 클래스"""
    
    def __init__(self, project_root: str = None):
        # 루트 디렉토리 설정
        if project_root:
            self.project_root = project_root
        else:
            # 현재 파일 위치에서 프로젝트 루트 찾기
            current_file = os.path.abspath(__file__)
            # backend/input_handler/core/input_main.py에서 루트까지 3단계 위
            self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file))))

        self.form_parser = FormParser()
        self.image_processor = ImagePreprocessor()
        
        # 기본 디렉토리 설정
        self.data_dir = os.path.join(self.project_root, "backend", "data")
        self.input_dir = os.path.join(self.data_dir, "input")
        self.output_dir = os.path.join(self.data_dir, "output")
        self.result_dir = os.path.join(self.data_dir, "result")
        
        # 디렉토리 생성
        self._create_directories()

        
    
    def _create_directories(self):
        """필요한 디렉토리 생성"""
        directories = [self.data_dir, self.input_dir, self.output_dir, self.result_dir]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def create_config_yaml(self, product_data: Dict[str, Any], 
                          verbose: bool = False) -> str:
        """config.yaml 파일 생성"""
        try:
            config = {
                'settings': {
                    'verbose': verbose,
                    'project_root': self.project_root
                },
                'data': {
                    'output_path': self.output_dir,
                    'result_path': self.result_dir
                },
                'input': product_data
            }
            
            # config.yaml 파일 경로
            config_path = os.path.join(self.project_root, "config.yaml")
            
            # YAML 파일 생성
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, 
                         allow_unicode=True, sort_keys=False)
            
            logger.info(f"config.yaml 생성 완료: {config_path}")
            return config_path
            
        except Exception as e:
            logger.error(f"config.yaml 생성 실패: {str(e)}")
            raise Exception(f"설정 파일 생성 중 오류 발생: {str(e)}")
    
    def process_image_upload(self, uploaded_file) -> Optional[str]:
        """업로드된 이미지 처리"""
        try:
            if uploaded_file is None:
                return None
            
            # 이미지 처리
            image_path = self.image_processor.process_image(uploaded_file, self.input_dir)
            
            if image_path:
                # 상대 경로로 변환
                relative_path = os.path.relpath(image_path, self.project_root)
                logger.info(f"이미지 업로드 완료: {relative_path}")
                return relative_path
            else:
                logger.error("이미지 처리 실패")
                return None
                
        except Exception as e:
            logger.error(f"이미지 업로드 처리 중 오류: {str(e)}")
            return None
    
    def process_form_input(self, form_data: Dict[str, Any], 
                      uploaded_files=None) -> Dict[str, Any]:  # uploaded_file → uploaded_files
        """전체 입력 처리 파이프라인"""
        try:
            # 1. 폼 데이터 파싱 및 검증 (이미지 제외)
            temp_data = form_data.copy()
            temp_data['image_path'] = ['temp']  # 임시 값 (검증 통과용)
            parsed_data = self.form_parser.parse_form_data(temp_data)
            
            # 2. 이미지 처리 (필수)
            if not uploaded_files:
                raise ValueError("이미지는 필수 항목입니다. 최소 1개의 이미지를 업로드해주세요.")
            
            image_paths = self.process_multiple_images(uploaded_files)
            if not image_paths:
                raise ValueError("이미지 처리에 실패했습니다. 올바른 이미지 파일을 업로드해주세요.")
            
            parsed_data['image_path'] = image_paths
            
            # 3. config.yaml 생성
            config_path = self.create_config_yaml(parsed_data)
            
            logger.info("입력 처리 파이프라인 완료")
            return parsed_data
            
        except Exception as e:
            logger.error(f"입력 처리 파이프라인 실패: {str(e)}")
            raise Exception(f"입력 처리 중 오류 발생: {str(e)}")

    def process_multiple_images(self, uploaded_files) -> List[str]:
        """여러 업로드된 이미지 처리"""
        try:
            if not uploaded_files:
                return []
            
            # 이미지 처리
            image_paths = self.image_processor.process_multiple_images(uploaded_files, self.input_dir)
            
            if image_paths:
                logger.info(f"이미지 {len(image_paths)}개 업로드 완료")
                return image_paths
            else:
                logger.error("이미지 처리 실패")
                return []
                
        except Exception as e:
            logger.error(f"다중 이미지 업로드 처리 중 오류: {str(e)}")
            return []
    
    def load_config(self, config_path: str = None) -> Dict[str, Any]:
        """config.yaml 파일 로드"""
        try:
            if config_path is None:
                config_path = os.path.join(self.project_root, "config.yaml")
            
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {config_path}")
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            logger.info(f"config.yaml 로드 완료: {config_path}")
            return config
            
        except Exception as e:
            logger.error(f"config.yaml 로드 실패: {str(e)}")
            raise Exception(f"설정 파일 로드 중 오류 발생: {str(e)}")
    
    def get_product_input_dict(self, config_path: str = None) -> Dict[str, Any]:
        """config.yaml에서 product_input 딕셔너리 추출"""
        try:
            config = self.load_config(config_path)
            
            if 'input' not in config:
                raise ValueError("설정 파일에 'input' 섹션이 없습니다.")
            
            product_input = config['input']
            
            logger.info("product_input 딕셔너리 추출 완료")
            return product_input
            
        except Exception as e:
            logger.error(f"product_input 딕셔너리 추출 실패: {str(e)}")
            raise Exception(f"상품 입력 데이터 추출 중 오류 발생: {str(e)}")
    
    def validate_existing_config(self, config_path: str = None) -> bool:
        """기존 config.yaml 유효성 검증"""
        try:
            config = self.load_config(config_path)
            
            # 필수 섹션 확인
            required_sections = ['settings', 'data', 'input']
            for section in required_sections:
                if section not in config:
                    logger.error(f"필수 섹션 누락: {section}")
                    return False
            
            # 입력 데이터 검증
            input_data = config['input']
            validated_data = self.form_parser.schema(**input_data)
            
            logger.info("기존 config.yaml 유효성 검증 완료")
            return True
            
        except Exception as e:
            logger.error(f"config.yaml 유효성 검증 실패: {str(e)}")
            return False