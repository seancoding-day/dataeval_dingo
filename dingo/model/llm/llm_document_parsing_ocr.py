import base64
import json
from typing import List

from dingo.io import Data
from dingo.model import Model
from dingo.model.llm.base_openai import BaseOpenAI
from dingo.model.modelres import ModelRes
from dingo.model.prompt.prompt_mineru_recognize import PromptMinerURecognizeQuality
from dingo.utils import log
from dingo.utils.exception import ConvertJsonError
from dingo.model.response.response_class import ResponseScoreReason


@Model.llm_register("LLMMinerURecognizeQuality")
class LLMMinerURecognizeQuality(BaseOpenAI):
    prompt = PromptMinerURecognizeQuality
    @classmethod
    def build_messages(cls, input_data: Data) -> List:
        gt_markdown = input_data.prompt
        pred_json = json.loads(input_data.content)[0]
        messages = [
            {
                "role": "user",
                "content": [
                    {"text": f"Markdown:\n{gt_markdown}"},
                    {"text": f"Pred:\n{pred_json['content']}; bbox_id: {pred_json['bbox_id']}; bbox_type: {pred_json['type']}"}
                ]
            }]
        return messages

    @classmethod
    def process_response(cls, response: str) -> ModelRes:
        log.info(response)

        response = response.replace("```json", "")
        response = response.replace("```", "")

        types = []
        names = []

        if response:
            try:
                result_data = json.loads(response)
                errors = result_data.get("errors", [])

                for error in errors:
                    error_category = error.get("error_category", "")
                    error_label = error.get("error_label", "")

                    if error_category and error_label:
                        types.append(error_category)
                        names.append(error_label)
            except json.JSONDecodeError as e:
                log.error(f"JSON解析错误: {e}")

        result = ModelRes()
        result.error_status = False
        result.type = types
        result.name = names
        result.reason = [response]

        return result