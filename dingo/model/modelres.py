from typing import List

from pydantic import BaseModel


class ModelRes(BaseModel):
    error_status: bool = False
    type: str = "QUALITY_GOOD"
    name: str = "Data"
    reason: List[str] = []
