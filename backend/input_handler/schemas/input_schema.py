from pydantic import BaseModel, Field, validator
from typing import List, Optional
import re

class ProductInputSchema(BaseModel):
    """상품 입력 데이터 스키마"""
    
    name: str = Field(
        ..., 
        min_length=1, 
        max_length=100,
        description="상품명 (필수)"
    )
    
    category: str = Field(
        ..., 
        min_length=1, 
        max_length=50,
        description="카테고리 (필수)"
    )
    
    price: int = Field(
        ..., 
        ge=0, 
        le=10000000,
        description="가격 (필수, 0원 이상 1천만원 이하)"
    )
    
    brand: str = Field(
        ..., 
        min_length=1, 
        max_length=50,
        description="브랜드명 (필수)"
    )
    
    features: str = Field(
        ..., 
        min_length=1, 
        max_length=500,
        description="상품 특징 (필수)"
    )
    
    css_type: int = Field(
        ...,
        description="CSS 타입 (필수, 1 또는 2)"
    )
    
    image_path: Optional[List[str]] = Field(
        default=None,
        description="이미지 경로 리스트 (선택사항)"
    )
    
    @validator('name')
    def validate_name(cls, v):
        """상품명 검증"""
        v_str = str(v).strip()

        if not v or not v_str:
            raise ValueError('상품명은 필수 입력사항입니다.')
        
        # 특수문자 제한 (기본적인 문자, 숫자, 한글, 공백, 일부 특수문자만 허용)
        if not re.match(r'^[a-zA-Z0-9가-힣\s\-\(\)\[\]\/\.\,\!\?\:\;\'\"]+$', v_str):
            raise ValueError('상품명에 허용되지 않은 특수문자가 포함되어 있습니다.')
        
        return v_str
    
    @validator('category')
    def validate_category(cls, v):
        """카테고리 검증"""
        if not v or not v.strip():
            raise ValueError('카테고리는 필수 입력사항입니다.')
        
        return v.strip()
    
    @validator('brand')
    def validate_brand(cls, v):
        """브랜드명 검증"""
        if not v or not v.strip():
            raise ValueError('브랜드명은 필수 입력사항입니다.')
        
        return v.strip()
    
    @validator('features')
    def validate_features(cls, v):
        """상품 특징 검증"""
        if not v or not v.strip():
            raise ValueError('상품 특징은 필수 입력사항입니다.')
        
        return v.strip()
    
    @validator('css_type')
    def validate_css_type(cls, v):
        """CSS 타입 검증"""
        if v not in [1, 2]:
            raise ValueError('CSS 타입은 1 또는 2만 선택 가능합니다.')
        
        return v
    
    @validator('image_path')
    def validate_image_path(cls, v):
        """이미지 경로 검증 (선택사항)"""
        if v is None:
            return None
        
        if isinstance(v, str):
            # 단일 문자열인 경우 리스트로 변환
            v = [v]
        
        if not isinstance(v, list):
            raise ValueError('이미지 경로는 문자열 리스트여야 합니다.')
        
        # 빈 문자열이나 None 값 제거
        valid_paths = []
        for path in v:
            if path and isinstance(path, str) and path.strip():
                valid_paths.append(path.strip())
        
        return valid_paths if valid_paths else None
    
    class Config:
        """Pydantic 설정"""
        # JSON 스키마 생성 시 예시 포함
        schema_extra = {
            "example": {
                "name": "우일 여성 여름 인견 7부 블라우스",
                "category": "블라우스",
                "price": 29900,
                "brand": "우일",
                "features": "인견 소재, 우수한 흡수성과 통기성, 부드러운 촉감",
                "css_type": 1,
                "image_path": [
                    "backend/data/input/product_abc123.jpg",
                    "backend/data/input/product_def456.jpg"
                ]
            }
        }
        
        # 필드 순서 지정
        fields = {
            "name": {"title": "상품명"},
            "category": {"title": "카테고리"},
            "price": {"title": "가격"},
            "brand": {"title": "브랜드"},
            "features": {"title": "상품 특징"},
            "css_type": {"title": "CSS 타입"},
            "image_path": {"title": "이미지 경로"}
        }