from typing import List, Optional

from dingo.config.input_args import EvaluatorLLMArgs
from dingo.io import Data
from dingo.io.output.eval_detail import EvalDetail, TokenUsage


class LLMCallResult:
    def __init__(self, content: str, usage: Optional[TokenUsage] = None):
        self.content = content
        self.usage = usage


def llm_response_content(response) -> str:
    if isinstance(response, LLMCallResult):
        return response.content
    return str(response)


class BaseLLM:
    client = None

    prompt: str | List = None
    dynamic_config: EvaluatorLLMArgs = EvaluatorLLMArgs()

    @classmethod
    def eval(cls, input_data: Data) -> EvalDetail:
        raise NotImplementedError()
