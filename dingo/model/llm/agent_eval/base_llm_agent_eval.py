"""
Base class for all Agent evaluation metrics.

Provides standardized:
- 0~10 score → 0.0~1.0 normalization
- Configurable threshold via dynamic_config.model_extra
- Unified JSON response parsing with {"score": 0-10, "reason": "...", ...}
- Error fallback handling
- `eval_layer` and `input_data_type` declarations for orchestrator integration

Subclasses only need to define:
- `prompt`: the evaluation prompt template
- `build_messages()`: how to format input data into LLM messages
- Optionally override `process_response()` for custom parsing
"""

import json
from typing import Optional

from dingo.io.input import Data, RequiredField
from dingo.io.output.eval_detail import EvalDetail, QualityLabel
from dingo.model.llm.base_openai import BaseOpenAI
from dingo.utils import log
from dingo.utils.exception import ConvertJsonError


class BaseLLMAgentEval(BaseOpenAI):
    """Shared base class for all Agent evaluation metrics."""

    eval_layer: str = ""
    input_data_type: str = "trace_summary"
    default_threshold: float = 0.6

    @classmethod
    def _detect_language_hint(cls, text: str) -> str:
        """Detect if text contains CJK characters and return a language instruction."""
        if not text:
            return ""
        import re
        cjk_count = len(re.findall(r'[一-鿿㐀-䶿]', text[:500]))
        if cjk_count > 5:
            return '\n\n注意：请用中文回答 "reason" 字段。'
        return ""

    @classmethod
    def _get_threshold(cls) -> float:
        if cls.dynamic_config and cls.dynamic_config.model_extra:
            return float(cls.dynamic_config.model_extra.get(
                "threshold", cls.default_threshold
            ))
        return cls.default_threshold

    @classmethod
    def _strip_json_fences(cls, response: str) -> str:
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        return response.strip()

    @classmethod
    def _parse_json_response(cls, response: str) -> dict:
        cleaned = cls._strip_json_fences(response)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            raise ConvertJsonError(
                f"Failed to parse agent eval JSON: {cleaned[:500]}"
            )

    @classmethod
    def process_response(cls, response: str) -> EvalDetail:
        """Standardized response processing for agent evaluators.

        Expected LLM output: {"score": 0-10, "reason": "...", ...extra fields...}
        Score is normalized to 0.0~1.0 and compared against threshold.
        Extra fields are preserved in EvalDetail.reason as JSON.
        """
        log.info(response)
        data = cls._parse_json_response(response)

        raw_score = data.get("score", data.get("overall_score", 0))
        try:
            raw_score = float(raw_score)
        except (TypeError, ValueError):
            raw_score = 0.0

        normalized_score = max(0.0, min(1.0, raw_score / 10.0))
        threshold = cls._get_threshold()

        reason_text = data.get("reason", "")
        details = {k: v for k, v in data.items() if k not in ("score", "reason")}

        result = EvalDetail(metric=cls.__name__)
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
