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
                "content": cls.prompt.content + f"ground_truth:{gt_markdown}\n\nPred_content:{pred_json['content']}"
            }]
        return messages 

    @classmethod
    def process_response(cls, response: str) -> ModelRes:
        log.info(response)

        response = response.replace("```json", "")
        response = response.replace("```", "")

        types = []
        names = []
        reasons = []
        if response:
            try:
                result_data = json.loads(response)
                errors = result_data.get("errors", [])

                for error in errors:
                    error_category = error.get("error_category", "")
                    error_label = error.get("error_label", "")
                    bbox_type = error.get("bbox_type", "")
                    bbox_id = error.get("bbox_id", "")
                    if error_category and error_label :
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