import os
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path

# 로거 임포트 추가
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.logger import get_logger

from .form_parser import FormParser
from .image_preprocess import ImagePreprocessor

# 로거 설정
logger = get_logger(__name__)

class InputHandler:
    """입력 처리 메인 클래스"""
    
    def __init__(self, project_root: str = None):
        logger.debug("🛠️ InputHandler 인스턴스 초기화 시작")
        
        # 루트 디렉토리 설정
        if project_root:
            self.project_root = project_root
            logger.debug(f"🛠️ 제공된 프로젝트 루트 사용: {project_root}")
        else:
            # 현재 파일 위치에서 프로젝트 루트 찾기
            current_file = os.path.abspath(__file__)
            # backend/input_handler/core/input_main.py에서 루트까지 3단계 위
            self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file))))
            logger.debug(f"🛠️ 자동 감지된 프로젝트 루트: {self.project_root}")

        # 파서 및 프로세서 초기화
        logger.debug("🛠️ FormParser 및 ImagePreprocessor 초기화 시작")
        self.form_parser = FormParser()
        self.image_processor = ImagePreprocessor()
        
        # 기본 디렉토리 설정
        self.data_dir = os.path.join(self.project_root, "backend", "data")
        self.input_dir = os.path.join(self.data_dir, "input")
        self.output_dir = os.path.join(self.data_dir, "output")
        self.result_dir = os.path.join(self.data_dir, "result")

        self.base_config_dir = Path("backend/data/config")
        self.base_config_dir.mkdir(parents=True, exist_ok=True)
        
        logger.debug(f"🛠️ 디렉토리 경로 설정 완료:")
        logger.debug(f"🛠️   - data: {self.data_dir}")
        logger.debug(f"🛠️   - input: {self.input_dir}")
        logger.debug(f"🛠️   - output: {self.output_dir}")
        logger.debug(f"🛠️   - result: {self.result_dir}")
        
        # 디렉토리 생성
        self._create_directories()
        
        logger.info("✅ InputHandler 인스턴스 초기화 완료")
    
    def _create_directories(self):
        """필요한 디렉토리 생성"""
        logger.debug("🛠️ 필요한 디렉토리 생성 시작")
        
        directories = [self.data_dir, self.input_dir, self.output_dir, self.result_dir]
        created_count = 0
        existing_count = 0
        
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                created_count += 1
                logger.debug(f"🛠️ 디렉토리 생성: {directory}")
            else:
                existing_count += 1
                logger.debug(f"🛠️ 기존 디렉토리 확인: {directory}")
        
        logger.info(f"✅ 디렉토리 설정 완료: 생성 {created_count}개, 기존 {existing_count}개")
    
    def create_config_yaml(self, product_data: Dict[str, Any], 
                          verbose: bool = False) -> str:
        """config.yaml 파일 생성"""
        logger.debug("🛠️ config.yaml 파일 생성 시작")
        logger.debug(f"🛠️ verbose 모드: {verbose}")
        logger.debug(f"🛠️ 상품 데이터 키: {list(product_data.keys())}")
        
        try:
            # 설정 구조 생성
            config = {
                'settings': {
                    'verbose': verbose,
                    'project_root': self.project_root
                },
                'data': {
                    'output_path': self.output_dir,
                    'result_path': self.result_dir
                },
                'db_config': {
                    'host': '',
                    'user': 'GEOGEO',
                    'password': '',
                    'db': 'geo_db'
                },
                'input': product_data
            }
            
            logger.debug(f"🛠️ 설정 구조 생성 완료: {len(config)} 섹션")
            
            # config.yaml 파일 경로
            config_path = os.path.join(self.project_root, "config.yaml")
            logger.debug(f"🛠️ 설정 파일 경로: {config_path}")
            
            # YAML 파일 생성
            logger.debug("🛠️ YAML 파일 쓰기 시작")
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, 
                         allow_unicode=True, sort_keys=False)
            
            # 생성된 파일 크기 확인
            file_size = os.path.getsize(config_path)
            logger.debug(f"🛠️ 생성된 파일 크기: {file_size} bytes")
            
            logger.info(f"✅ config.yaml 생성 완료: {os.path.basename(config_path)}")
            return config_path
            
        except Exception as e:
            logger.error(f"❌ config.yaml 생성 실패: {e}")
            raise Exception(f"설정 파일 생성 중 오류 발생: {str(e)}")
    
    def process_image_upload(self, uploaded_file) -> Optional[str]:
        """업로드된 이미지 처리 (단일 파일)"""
        logger.debug(f"🛠️ 단일 이미지 업로드 처리 시작: {getattr(uploaded_file, 'name', getattr(uploaded_file, 'filename', 'None')) if uploaded_file else 'None'}")
        
        try:
            if uploaded_file is None:
                logger.warning("⚠️ 업로드된 파일이 없음")
                return None
            
            # 이미지 처리
            logger.debug("🛠️ ImagePreprocessor를 통한 이미지 처리 시작")
            image_path = self.image_processor.process_image(uploaded_file, self.input_dir)
            
            if image_path:
                # 상대 경로로 변환
                relative_path = os.path.relpath(image_path, self.project_root)
                logger.info(f"✅ 단일 이미지 업로드 완료: {relative_path}")
                return relative_path
            else:
                logger.warning("⚠️ 이미지 처리 실패 - 유효하지 않은 이미지")
                return None
                
        except Exception as e:
            logger.error(f"❌ 이미지 업로드 처리 중 오류: {e}")
            return None
    
    def get_user_config_path(self, user_session_id: str) -> Path:
        """사용자별 설정 파일 경로 반환"""
        return self.base_config_dir / f"config_{user_session_id}.yaml"
    
    def process_form_input_with_session(self, form_data: dict, uploaded_files, user_session_id: str):
        """사용자별 세션을 고려한 폼 입력 처리"""
        try:
            # 사용자별 설정 파일 경로
            config_path = self.get_user_config_path(user_session_id)
            
            # 사용자별 이미지 저장 경로
            user_input_dir = Path(f"backend/data/input/{user_session_id}")
            user_input_dir.mkdir(parents=True, exist_ok=True)
            
            # 기존 로직 + 사용자별 경로 적용
            product_input = self.process_form_input(form_data, uploaded_files)
            product_input['user_session_id'] = user_session_id
            product_input['config_path'] = str(config_path)
            
            # 사용자별 설정 파일 저장
            self.save_config_with_session(product_input, config_path)
            
            return product_input
            
        except Exception as e:
            logger.error(f"❌ 사용자별 폼 입력 처리 실패 (세션: {user_session_id}): {e}")
            raise
    
    def save_config_with_session(self, product_input: dict, config_path: Path):
        """사용자별 설정 파일 저장"""
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(product_input, f, default_flow_style=False, ensure_ascii=False)
            logger.info(f"✅ 사용자별 설정 파일 저장: {config_path}")
        except Exception as e:
            logger.error(f"❌ 설정 파일 저장 실패: {e}")
            raise
    
    def process_form_input(self, form_data: Dict[str, Any], 
                      uploaded_files=None) -> Dict[str, Any]:
        """전체 입력 처리 파이프라인"""
        logger.debug("🛠️ 전체 입력 처리 파이프라인 시작")
        logger.debug(f"🛠️ 폼 데이터 키: {list(form_data.keys())}")
        logger.debug(f"🛠️ 업로드된 파일 수: {len(uploaded_files) if uploaded_files else 0}")
        
        try:
            # 1. 폼 데이터 파싱 및 검증 (이미지 제외)
            logger.debug("🛠️ 1단계: 폼 데이터 파싱 및 검증 시작")
            temp_data = form_data.copy()
            
            # 이미지가 있는 경우에만 임시 값 설정
            if uploaded_files and len(uploaded_files) > 0:
                temp_data['image_path_list'] = ['temp']  # 임시 값 (검증 통과용)
                logger.debug("🛠️ 이미지 파일 존재 - 임시 image_path_list 설정")
            else:
                logger.debug("🛠️ 이미지 파일 없음 - image_path_list 설정하지 않음")
            
            parsed_data = self.form_parser.parse_form_data(temp_data)
            logger.debug("🛠️ 폼 데이터 파싱 완료")
            
            # 2. 이미지 처리 (선택사항)
            logger.debug("🛠️ 2단계: 이미지 처리 시작")
            if uploaded_files and len(uploaded_files) > 0:
                logger.debug(f"🛠️ 이미지 파일 처리 시작: {len(uploaded_files)}개")
                image_paths = self.process_multiple_images(uploaded_files)
                
                if image_paths:
                    parsed_data['image_path_list'] = image_paths
                    logger.debug(f"🛠️ 이미지 경로 설정 완료: {len(image_paths)}개")
                else:
                    logger.warning("⚠️ 일부 또는 모든 이미지 처리 실패")
                    # 이미지 처리 실패해도 계속 진행 (이미지는 선택사항)
                    if 'image_path_list' in parsed_data:
                        del parsed_data['image_path_list']
            else:
                logger.debug("🛠️ 업로드된 이미지 없음 - 이미지 처리 건너뜀")
                # 임시로 설정된 image_path_list 제거
                if 'image_path_list' in parsed_data:
                    del parsed_data['image_path_list']
            
            # 3. config.yaml 생성
            logger.debug("🛠️ 3단계: config.yaml 생성 시작")
            config_path = self.create_config_yaml(parsed_data)
            logger.debug(f"🛠️ config.yaml 생성 완료: {config_path}")
            
            logger.info("✅ 전체 입력 처리 파이프라인 완료")
            return parsed_data
            
        except Exception as e:
            logger.error(f"❌ 입력 처리 파이프라인 실패: {e}")
            raise Exception(f"입력 처리 중 오류 발생: {str(e)}")

    def process_multiple_images(self, uploaded_files) -> List[str]:
        """여러 업로드된 이미지 처리"""
        logger.debug(f"🛠️ 다중 이미지 처리 시작: {len(uploaded_files)}개 파일")
        
        try:
            if not uploaded_files:
                logger.warning("⚠️ 처리할 이미지 파일이 없음")
                return []
            
            # 파일명 로그 (FastAPI와 Streamlit 모두 지원)
            file_names = []
            for f in uploaded_files:
                if hasattr(f, 'filename'):  # FastAPI UploadFile
                    file_names.append(f.filename)
                elif hasattr(f, 'name'):   # Streamlit 업로드 파일
                    file_names.append(f.name)
                else:
                    file_names.append('unknown')
            logger.debug(f"🛠️ 업로드된 파일들: {file_names}")
            
            # 이미지 처리
            logger.debug("🛠️ ImagePreprocessor를 통한 다중 이미지 처리 시작")
            image_paths = self.image_processor.process_multiple_images(uploaded_files, self.input_dir)
            
            if image_paths:
                success_count = len(image_paths)
                total_count = len(uploaded_files)
                
                if success_count == total_count:
                    logger.info(f"✅ 모든 이미지 처리 완료: {success_count}개")
                else:
                    logger.warning(f"⚠️ 일부 이미지만 처리 완료: {success_count}/{total_count}개")
                
                logger.debug(f"🛠️ 처리된 이미지 경로들: {image_paths}")
                return image_paths
            else:
                logger.warning("⚠️ 모든 이미지 처리 실패")
                return []
                
        except Exception as e:
            logger.error(f"❌ 다중 이미지 처리 중 오류: {e}")
            return []
    
    def load_config(self, config_path: str = None) -> Dict[str, Any]:
        """config.yaml 파일 로드"""
        if config_path is None:
            config_path = os.path.join(self.project_root, "config.yaml")
        
        logger.debug(f"🛠️ config.yaml 파일 로드 시작: {config_path}")
        
        try:
            # 파일 존재 확인
            if not os.path.exists(config_path):
                logger.error(f"❌ 설정 파일을 찾을 수 없습니다: {config_path}")
                raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {config_path}")
            
            # 파일 크기 확인
            file_size = os.path.getsize(config_path)
            logger.debug(f"🛠️ 설정 파일 크기: {file_size} bytes")
            
            # YAML 파일 읽기
            logger.debug("🛠️ YAML 파일 파싱 시작")
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 로드된 설정 정보
            if config:
                sections = list(config.keys())
                logger.debug(f"🛠️ 로드된 설정 섹션: {sections}")
                logger.info(f"✅ config.yaml 로드 완료: {os.path.basename(config_path)}")
            else:
                logger.warning("⚠️ 빈 설정 파일 로드")
            
            return config
            
        except yaml.YAMLError as e:
            logger.error(f"❌ YAML 파싱 실패: {e}")
            raise Exception(f"설정 파일 파싱 중 오류 발생: {str(e)}")
        except Exception as e:
            logger.error(f"❌ config.yaml 로드 실패: {e}")
            raise Exception(f"설정 파일 로드 중 오류 발생: {str(e)}")
    
    def get_product_input_dict(self, config_path: str = None) -> Dict[str, Any]:
        """config.yaml에서 product_input 딕셔너리 추출"""
        logger.debug("🛠️ product_input 딕셔너리 추출 시작")
        
        try:
            # 설정 파일 로드
            config = self.load_config(config_path)
            
            # input 섹션 확인
            if 'input' not in config:
                logger.error("❌ 설정 파일에 'input' 섹션이 없습니다")
                raise ValueError("설정 파일에 'input' 섹션이 없습니다.")
            
            product_input = config['input']
            
            # 추출된 데이터 정보
            if isinstance(product_input, dict):
                keys = list(product_input.keys())
                logger.debug(f"🛠️ 추출된 상품 데이터 키: {keys}")
                
                # 필수 필드 확인
                required_fields = ['name', 'category', 'price', 'brand', 'features']
                missing_fields = [field for field in required_fields if field not in product_input]
                
                if missing_fields:
                    logger.warning(f"⚠️ 누락된 필수 필드: {missing_fields}")
                else:
                    logger.debug("🛠️ 모든 필수 필드 확인됨")
                
                # 이미지 필드 확인 (선택사항)
                if 'image_path_list' in product_input:
                    image_count = len(product_input['image_path_list']) if isinstance(product_input['image_path_list'], list) else 1
                    logger.debug(f"🛠️ 이미지 파일: {image_count}개")
                else:
                    logger.debug("🛠️ 이미지 파일 없음")
                
                logger.info("✅ product_input 딕셔너리 추출 완료")
            else:
                logger.warning("⚠️ product_input이 딕셔너리 형태가 아님")
            
            return product_input
            
        except Exception as e:
            logger.error(f"❌ product_input 딕셔너리 추출 실패: {e}")
            raise Exception(f"상품 입력 데이터 추출 중 오류 발생: {str(e)}")
    
    def validate_existing_config(self, config_path: str = None) -> bool:
        """기존 config.yaml 유효성 검증"""
        logger.debug("🛠️ 기존 config.yaml 유효성 검증 시작")
        
        try:
            # 설정 파일 로드
            config = self.load_config(config_path)
            
            # 필수 섹션 확인
            required_sections = ['settings', 'data', 'input']
            logger.debug(f"🛠️ 필수 섹션 확인: {required_sections}")
            
            missing_sections = []
            for section in required_sections:
                if section not in config:
                    missing_sections.append(section)
                    logger.warning(f"⚠️ 필수 섹션 누락: {section}")
                else:
                    logger.debug(f"🛠️ 섹션 확인됨: {section}")
            
            if missing_sections:
                logger.error(f"❌ 필수 섹션 누락: {missing_sections}")
                return False
            
            # 입력 데이터 검증 (이미지는 선택사항이므로 제외)
            logger.debug("🛠️ 입력 데이터 스키마 검증 시작")
            input_data = config['input']
            
            # 이미지 필드가 없어도 검증할 수 있도록 임시 추가
            temp_input_data = input_data.copy()
            if 'image_path' not in temp_input_data:
                temp_input_data['image_path'] = []  # 빈 리스트로 설정
            
            validated_data = self.form_parser.schema(**temp_input_data)
            logger.debug("🛠️ 스키마 검증 통과")
            
            logger.info("✅ config.yaml 유효성 검증 완료 - 유효함")
            return True
            
        except Exception as e:
            logger.error(f"❌ config.yaml 유효성 검증 실패: {e}")
            return False