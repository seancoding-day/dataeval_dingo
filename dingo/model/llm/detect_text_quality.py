from dingo.model import Model
from dingo.model.llm.base_openai import BaseOpenAI


@Model.llm_register('detect_text_quality')
class DetectTextQuality(BaseOpenAI):
    ...
