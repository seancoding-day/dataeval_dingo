import inspect

import pytest

from dingo.io import Data
from dingo.io.output.eval_detail import EvalDetail, QualityLabel
from dingo.model.model import Model
from dingo.model.rule.guobiao import rule_tc609_quality
from dingo.model.rule.guobiao.rule_tc609_quality import (
    Rule_TC609_0202_SafetyCompliance,
    Rule_TC609_0301_ContentDiversity,
)


def test_tc609_quality_defines_all_standard_metrics():
    rule_classes = {
        name: cls
        for name, cls in inspect.getmembers(
            rule_tc609_quality,
            lambda value: inspect.isclass(value)
            and value.__module__ == rule_tc609_quality.__name__,
        )
        if name.startswith("Rule_TC609_")
    }

    assert len(rule_classes) == 40
    assert all(name in Model.rule_name_map for name in rule_classes)

    expected_primary_codes = {
        "0101", "0102", "0103", "0104",
        "0201", "0202", "0203", "0204", "0205", "0206", "0207", "0208",
        "0301", "0302", "0303", "0304", "0305",
    }
    actual_codes = {
        name.split("_")[2]
        for name in rule_classes
        if len(name.split("_")[2]) == 4
    }
    assert actual_codes == expected_primary_codes


def test_composite_rule_maps_component_failure_to_tc609_label(monkeypatch):
    class PassingRule:
        @classmethod
        def eval(cls, input_data):
            return EvalDetail(
                metric=cls.__name__,
                label=[QualityLabel.QUALITY_GOOD],
            )

    class FailingRule:
        @classmethod
        def eval(cls, input_data):
            return EvalDetail(
                metric=cls.__name__,
                status=True,
                label=["QUALITY_BAD_TEST.FailingRule"],
                reason=["component failed"],
            )

    component_map = {
        Rule_TC609_0202_SafetyCompliance.component_rules[0]: PassingRule,
        Rule_TC609_0202_SafetyCompliance.component_rules[1]: FailingRule,
        Rule_TC609_0202_SafetyCompliance.component_rules[2]: PassingRule,
    }
    monkeypatch.setattr(
        Rule_TC609_0202_SafetyCompliance,
        "_resolve_rule",
        classmethod(lambda cls, path: component_map[path]),
    )

    result = Rule_TC609_0202_SafetyCompliance.eval(
        Data(data_id="safety", content="test")
    )

    assert result.status is True
    assert result.label == [
        "QUALITY_BAD_TC609_0202.Rule_TC609_0202_SafetyCompliance"
    ]
    assert result.reason == ["FailingRule: component failed"]


def test_uncovered_rule_is_explicit_placeholder():
    assert Rule_TC609_0301_ContentDiversity.group == ["guobiao_placeholder"]
    with pytest.raises(NotImplementedError, match="placeholder"):
        Rule_TC609_0301_ContentDiversity.eval(
            Data(data_id="diversity", content="test")
        )
