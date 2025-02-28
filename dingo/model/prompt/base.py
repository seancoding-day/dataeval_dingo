from typing import List


class BasePrompt:
    metric_type: str  # This will be set by the decorator
    group: List[str]  # This will be set by the decorator
    content: str
