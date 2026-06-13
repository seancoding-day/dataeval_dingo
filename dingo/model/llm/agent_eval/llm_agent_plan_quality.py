"""
LLMAgentPlanQuality: Evaluates the quality of an agent's reasoning plan.

Assesses coherence, completeness, and feasibility of the agent's plan.
If no planning content is found in the trace, defaults to passing (score=1.0).
"""

import time
from typing import List

from dingo.io.input import Data, RequiredField
from dingo.io.output.eval_detail import EvalDetail, QualityLabel
from dingo.model import Model
from dingo.model.llm.agent_eval.base_llm_agent_eval import BaseLLMAgentEval
from dingo.utils import log
from dingo.utils.exception import ConvertJsonError, ExceedMaxTokens

try:
    from pydantic import ValidationError
except ImportError:
    ValidationError = Exception


@Model.llm_register("LLMAgentPlanQuality")
class LLMAgentPlanQuality(BaseLLMAgentEval):
    """
    Evaluates the quality of an agent's reasoning plan.

    Input:
        prompt  - The task objective or user request
        content - The agent trace or plan description

    If no planning content is detected in the trace, the evaluator
    returns score=1.0 (pass) because absence of planning may be
    acceptable for simple tasks.
    """

    eval_layer = "reasoning"
    input_data_type = "trace_summary"
    default_threshold = 0.6

    _required_fields = [RequiredField.PROMPT, RequiredField.CONTENT]

    prompt = """You are an expert evaluator assessing the quality of an AI agent's reasoning plan.

First, determine whether the trace contains any planning content (explicit steps, strategy, or reasoning about how to approach the task). If there is no planning content at all, set score to -1 as a sentinel value.

If planning content exists, evaluate it on three dimensions:
1. **Coherence** (1-5): Is the plan logically structured and internally consistent?
2. **Completeness** (1-5): Does the plan cover all necessary steps to achieve the goal?
3. **Feasibility** (1-5): Are the planned steps realistic and achievable?

Compute an overall **score** from 0 to 10 that is CONSISTENT with the three
dimensions above (e.g. all 5s → 9-10, all 3s → 5-6, all 1s → 0-2). Do not let
the score contradict the dimension ratings.

IMPORTANT: The "reason" field MUST be in the same language as the Task Objective. If the task objective is in Chinese, respond in Chinese. If in English, respond in English.

Return your evaluation as a JSON object with this exact schema:
{
  "coherence": <integer 1-5, or null if no plan>,
  "completeness": <integer 1-5, or null if no plan>,
  "feasibility": <integer 1-5, or null if no plan>,
  "score": <integer -1 if no plan found, otherwise 0-10>,
  "reason": "<explanation; if no plan, state that planning content was not found>"
}

Do not include any text outside the JSON object."""

    @classmethod
    def build_messages(cls, input_data: Data) -> List[dict]:
        """Build LLM messages for plan quality evaluation."""
        lang_hint = cls._detect_language_hint(
            str(input_data.prompt) + str(input_data.content)
        )
        user_content = f"""{cls.prompt}

## Task Objective
{input_data.prompt}

## Agent Trace / Plan
{input_data.content}

Evaluate the plan quality and return the JSON evaluation.{lang_hint}"""

        return [{"role": "user", "content": user_content}]

    @classmethod
    def eval(cls, input_data: Data) -> EvalDetail:
        """Override eval() to handle the no-planning special case."""
        if cls.client is None:
            cls.create_client()

        messages = cls.build_messages(input_data)

        attempts = 0
        except_msg = ""
        except_name = Exception.__class__.__name__
        while attempts < 3:
            try:
                response = cls.send_messages(messages)

                data = cls._parse_json_response(response)
                raw_score = data.get("score", 0)

                try:
                    raw_score = float(raw_score)
                except (TypeError, ValueError):
                    raw_score = 0.0

                result = EvalDetail(metric=cls.__name__)

                if raw_score < 0:
                    # Sentinel value: no planning content found, treat as pass
                    log.info(f"{cls.__name__}: No planning content found in trace, defaulting to pass")
                    result.status = False
                    result.label = [QualityLabel.QUALITY_GOOD]
                    result.score = 1.0
                    result.reason = [data.get("reason", "No planning content found; evaluation skipped.")]
                    return result

                normalized_score = max(0.0, min(1.0, raw_score / 10.0))
                threshold = cls._get_threshold()
                reason_text = data.get("reason", "")
                details = {k: v for k, v in data.items() if k not in ("score", "reason")}

                import json
                result.score = normalized_score
                if normalized_score >= threshold:
                    result.status = False
                    result.label = [QualityLabel.QUALITY_GOOD]
                else:
                    result.status = True
                    result.label = [f"AGENT_QUALITY.{cls.__name__}"]

                reason_parts = [reason_text] if reason_text else []
                if details:
                    reason_parts.append(json.dumps(details, ensure_ascii=False, default=str))
                result.reason = reason_parts if reason_parts else None

                return result

            except (ValidationError, ExceedMaxTokens, ConvertJsonError) as e:
                except_msg = str(e)
                except_name = e.__class__.__name__
                break
            except Exception as e:
                attempts += 1
                time.sleep(1)
                except_msg = str(e)
                except_name = e.__class__.__name__

        res = EvalDetail(metric=cls.__name__)
        res.status = True
        res.label = [f"QUALITY_BAD.{except_name}"]
        res.reason = [except_msg]
        return res
