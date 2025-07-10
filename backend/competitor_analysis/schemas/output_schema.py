from pydantic import BaseModel
from typing import List

class CompetitorOutput(BaseModel):
    differences: List[str]