import re
import logging
from typing import Dict, Any, Optional, List
from ..schemas.input_schema import ProductInputSchema

logger = logging.getLogger(__name__)


class FormParser:
    """사용자 입력 폼 파싱 및 검증 클래스"""
    
    def __init__(self):
        self.schema = ProductInputSchema
        
    def clean_text(self, text: str) -> str:
        """텍스트 정리 (공백, 특수문자 등)"""
        if not text:
            return ""
            
        # 연속된 공백을 하나로 변환
        text = re.sub(r'\s+', ' ', text)
        
        # 앞뒤 공백 제거
        text = text.strip()
        
        # 특수문자 정리 (선택적)
        # text = re.sub(r'[^\w\s가-힣ㄱ-ㅎㅏ-ㅣ\-\(\)\[\]\/\.\,\!\?\:\;\']', '', text)
        
        return text
    
    def validate_price(self, price_input: Any) -> int:
        """가격 유효성 검증 및 변환"""
        try:
            if isinstance(price_input, str):
                # 콤마, 원화 표시 등 제거
                price_str = re.sub(r'[,원￦$]', '', price_input)
                price = int(price_str)
            else:
                price = int(price_input)
                
            if price < 0:
                raise ValueError("가격은 0원 이상이어야 합니다.")
            if price > 10000000:
                raise ValueError("가격은 1천만원 이하여야 합니다.")
                
            return price
            
        except ValueError as e:
            logger.error(f"가격 검증 실패: {str(e)}")
            raise ValueError(f"올바른 가격을 입력해주세요: {str(e)}")
    
    def extract_features(self, features_input: str) -> str:
        """상품 특징 추출 및 정리"""
        if not features_input:
            return ""
            
        features = self.clean_text(features_input)
        
        # 특징이 너무 길면 자르기
        if len(features) > 500:
            features = features[:497] + "..."
            
        return features
    
    def validate_category(self, category: str) -> str:
        """카테고리 유효성 검증"""
        if not category:
            raise ValueError("카테고리는 필수 입력사항입니다.")
            
        category = self.clean_text(category)
        
        # 카테고리 길이 제한
        if len(category) > 50:
            category = category[:50]
            
        return category
    
    def validate_brand(self, brand: str) -> str:
        """브랜드 유효성 검증"""
        if not brand:
            raise ValueError("브랜드명은 필수 입력사항입니다.")
            
        brand = self.clean_text(brand)
        
        # 브랜드명 길이 제한
        if len(brand) > 50:
            brand = brand[:50]
            
        return brand
    
    def parse_form_data(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """폼 데이터 파싱 및 검증"""
        try:
            parsed_data = {}
            
            # 상품명
            if 'name' not in form_data or not form_data['name']:
                raise ValueError("상품명은 필수 입력사항입니다.")
            parsed_data['name'] = self.clean_text(form_data['name'])
            
            # 카테고리
            parsed_data['category'] = self.validate_category(form_data.get('category', ''))
            
            # 가격
            parsed_data['price'] = self.validate_price(form_data.get('price', 0))
            
            # 브랜드
            parsed_data['brand'] = self.validate_brand(form_data.get('brand', ''))
            
            # 특징
            parsed_data['features'] = self.extract_features(form_data.get('features', ''))
            
            # 이미지 경로 (선택사항)
            parsed_data['image_path'] = form_data.get('image_path')
            
            # 상품 링크 (선택사항)
            parsed_data['product_link'] = form_data.get('product_link')
            
            # Pydantic 스키마로 최종 검증
            validated_data = self.schema(**parsed_data)
            
            logger.info("폼 데이터 파싱 완료")
            return validated_data.dict()
            
        except Exception as e:
            logger.error(f"폼 데이터 파싱 실패: {str(e)}")
            raise ValueError(f"입력 데이터 검증 실패: {str(e)}")
    
    def create_product_summary(self, product_data: Dict[str, Any]) -> str:
        """상품 데이터 요약 생성"""
        try:
            summary = f"""
상품 정보 요약:
- 상품명: {product_data['name']}
- 카테고리: {product_data['category']}
- 브랜드: {product_data['brand']}
- 가격: {product_data['price']:,}원
- 특징: {product_data['features'][:100]}{'...' if len(product_data['features']) > 100 else ''}
            """.strip()
            
            if product_data.get('image_path'):
                summary += f"\n- 이미지: {product_data['image_path']}"
            
            if product_data.get('product_link'):
                summary += f"\n- 링크: {product_data['product_link']}"
                
            return summary
            
        except Exception as e:
            logger.error(f"상품 요약 생성 실패: {str(e)}")
            return "상품 요약 생성 중 오류가 발생했습니다."