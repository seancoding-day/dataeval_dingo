import json

from dingo.model import Model
from dingo.model.llm.base_openai import BaseOpenAI
from dingo.model.modelres import ModelRes
from dingo.model.prompt.prompt_long_video_qa import PromptLongVideoQa
from dingo.utils import log


@Model.llm_register("LLMLongVideoQa")
class LLMLongVideoQa(BaseOpenAI):
    prompt = PromptLongVideoQa

    @classmethod
    def process_response(cls, response: str) -> ModelRes:
        log.info(response)
        result = ModelRes()
        result.error_status = False
        result.type = "text"
        result.name = "qa_pairs"
        result.reason = [response]

        return result
