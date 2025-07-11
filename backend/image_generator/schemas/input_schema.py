from pydantic import BaseModel
from typing import List

class ImageGenRequest(BaseModel):
    name: str
    category: str
    price: int
    features: str
    image_path: str