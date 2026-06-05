"""
LLMAgentTaskCompletion: Evaluates whether an Agent successfully completed its assigned task.

Compares the task objective (prompt) against the execution result summary (content)
and scores on goal achievement, accuracy, and completeness.
"""

from typing import List

from dingo.io.input import Data, RequiredField
from dingo.model import Model
from dingo.model.llm.agent_eval.base_llm_agent_eval import BaseLLMAgentEval


@Model.llm_register("LLMAgentTaskCompletion")
class LLMAgentTaskCompletion(BaseLLMAgentEval):
    """
    Evaluates whether the agent completed its assigned task.

    Input:
        prompt  - The task objective or user request
        content - The agent execution result summary

    Output score reflects the degree to which the agent achieved the goal,
    produced accurate results, and covered all required aspects.
    """

    eval_layer = "execution"
    input_data_type = "trace_summary"
    default_threshold = 0.6

    _required_fields = [RequiredField.PROMPT, RequiredField.CONTENT]

    prompt = """You are an expert evaluator assessing whether an AI agent successfully completed its assigned task.

Evaluate the agent's performance across three dimensions:
1. **Goal Achievement** (1-5): Did the agent accomplish the main objective?
2. **Accuracy** (1-5): Is the result correct and free of errors?
3. **Completeness** (1-5): Did the agent address all aspects of the task?

Then compute an overall score from 0 to 10 reflecting the combined quality.

Respond in the same language as the input content for the "reason" field.

Return your evaluation as a JSON object with this exact schema:
{
  "goal_achievement": <integer 1-5>,
  "accuracy": <integer 1-5>,
  "completeness": <integer 1-5>,
  "score": <integer 0-10>,
  "reason": "<concise explanation of the evaluation>"
}

Do not include any text outside the JSON object."""

    @classmethod
    def build_messages(cls, input_data: Data) -> List[dict]:
        """Build LLM messages for task completion evaluation."""
        lang_hint = cls._detect_language_hint(
            str(input_data.prompt) + str(input_data.content)
        )
        user_content = f"""{cls.prompt}

## Task Objective
{input_data.prompt}

## Agent Execution Result
{input_data.content}

Evaluate whether the agent completed its task and return the JSON evaluation.{lang_hint}"""

        return [{"role": "user", "content": user_content}]
