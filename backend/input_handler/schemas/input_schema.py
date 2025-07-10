from pydantic import BaseModel, Field, validator
from typing import Optional,List
import re


class ProductInputSchema(BaseModel):
    """상품 입력 데이터 검증 스키마"""
    
    name: str = Field(..., min_length=1, max_length=200, description="상품명")
    category: str = Field(..., min_length=1, max_length=50, description="카테고리")
    price: int = Field(..., ge=0, le=10000000, description="가격 (0원 이상 1천만원 이하)")
    brand: str = Field(..., min_length=1, max_length=50, description="브랜드명")
    features: str = Field(..., min_length=1, max_length=500, description="상품 특징")
    image_path: List[str] = Field(..., min_items=1, description="이미지 경로 목록 (최소 1개)")
    product_link: Optional[str] = Field(None, description="상품 링크")
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('상품명은 필수 입력사항입니다.')
        return v.strip()
    
    @validator('category')
    def validate_category(cls, v):
        if not v.strip():
            raise ValueError('카테고리는 필수 입력사항입니다.')
        return v.strip()
    
    @validator('brand')
    def validate_brand(cls, v):
        if not v.strip():
            raise ValueError('브랜드명은 필수 입력사항입니다.')
        return v.strip()
    
    @validator('features')
    def validate_features(cls, v):
        if not v.strip():
            raise ValueError('상품 특징은 필수 입력사항입니다.')
        return v.strip()
    
    @validator('product_link')
    def validate_product_link(cls, v):
        if v and v.strip():
            # 기본적인 URL 형식 검증
            url_pattern = re.compile(
                r'^https?://'  # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
                r'localhost|'  # localhost...
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
                r'(?::\d+)?'  # optional port
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            
            if not url_pattern.match(v.strip()):
                raise ValueError('올바른 URL 형식이 아닙니다.')
            return v.strip()
        return v
    
    class Config:
        str_strip_whitespace = True
        validate_assignment = True