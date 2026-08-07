from dingo.config.input_args import EvaluatorLLMArgs
from dingo.io.input import RequiredField
from dingo.model import Model
from dingo.model.llm.base_openai import BaseOpenAI
from dingo.model.llm.guobiao.llm_tc609_base import (
    serialize_data_content,
)
from dingo.model.rule.guobiao.rule_tc609_quality_base import (
    TC609_DATASET_TYPE_DESCRIPTIONS,
)


@Model.llm_register("LLM_TC609_0207_DataTypeConsistency")
class LLM_TC609_0207_DataTypeConsistency(BaseOpenAI):
    """Evaluate whether text content matches the configured dataset type."""

    _required_fields = [RequiredField.DATA_CONTENT]
    dynamic_config = EvaluatorLLMArgs(dataset_type="通识数据集")
    _metric_info = {
        "category": "National Standard LLM Assessment Metrics",
        "metric_name": "LLM_TC609_0207_DataTypeConsistency",
        "description": (
            "Uses an LLM to assess whether text content matches the configured "
            "TC609 dataset type."
        ),
        "paper_title": "TC609 high-quality dataset quality evaluation specification",
        "paper_url": "",
        "paper_authors": "SAC/TC609",
        "evaluation_results": "",
        "examples": "examples/guobiao/example_data.py",
    }
    prompt = """

"""

    @classmethod
    def get_request_extra_params(cls):
        extra_params = super().get_request_extra_params()
        extra_params.pop("dataset_type", None)
        return extra_params

    @classmethod
    def build_messages(cls, input_data):
        dataset_type = cls.dynamic_config.dataset_type
        if dataset_type not in TC609_DATASET_TYPE_DESCRIPTIONS:
            allowed = ", ".join(TC609_DATASET_TYPE_DESCRIPTIONS)
            raise ValueError(f"dataset_type must be one of: {allowed}")
        type_definitions = "\n".join(
            f"- {name}: {description}"
            for name, description in TC609_DATASET_TYPE_DESCRIPTIONS.items()
        )
        content = serialize_data_content(input_data.data_content)
        request = (
            f"# 目标数据集类型\n{dataset_type}\n\n"
            f"# 数据集类型定义\n{type_definitions}\n\n"
            f"# 待评估数据\n{content}"
        )
        return [{"role": "user", "content": cls.prompt + request}]
