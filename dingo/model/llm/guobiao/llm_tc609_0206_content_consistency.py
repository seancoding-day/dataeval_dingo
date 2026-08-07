from dingo.io.input import RequiredField
from dingo.model import Model
from dingo.model.llm.base_openai import BaseOpenAI
from dingo.model.llm.guobiao.llm_tc609_base import (
    serialize_data_content,
)


@Model.llm_register("LLM_TC609_0206_ContentConsistency")
class LLM_TC609_0206_ContentConsistency(BaseOpenAI):
    """Evaluate semantic and factual consistency among text content items."""

    _required_fields = [RequiredField.DATA_CONTENT]
    _metric_info = {
        "category": "National Standard LLM Assessment Metrics",
        "metric_name": "LLM_TC609_0206_ContentConsistency",
        "description": (
            "Uses an LLM to assess semantic and factual consistency among text "
            "items in data_content."
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
    def build_messages(cls, input_data):
        content = serialize_data_content(input_data.data_content)
        return [{"role": "user", "content": cls.prompt + content}]
