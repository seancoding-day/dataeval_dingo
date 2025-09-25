from typing import List

from dingo.io import Data
from dingo.model import Model
from dingo.model.llm.base_openai import BaseOpenAI
from dingo.model.modelres import ModelRes
from dingo.model.prompt.prompt_document_parsing import PromptDocumentParsingQuality
from dingo.utils import log


@Model.llm_register("VLMDocumentParsingQuality")
class VLMDocumentParsingQuality(BaseOpenAI):
    prompt = PromptDocumentParsingQuality

    @classmethod
    def build_messages(cls, input_data: Data) -> List:
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": cls.prompt.content},
                    {"type": "image_url", "image_url": {"url": input_data.img}},
                    {"type": "text", "text": f"Markdown:\n{input_data.content}"}
                ]
            }
        ]
        return messages

    @classmethod
    def process_response(cls, response: str) -> ModelRes:
        log.info(response)
        result = ModelRes()
        result.error_status = False
        result.type = "ocr"
        result.name = "document_parsing"
        result.reason = [response]

        return result
