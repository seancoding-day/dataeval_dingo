from typing import List, Union

from pydantic import BaseModel


class ModelRes(BaseModel):
    error_status: bool = False
    type: str = 'QUALITY_GOOD'
    name: str = 'Data'
    reason: List[str] = []
