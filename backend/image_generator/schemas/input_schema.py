from pydantic import BaseModel
from typing import List

class ImageGenRequest(BaseModel):
    product_name: str
    category: str
    features: List[str]
    image_path: str
    layout_hint: str  # "top-left", "bottom-center", etc.