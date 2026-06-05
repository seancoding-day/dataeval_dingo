"""
LLMAgentTraceConclusion — synthesizes all evaluation results into a structured diagnosis.

Called after all other evaluators complete for a trace. Takes the full set of
evaluation scores as input and produces:
- Overall severity (critical / warning / good)
- Root cause analysis
- Actionable recommendations
- A single aggregate score (0-10)

This is NOT an evaluator in the traditional sense — it's a diagnostic synthesizer.
"""

from typing import List

from dingo.io.input import Data, RequiredField
from dingo.io.output.eval_detail import EvalDetail, QualityLabel
from dingo.model.llm.agent_eval.base_llm_agent_eval import BaseLLMAgentEval
from dingo.model.model import Model

CONCLUSION_PROMPT = """You are an AI agent quality analyst. Given the evaluation results from multiple evaluators that assessed an agent's execution trace, synthesize a comprehensive diagnosis.

## Task Objective
{objective}

## Evaluation Results
{eval_results}

## Trace Summary
{trace_summary}

## Instructions
Analyze all evaluation scores and produce a structured JSON diagnosis:

1. **severity**: "critical" (any score < 0.3), "warning" (any score < 0.6), or "good" (all scores >= 0.6)
2. **root_causes**: List the primary reasons for any failures or low scores
3. **recommendations**: Actionable suggestions to improve the agent's performance
4. **highlights**: What the agent did well
5. **score**: Overall quality score from 0 to 10, weighing task completion most heavily

Output STRICTLY as JSON:
```json
{{
    "severity": "critical|warning|good",
    "root_causes": ["cause 1", "cause 2"],
    "recommendations": ["rec 1", "rec 2"],
    "highlights": ["highlight 1"],
    "score": 0-10,
    "summary": "One-paragraph overall assessment in the same language as the task objective"
}}
```"""


@Model.llm_register("LLMAgentTraceConclusion")
class LLMAgentTraceConclusion(BaseLLMAgentEval):
    """Synthesize evaluation results into a structured trace-level diagnosis."""

    eval_layer = "conclusion"
    input_data_type = "eval_synthesis"
    default_threshold = 0.5
    _required_fields = [RequiredField.PROMPT, RequiredField.CONTENT]

    @classmethod
    def build_messages(cls, input_data: Data) -> List:
        objective = getattr(input_data, "prompt", "") or "Agent trace"
        eval_results = getattr(input_data, "content", "") or "{}"
        trace_summary = getattr(input_data, "context", "") or ""
        lang_hint = cls._detect_language_hint(
            str(input_data.prompt) + str(input_data.content)
        )

        prompt_text = CONCLUSION_PROMPT.format(
            objective=objective,
            eval_results=eval_results,
            trace_summary=trace_summary,
        ) + lang_hint
        return [{"role": "user", "content": prompt_text}]

    @classmethod
    def process_response(cls, response: str) -> EvalDetail:
        from dingo.utils import log
        log.info(response)

        data = cls._parse_json_response(response)

        raw_score = data.get("score", 5)
        try:
            raw_score = float(raw_score)
        except (TypeError, ValueError):
            raw_score = 5.0

        normalized_score = max(0.0, min(1.0, raw_score / 10.0))
        severity = data.get("severity", "warning")

        result = EvalDetail(metric=cls.__name__)
        result.score = normalized_score

        if severity == "good":
            result.status = False
            result.label = [QualityLabel.QUALITY_GOOD]
        elif severity == "critical":
            result.status = True
            result.label = ["AGENT_QUALITY.TraceConclusion.CRITICAL"]
        else:
            result.status = True
            result.label = ["AGENT_QUALITY.TraceConclusion.WARNING"]

        import json
        result.reason = [
            data.get("summary", ""),
            json.dumps({
                "severity": severity,
                "root_causes": data.get("root_causes", []),
                "recommendations": data.get("recommendations", []),
                "highlights": data.get("highlights", []),
            }, ensure_ascii=False),
        ]

        return result
