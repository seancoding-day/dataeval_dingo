from typing import Dict, List, Optional, Union

from pydantic import BaseModel


class Data(BaseModel):
    """
    Data, output of converter.
    """

    data_id: str
    prompt: str = None
    content: str = None
    image: Optional[List] = None
    context: Optional[Union[str, List[str]]] = None  # Added for hallucination detection
    raw_data: Dict = {}
