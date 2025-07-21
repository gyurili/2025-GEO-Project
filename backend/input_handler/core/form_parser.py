import re
from typing import Dict, Any, Optional, List
import sys
from pathlib import Path

# 로거 임포트 추가
sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.logger import get_logger

from ..schemas.input_schema import ProductInputSchema

# 로거 설정
logger = get_logger(__name__)

class FormParser:
    """사용자 입력 폼 파싱 및 검증 클래스"""
    
    def __init__(self):
        logger.debug("🛠️ FormParser 인스턴스 초기화 시작")
        self.schema = ProductInputSchema
        logger.info("✅ FormParser 인스턴스 초기화 완료")
        
    def clean_text(self, text: str) -> str:
        """텍스트 정리 (공백, 특수문자 등)"""
        logger.debug(f"🛠️ 텍스트 정리 시작: 입력 길이={len(text) if text else 0}")
        
        if not text:
            logger.debug("🛠️ 빈 텍스트 입력, 빈 문자열 반환")
            return ""
            
        # 연속된 공백을 하나로 변환
        text = re.sub(r'\s+', ' ', text)
        
        # 앞뒤 공백 제거
        text = text.strip()
        
        # 특수문자 정리 (선택적)
        # text = re.sub(r'[^\w\s가-힣ㄱ-ㅎㅏ-ㅣ\-\(\)\[\]\/\.\,\!\?\:\;\']', '', text)
        
        logger.debug(f"🛠️ 텍스트 정리 완료: 출력 길이={len(text)}")
        return text
    
    def validate_price(self, price_input: Any) -> int:
        """가격 유효성 검증 및 변환"""
        logger.debug(f"🛠️ 가격 유효성 검증 시작: 입력값={price_input}, 타입={type(price_input)}")
        
        try:
            if isinstance(price_input, str):
                logger.debug("🛠️ 문자열 가격 입력 감지, 숫자 변환 시작")
                # 콤마, 원화 표시 등 제거
                price_str = re.sub(r'[,원￦$]', '', price_input)
                price = int(price_str)
                logger.debug(f"🛠️ 문자열 가격 변환 완료: '{price_input}' -> {price}")
            else:
                price = int(price_input)
                logger.debug(f"🛠️ 숫자 가격 변환 완료: {price}")
                
            # 가격 범위 검증
            if price < 0:
                logger.warning(f"⚠️ 가격 범위 오류: {price} (음수 가격)")
                raise ValueError("가격은 0원 이상이어야 합니다.")
            if price > 10000000:
                logger.warning(f"⚠️ 가격 범위 오류: {price} (상한선 초과)")
                raise ValueError("가격은 1천만원 이하여야 합니다.")
                
            logger.info(f"✅ 가격 유효성 검증 완료: {price:,}원")
            return price
            
        except ValueError as e:
            logger.error(f"❌ 가격 검증 실패: {e}")
            raise ValueError(f"올바른 가격을 입력해주세요: {str(e)}")
    
    def validate_css_type(self, css_type: Any) -> int:
        """CSS 타입 유효성 검증"""
        logger.debug(f"🛠️ CSS 타입 유효성 검증 시작: 입력값={css_type}, 타입={type(css_type)}")
        
        try:
            if isinstance(css_type, str):
                logger.debug("🛠️ 문자열 CSS 타입 입력 감지, 숫자 변환 시작")
                css_type = int(css_type.strip())
                logger.debug(f"🛠️ 문자열 CSS 타입 변환 완료: '{css_type}' -> {css_type}")
            else:
                css_type = int(css_type)
                logger.debug(f"🛠️ 숫자 CSS 타입 변환 완료: {css_type}")
                
            # CSS 타입 값 검증
            if css_type not in [1, 2]:
                logger.warning(f"⚠️ CSS 타입 범위 오류: {css_type} (1 또는 2만 허용)")
                raise ValueError("CSS 타입은 1 또는 2만 선택 가능합니다.")
                
            logger.info(f"✅ CSS 타입 유효성 검증 완료: {css_type}")
            return css_type
            
        except ValueError as e:
            logger.error(f"❌ CSS 타입 검증 실패: {e}")
            raise ValueError(f"올바른 CSS 타입을 선택해주세요: {str(e)}")
        """상품 특징 추출 및 정리"""
        logger.debug(f"🛠️ 상품 특징 추출 시작: 입력 길이={len(features_input) if features_input else 0}")
        
        if not features_input:
            logger.debug("🛠️ 빈 특징 입력, 빈 문자열 반환")
            return ""
            
        features = self.clean_text(features_input)
        
        # 특징이 너무 길면 자르기
        if len(features) > 500:
            logger.warning(f"⚠️ 상품 특징 길이 초과: {len(features)}자 -> 500자로 단축")
            features = features[:497] + "..."
            
        logger.info(f"✅ 상품 특징 추출 완료: {len(features)}자")
        return features
    
    def validate_category(self, category: str) -> str:
        """카테고리 유효성 검증"""
        logger.debug(f"🛠️ 카테고리 유효성 검증 시작: '{category}'")
        
        if not category:
            logger.error("❌ 카테고리 검증 실패: 필수 입력사항 누락")
            raise ValueError("카테고리는 필수 입력사항입니다.")
            
        category = self.clean_text(category)
        
        # 카테고리 길이 제한
        if len(category) > 50:
            logger.warning(f"⚠️ 카테고리 길이 초과: {len(category)}자 -> 50자로 단축")
            category = category[:50]
            
        logger.info(f"✅ 카테고리 유효성 검증 완료: '{category}'")
        return category

    def extract_features(self, features_input: str) -> str:
        """상품 특징 추출 및 정리"""
        logger.debug(f"🛠️ 상품 특징 추출 시작: 입력 길이={len(features_input) if features_input else 0}")
        
        if not features_input:
            logger.debug("🛠️ 빈 특징 입력, 빈 문자열 반환")
            return ""
            
        features = self.clean_text(features_input)
        
        # 특징이 너무 길면 자르기
        if len(features) > 500:
            logger.warning(f"⚠️ 상품 특징 길이 초과: {len(features)}자 -> 500자로 단축")
            features = features[:497] + "..."
            
        logger.info(f"✅ 상품 특징 추출 완료: {len(features)}자")
        return features
    
    def validate_brand(self, brand: str) -> str:
        """브랜드 유효성 검증"""
        logger.debug(f"🛠️ 브랜드 유효성 검증 시작: '{brand}'")
        
        if not brand:
            logger.error("❌ 브랜드 검증 실패: 필수 입력사항 누락")
            raise ValueError("브랜드명은 필수 입력사항입니다.")
            
        brand = self.clean_text(brand)
        
        # 브랜드명 길이 제한
        if len(brand) > 50:
            logger.warning(f"⚠️ 브랜드명 길이 초과: {len(brand)}자 -> 50자로 단축")
            brand = brand[:50]
            
        logger.info(f"✅ 브랜드 유효성 검증 완료: '{brand}'")
        return brand
    
    def validate_image_paths(self, image_paths: Optional[List[str]]) -> Optional[List[str]]:
        """이미지 경로 유효성 검증 (선택사항)"""
        logger.debug(f"🛠️ 이미지 경로 유효성 검증 시작: {len(image_paths) if image_paths else 0}개")
        
        if not image_paths:
            logger.debug("🛠️ 이미지 경로 없음 - 선택사항이므로 None 반환")
            return None
        
        if isinstance(image_paths, str):
            # 단일 문자열인 경우 리스트로 변환
            logger.debug("🛠️ 단일 이미지 경로를 리스트로 변환")
            image_paths = [image_paths]
        
        # 빈 문자열이나 'temp' 같은 임시 값 제거
        valid_paths = []
        for path in image_paths:
            if path and path.strip() and path != 'temp':
                valid_paths.append(path.strip())
                logger.debug(f"🛠️ 유효한 이미지 경로: {path}")
            else:
                logger.debug(f"🛠️ 무효한 이미지 경로 제외: {path}")
        
        if valid_paths:
            logger.info(f"✅ 이미지 경로 검증 완료: {len(valid_paths)}개")
            return valid_paths
        else:
            logger.debug("🛠️ 유효한 이미지 경로 없음")
            return None
    
    def parse_form_data(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """폼 데이터 파싱 및 검증"""
        logger.debug("🛠️ 폼 데이터 파싱 및 검증 시작")
        logger.debug(f"🛠️ 입력 폼 데이터 키: {list(form_data.keys())}")
        
        try:
            parsed_data = {}
            
            # 상품명
            logger.debug("🛠️ 상품명 검증 시작")
            if 'name' not in form_data or not form_data['name']:
                logger.error("❌ 상품명 검증 실패: 필수 입력사항 누락")
                raise ValueError("상품명은 필수 입력사항입니다.")
            parsed_data['name'] = self.clean_text(form_data['name'])
            logger.debug(f"🛠️ 상품명 처리 완료: '{parsed_data['name']}'")
            
            # 카테고리
            logger.debug("🛠️ 카테고리 검증 시작")
            parsed_data['category'] = self.validate_category(form_data.get('category', ''))
            
            # 가격
            logger.debug("🛠️ 가격 검증 시작")
            parsed_data['price'] = self.validate_price(form_data.get('price', 0))
            
            # 브랜드
            logger.debug("🛠️ 브랜드 검증 시작")
            parsed_data['brand'] = self.validate_brand(form_data.get('brand', ''))
            
            # CSS 타입
            logger.debug("🛠️ CSS 타입 검증 시작")
            parsed_data['css_type'] = self.validate_css_type(form_data.get('css_type', 1))
            
            # 특징
            logger.debug("🛠️ 상품 특징 처리 시작")
            parsed_data['features'] = self.extract_features(form_data.get('features', ''))
            
            # 이미지 경로
            logger.debug("🛠️ 이미지 경로 처리 시작")
            image_paths = self.validate_image_paths(form_data.get('image_path'))
            if image_paths:
                parsed_data['image_path'] = image_paths
                logger.debug(f"🛠️ 이미지 경로 설정: {len(image_paths)}개")
            else:
                logger.debug("🛠️ 이미지 경로 없음 - 선택사항이므로 제외")
            
            # Pydantic 스키마로 최종 검증 (이미지 필드 선택사항 처리)
            logger.debug("🛠️ Pydantic 스키마 검증 시작")
            
            # 이미지 필드가 없으면 빈 리스트로 설정하여 검증
            validation_data = parsed_data.copy()
            if 'image_path' not in validation_data:
                validation_data['image_path'] = []
                logger.debug("🛠️ 검증용 빈 image_path 설정")
            
            validated_data = self.schema(**validation_data)
            
            # 검증된 데이터에서 빈 image_path는 제거
            final_data = validated_data.dict()
            if 'image_path' in final_data and not final_data['image_path']:
                del final_data['image_path']
                logger.debug("🛠️ 빈 image_path 제거")
            
            logger.info("✅ 폼 데이터 파싱 및 검증 완료")
            return final_data
            
        except Exception as e:
            logger.error(f"❌ 폼 데이터 파싱 실패: {e}")
            raise ValueError(f"입력 데이터 검증 실패: {str(e)}")
    
    def create_product_summary(self, product_data: Dict[str, Any]) -> str:
        """상품 데이터 요약 생성"""
        logger.debug("🛠️ 상품 데이터 요약 생성 시작")
        logger.debug(f"🛠️ 요약할 데이터 키: {list(product_data.keys())}")
        
        try:
            summary = f"""
상품 정보 요약:
- 상품명: {product_data['name']}
- 카테고리: {product_data['category']}
- 브랜드: {product_data['brand']}
- 가격: {product_data['price']:,}원
- CSS 타입: {product_data['css_type']}
- 특징: {product_data['features'][:100]}{'...' if len(product_data['features']) > 100 else ''}
            """.strip()
            
            # 선택적 필드 추가
            if product_data.get('image_path'):
                if isinstance(product_data['image_path'], list):
                    summary += f"\n- 이미지: {len(product_data['image_path'])}개"
                    logger.debug(f"🛠️ 이미지 정보 추가: {len(product_data['image_path'])}개")
                else:
                    summary += f"\n- 이미지: {product_data['image_path']}"
                    logger.debug("🛠️ 단일 이미지 정보 추가")
            else:
                summary += "\n- 이미지: 없음"
                logger.debug("🛠️ 이미지 없음 표시")
                
            logger.info(f"✅ 상품 데이터 요약 생성 완료: {len(summary)}자")
            return summary
            
        except Exception as e:
            logger.error(f"❌ 상품 요약 생성 실패: {e}")
            return "상품 요약 생성 중 오류가 발생했습니다."