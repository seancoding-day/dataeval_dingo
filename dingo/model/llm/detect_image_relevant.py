from typing import List

from dingo.io.input import MetaData
from dingo.model import Model
from dingo.model.llm.base_openai import BaseOpenAI


@Model.llm_register('detect_image_relevant')
class DetectImageRelevant(BaseOpenAI):

    @classmethod
    def build_messages(cls, input_data: MetaData) -> List:
        messages = [
            {"role": "user",
             "content": [{'type': 'text', 'text': cls.prompt.content},
                         {'type': 'image_url', 'image_url': {'url': input_data.prompt}},
                         {'type': 'image_url', 'image_url': {'url': input_data.content}}]
             }
        ]
        return messages
