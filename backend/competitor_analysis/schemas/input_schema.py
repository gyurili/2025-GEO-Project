from pydantic import BaseModel
from typing import Optional

class ProductInput(BaseModel):
    name: str
    category: str
    price: int
    brand: str
    features: str
    image_path: str
    css_type: int