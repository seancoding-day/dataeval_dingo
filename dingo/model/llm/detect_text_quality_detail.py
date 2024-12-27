import json

from dingo.model import Model
from dingo.model.llm.base_openai import BaseOpenAI
from dingo.model.modelres import ModelRes
from dingo.model.response.response_class import ResponseScoreTypeNameReason
from dingo.utils import log
from dingo.utils.exception import ConvertJsonError


@Model.llm_register('detect_text_quality_detail')
class DetectTextQualityDetail(BaseOpenAI):
    @classmethod
    def process_response(cls, response: str) -> ModelRes:
        log.info(response)

        if response.startswith('```json'):
            response = response[7:]
        if response.startswith('```'):
            response = response[3:]
        if response.endswith('```'):
            response = response[:-3]
        try:
            response_json = json.loads(response)
        except json.JSONDecodeError:
            raise ConvertJsonError(f'Convert to JSON format failed: {response}')

        response_model = ResponseScoreTypeNameReason(**response_json)

        result = ModelRes()
        # error_status
        if response_model.score == 1:
            result.reason = [response_model.reason]
        else:
            result.error_status = True
            result.type = response_model.type
            result.name = response_model.name
            result.reason = [response_model.reason]

        return result
