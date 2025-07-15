from pydantic import BaseModel

class TextGenRequest(BaseModel):
    name: str
    category: str
    price: int
    brand: str
    features: str
    image_path: str
    css_type: int