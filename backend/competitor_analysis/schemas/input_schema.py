from pydantic import BaseModel
from typing import Optional

class ProductInput(BaseModel):
    name: str
    category: str
    price: int
    brand: str
    features: str
    image_path: str
    product_link: Optional[str] = None
    css_type: int