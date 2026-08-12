"""
Agent-specific rule evaluators for deterministic quality checks.

These rules run without LLM calls, checking structural properties
of agent execution traces (loops, token budget, latency anomalies).
"""

import hashlib
import json
import statistics
from typing import Any, List, Optional

from dingo.config.input_args import EvaluatorRuleArgs
from dingo.io.input import Data, RequiredField
from dingo.io.output.eval_detail import EvalDetail, QualityLabel
from dingo.model.model import Model
from dingo.model.rule.base import BaseRule


def _load_trace_items(content: Any, primary_key: str, secondary_key: str) -> List[dict]:
    """Parse agent-trace ``content`` into a list of step / tool-call items.

    Accepts a JSON string, an already-parsed list, or a dict wrapper. For a dict
    payload, returns the first non-empty list among ``primary_key`` /
    ``secondary_key`` — using ``or`` (not ``dict.get`` defaults) so a
    present-but-null key falls through instead of yielding ``None``. Returns
    ``[]`` for free text, JSON null, or any non-list payload, so callers can
    iterate the result without guarding against ``None``.
    """
    try:
        data = json.loads(content) if isinstance(content, str) else content
    except (json.JSONDecodeError, TypeError):
        return []

    if isinstance(data, dict):
        items = data.get(primary_key) or data.get(secondary_key) or []
    elif isinstance(data, list):
        items = data
    else:
        return []

    return items if isinstance(items, list) else []


@Model.rule_register("AGENT_TRACE_QUALITY", ["agent_trace_basic"])
class RuleAgentTraceLoopDetection(BaseRule):
    """Detect repetitive tool call patterns indicating infinite loops.

    Input: content = JSON array of tool call objects with 'tool_name' field.
    Detection: n-gram analysis on tool call signatures.
    A loop is detected when the same subsequence of 2+ calls repeats 3 or more
    consecutive times.

    A signature combines the tool name with a fingerprint of its arguments, so
    a fan-out over one tool with different arguments (eight distinct search
    queries) is not mistaken for a stuck loop, while the same call issued over
    and over still is. Calls carrying no arguments compare by name alone.
    """

    # Trace-level evaluator: declares input_data_type / eval_layer so agent
    # orchestrators (e.g. dingo-saas) feed it the whole tool-call sequence as
    # JSON rather than running it per-span on plain text.
    eval_layer = "trajectory"
    input_data_type = "agent_trace_json"

    _ARGUMENT_KEYS = ("args", "arguments", "tool_input", "input")

    _required_fields = [RequiredField.CONTENT]

    @classmethod
    def eval(cls, input_data: Data) -> EvalDetail:
        result = EvalDetail(metric=cls.__name__)

        calls = cls._extract_calls(input_data.content)
        if len(calls) < 6:
            result.label = [QualityLabel.QUALITY_GOOD]
            return result

        loop_info = cls._detect_loops([signature for _, signature in calls])
        if loop_info:
            start = loop_info["position"]
            pattern = [name for name, _ in calls[start : start + len(loop_info["pattern"])]]
            result.status = True
            result.label = [f"{cls.metric_type}.{cls.__name__}"]
            result.reason = [
                f"Loop detected: pattern {pattern} "
                f"repeats {loop_info['count']} times at position {start}"
            ]
        else:
            result.label = [QualityLabel.QUALITY_GOOD]

        return result

    @classmethod
    def _extract_calls(cls, content: str) -> List[tuple]:
        """Return ``(tool_name, signature)`` per call, in trace order."""
        calls = []
        for item in _load_trace_items(content, "tool_calls", "steps"):
            if not isinstance(item, dict):
                continue
            name = item.get("tool_name") or item.get("name")
            if not name:
                continue
            calls.append((name, f"{name}|{cls._argument_fingerprint(item)}"))
        return calls

    @classmethod
    def _argument_fingerprint(cls, item: dict) -> str:
        """Stable fingerprint of a call's arguments; empty when it has none."""
        for key in cls._ARGUMENT_KEYS:
            value = item.get(key)
            if value in (None, "", {}, []):
                continue
            try:
                normalized = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
            except (TypeError, ValueError):
                normalized = str(value)
            return hashlib.sha256(normalized.encode()).hexdigest()[:12]
        return ""

    @classmethod
    def _detect_loops(
        cls, names: List[str], min_pattern_len: int = 2, min_repeats: int = 3
    ) -> Optional[dict]:
        for pattern_len in range(min_pattern_len, len(names) // min_repeats + 1):
            for start in range(len(names) - pattern_len * min_repeats + 1):
                pattern = names[start : start + pattern_len]
                count = 1
                pos = start + pattern_len
                while pos + pattern_len <= len(names):
                    if names[pos : pos + pattern_len] == pattern:
                        count += 1
                        pos += pattern_len
                    else:
                        break
                if count >= min_repeats:
                    return {
                        "pattern": pattern,
                        "count": count,
                        "position": start,
                    }
        return None


@Model.rule_register("AGENT_TRACE_QUALITY", ["agent_trace_basic"])
class RuleAgentTraceTokenBudget(BaseRule):
    """Check if total token usage exceeds a configurable budget.

    Input: content = JSON with 'total_tokens' field, or metadata with token info.
    Default budget: 500,000 tokens (configurable via dynamic_config.threshold).
    """

    # Trace-level evaluator (see RuleAgentTraceLoopDetection for rationale).
    eval_layer = "efficiency"
    input_data_type = "agent_trace_json"

    _required_fields = [RequiredField.CONTENT]
    # A real EvaluatorRuleArgs (not None) so set_config_rule's model_copy() in
    # the local/spark executors does not raise; the default also documents the
    # 500k budget and keeps it overridable via dynamic_config.threshold.
    dynamic_config = EvaluatorRuleArgs(threshold=500_000)

    @classmethod
    def eval(cls, input_data: Data) -> EvalDetail:
        result = EvalDetail(metric=cls.__name__)

        budget = 500_000
        if cls.dynamic_config and cls.dynamic_config.threshold is not None:
            try:
                budget = int(cls.dynamic_config.threshold)
            except (TypeError, ValueError):
                pass

        total_tokens = cls._extract_tokens(input_data)
        if total_tokens is None:
            result.label = [QualityLabel.QUALITY_GOOD]
            return result

        if total_tokens > budget:
            result.status = True
            result.label = [f"{cls.metric_type}.{cls.__name__}"]
            result.reason = [
                f"Token usage {total_tokens:,} exceeds budget {budget:,}"
            ]
            result.score = min(1.0, budget / total_tokens) if total_tokens > 0 else 0.0
        else:
            result.label = [QualityLabel.QUALITY_GOOD]
            result.score = 1.0

        return result

    @classmethod
    def _extract_tokens(cls, input_data: Data) -> Optional[int]:
        for source in [input_data.content, getattr(input_data, "metadata", None)]:
            if source is None:
                continue
            try:
                data = json.loads(source) if isinstance(source, str) else source
            except (json.JSONDecodeError, TypeError):
                continue
            if isinstance(data, dict):
                val = data.get("total_tokens")
                if val is not None:
                    try:
                        return int(val)
                    except (TypeError, ValueError):
                        pass
        return None


@Model.rule_register("AGENT_TRACE_QUALITY", ["agent_trace_basic"])
class RuleAgentTraceLatencyAnomaly(BaseRule):
    """Detect abnormally slow steps using statistical outlier analysis.

    Input: content = JSON array of step objects with 'duration' or 'duration_seconds' field.
    A step is flagged if its duration exceeds mean + 3*stddev.
    """

    # Trace-level evaluator (see RuleAgentTraceLoopDetection for rationale).
    eval_layer = "efficiency"
    input_data_type = "agent_trace_json"

    _required_fields = [RequiredField.CONTENT]

    @classmethod
    def eval(cls, input_data: Data) -> EvalDetail:
        result = EvalDetail(metric=cls.__name__)

        steps = cls._extract_steps(input_data.content)
        durations = [s["duration"] for s in steps if s["duration"] is not None and s["duration"] > 0]

        if len(durations) < 3:
            result.label = [QualityLabel.QUALITY_GOOD]
            return result

        mean = statistics.mean(durations)
        stdev = statistics.stdev(durations)
        threshold = mean + 3 * stdev

        anomalies = [
            s for s in steps
            if s["duration"] is not None and s["duration"] > threshold
        ]

        if anomalies:
            result.status = True
            result.label = [f"{cls.metric_type}.{cls.__name__}"]
            result.reason = [
                f"Step '{a['name']}' took {a['duration']:.2f}s "
                f"(threshold: {threshold:.2f}s, mean: {mean:.2f}s)"
                for a in anomalies[:5]
            ]
        else:
            result.label = [QualityLabel.QUALITY_GOOD]

        return result

    @classmethod
    def _extract_steps(cls, content: str) -> List[dict]:
        return [
            {
                "name": item.get("name", "unknown"),
                "duration": cls._safe_float(
                    item.get("duration", item.get("duration_seconds"))
                ),
            }
            for item in _load_trace_items(content, "steps", "tool_calls")
            if isinstance(item, dict)
        ]

    @classmethod
    def _safe_float(cls, val) -> Optional[float]:
        if val is None:
            return None
        try:
            return float(val)
        except (TypeError, ValueError):
            return None
