from pydantic import BaseModel
from typing import List

class TextGenRequest(BaseModel):
    product_name: str
    category: str
    price: int
    brand: str
    features: List[str]
    image_path: str
    product_link: str