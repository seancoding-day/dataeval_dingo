"""Unit tests for the deterministic agent-trace rules in ``rule_agent.py``.

Covers the three trace-level rules and, importantly, the malformed-input edge
cases (JSON ``null`` values, non-dict items) that previously raised
``TypeError`` / ``AttributeError`` — plus the ``dynamic_config`` /
``input_data_type`` contract the dingo-saas orchestrator depends on.
"""

import json

import pytest

from dingo.config.input_args import EvaluatorRuleArgs
from dingo.io import Data
from dingo.io.output.eval_detail import QualityLabel
from dingo.model.model import Model
from dingo.model.rule.rule_agent import RuleAgentTraceLatencyAnomaly, RuleAgentTraceLoopDetection, RuleAgentTraceTokenBudget


def _data(content: str) -> Data:
    return Data(data_id="t", content=content)


class TestRuleAgentTraceLoopDetection:
    """Loop detection via n-gram repetition on the tool-name sequence."""

    def test_repeating_pattern_is_flagged(self):
        # [search, click] repeated 4 times → pattern len 2 repeats ≥ 3.
        content = json.dumps([{"tool_name": "search"}, {"tool_name": "click"}] * 4)
        res = RuleAgentTraceLoopDetection.eval(_data(content))
        assert res.status is True
        assert res.label == ["AGENT_TRACE_QUALITY.RuleAgentTraceLoopDetection"]
        assert res.reason is not None and "Loop detected" in res.reason[0]

    def test_dict_form_with_tool_calls_key(self):
        content = json.dumps(
            {"tool_calls": [{"tool_name": "a"}, {"tool_name": "b"}, {"tool_name": "c"}] * 3}
        )
        res = RuleAgentTraceLoopDetection.eval(_data(content))
        assert res.status is True

    def test_distinct_sequence_passes(self):
        content = json.dumps([{"tool_name": f"tool_{i}"} for i in range(8)])
        res = RuleAgentTraceLoopDetection.eval(_data(content))
        assert res.status is False
        assert res.label == [QualityLabel.QUALITY_GOOD]

    def test_same_tool_with_distinct_arguments_is_not_a_loop(self):
        # A research fan-out: one tool, eight different queries. Comparing tool
        # names alone reads this as ['WebSearch','WebSearch'] repeating 4 times.
        content = json.dumps(
            {
                "tool_calls": [
                    {"tool_name": "WebSearch", "args": {"query": f"topic {i}"}}
                    for i in range(8)
                ]
            }
        )
        res = RuleAgentTraceLoopDetection.eval(_data(content))
        assert res.status is False
        assert res.label == [QualityLabel.QUALITY_GOOD]

    def test_same_tool_with_identical_arguments_is_flagged(self):
        # Same tool, same arguments, over and over — a real stuck loop.
        content = json.dumps(
            {
                "tool_calls": [
                    {"tool_name": "WebSearch", "args": {"query": "same question"}}
                    for _ in range(6)
                ]
            }
        )
        res = RuleAgentTraceLoopDetection.eval(_data(content))
        assert res.status is True
        assert res.reason is not None and "Loop detected" in res.reason[0]

    def test_loop_reason_names_the_repeated_tool_not_its_signature(self):
        content = json.dumps(
            {
                "tool_calls": [
                    {"tool_name": "read_file", "args": {"path": "a.md"}}
                    for _ in range(6)
                ]
            }
        )
        res = RuleAgentTraceLoopDetection.eval(_data(content))
        assert res.status is True
        # The reported pattern stays human-readable: tool names, not the
        # internal argument fingerprint used for comparison.
        assert "read_file" in res.reason[0]
        assert "path" not in res.reason[0]

    def test_short_sequence_passes(self):
        # Fewer than 6 tool names → early pass, no analysis.
        content = json.dumps([{"tool_name": "a"}, {"tool_name": "b"}])
        res = RuleAgentTraceLoopDetection.eval(_data(content))
        assert res.status is False
        assert res.label == [QualityLabel.QUALITY_GOOD]

    def test_null_tool_calls_does_not_crash(self):
        # JSON null for a present key previously broke iteration (TypeError).
        res = RuleAgentTraceLoopDetection.eval(_data('{"tool_calls": null}'))
        assert res.status is False
        assert res.label == [QualityLabel.QUALITY_GOOD]

    def test_non_dict_items_do_not_crash(self):
        # Operator-precedence bug previously raised AttributeError on "a"/null.
        res = RuleAgentTraceLoopDetection.eval(_data('["a", null, {"name": "x"}]'))
        assert res.status is False
        assert res.label == [QualityLabel.QUALITY_GOOD]

    def test_non_json_text_passes(self):
        # Plain text content (not JSON) must be tolerated, not raise.
        res = RuleAgentTraceLoopDetection.eval(_data("just some free text"))
        assert res.status is False
        assert res.label == [QualityLabel.QUALITY_GOOD]


class TestRuleAgentTraceTokenBudget:
    """Token-budget rule with a default-but-overridable 500k threshold."""

    def test_default_threshold_is_500k(self):
        assert isinstance(RuleAgentTraceTokenBudget.dynamic_config, EvaluatorRuleArgs)
        assert RuleAgentTraceTokenBudget.dynamic_config.threshold == 500_000

    def test_under_budget_passes(self):
        res = RuleAgentTraceTokenBudget.eval(_data('{"total_tokens": 1000}'))
        assert res.status is False
        assert res.label == [QualityLabel.QUALITY_GOOD]
        assert res.score == 1.0

    def test_over_budget_is_flagged(self):
        res = RuleAgentTraceTokenBudget.eval(_data('{"total_tokens": 600000}'))
        assert res.status is True
        assert res.label == ["AGENT_TRACE_QUALITY.RuleAgentTraceTokenBudget"]
        assert res.reason is not None and "exceeds budget" in res.reason[0]

    def test_missing_tokens_passes(self):
        res = RuleAgentTraceTokenBudget.eval(_data('{"other_field": 1}'))
        assert res.status is False
        assert res.label == [QualityLabel.QUALITY_GOOD]

    def test_threshold_override_via_dynamic_config(self):
        original = RuleAgentTraceTokenBudget.dynamic_config.threshold
        try:
            RuleAgentTraceTokenBudget.dynamic_config.threshold = 100
            res = RuleAgentTraceTokenBudget.eval(_data('{"total_tokens": 200}'))
            assert res.status is True
        finally:
            RuleAgentTraceTokenBudget.dynamic_config.threshold = original


class TestRuleAgentTraceLatencyAnomaly:
    """Latency anomaly via mean + 3·stddev outlier detection."""

    def test_outlier_is_flagged(self):
        steps = [{"name": f"s{i}", "duration": 1.0} for i in range(15)]
        steps.append({"name": "slow", "duration": 40.0})
        res = RuleAgentTraceLatencyAnomaly.eval(_data(json.dumps({"steps": steps})))
        assert res.status is True
        assert res.label == ["AGENT_TRACE_QUALITY.RuleAgentTraceLatencyAnomaly"]
        assert res.reason is not None and "slow" in res.reason[0]

    def test_uniform_durations_pass(self):
        steps = [{"name": f"s{i}", "duration": 1.0} for i in range(5)]
        res = RuleAgentTraceLatencyAnomaly.eval(_data(json.dumps({"steps": steps})))
        assert res.status is False
        assert res.label == [QualityLabel.QUALITY_GOOD]

    def test_few_steps_pass(self):
        # Fewer than 3 valid durations → not enough data, early pass.
        steps = [{"name": "a", "duration": 1.0}, {"name": "b", "duration": 99.0}]
        res = RuleAgentTraceLatencyAnomaly.eval(_data(json.dumps({"steps": steps})))
        assert res.status is False
        assert res.label == [QualityLabel.QUALITY_GOOD]

    def test_duration_seconds_alias(self):
        steps = [{"name": f"s{i}", "duration_seconds": 1.0} for i in range(15)]
        steps.append({"name": "slow", "duration_seconds": 40.0})
        res = RuleAgentTraceLatencyAnomaly.eval(_data(json.dumps({"steps": steps})))
        assert res.status is True

    def test_null_steps_does_not_crash(self):
        res = RuleAgentTraceLatencyAnomaly.eval(_data('{"steps": null}'))
        assert res.status is False
        assert res.label == [QualityLabel.QUALITY_GOOD]


class TestRuleAgentRegistration:
    """The saas orchestrator keys off rule_name_map + the agent attributes."""

    @pytest.mark.parametrize(
        "name",
        [
            "RuleAgentTraceLoopDetection",
            "RuleAgentTraceTokenBudget",
            "RuleAgentTraceLatencyAnomaly",
        ],
    )
    def test_registered_in_name_map(self, name):
        assert name in Model.rule_name_map

    @pytest.mark.parametrize(
        "rule_cls",
        [
            RuleAgentTraceLoopDetection,
            RuleAgentTraceTokenBudget,
            RuleAgentTraceLatencyAnomaly,
        ],
    )
    def test_declares_agent_eval_attributes(self, rule_cls):
        # input_data_type + eval_layer are what dingo-saas' _is_agent_evaluator
        # checks to route these as trace-level (not span-level) evaluators.
        assert rule_cls.input_data_type == "agent_trace_json"
        assert rule_cls.eval_layer
