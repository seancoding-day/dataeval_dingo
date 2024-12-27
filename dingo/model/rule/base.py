from typing import List

from dingo.model.modelres import ModelRes
from dingo.io import MetaData
from dingo.config.config import DynamicRuleConfig


class BaseRule:
    metric_type: str  # This will be set by the decorator
    group: List[str]  # This will be set by the decorator
    dynamic_config:  DynamicRuleConfig

    @classmethod
    def eval(cls, input_data: MetaData) -> ModelRes:
        raise NotImplementedError()
