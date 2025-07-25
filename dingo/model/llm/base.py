from dingo.config.input_args import EvaluatorLLMArgs
from dingo.io import Data
from dingo.model.modelres import ModelRes
from dingo.model.prompt.base import BasePrompt


class BaseLLM:
    client = None

    prompt: str
    dynamic_config: EvaluatorLLMArgs

    @classmethod
    def set_prompt(cls, prompt: BasePrompt):
        raise NotImplementedError()

    @classmethod
    def eval(cls, input_data: Data) -> ModelRes:
        raise NotImplementedError()
