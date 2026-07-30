import inspect

import pytest

from dingo.config.input_args import EvaluatorRuleArgs
from dingo.io import Data
from dingo.io.output.eval_detail import EvalDetail, QualityLabel
from dingo.model.model import Model
from dingo.model.rule.guobiao import rule_tc609_quality
from dingo.model.rule.guobiao.rule_tc609_quality import (
    Rule_TC609_0201_FormatCompliance,
    Rule_TC609_0202_SafetyCompliance,
    Rule_TC609_0203_AnnotationCompliance,
    Rule_TC609_0204_StructuralCompleteness,
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


def test_tc609_rules_are_grouped_by_evaluation_object():
    expected_group_sizes = {
        "guobiao_doc": 4,
        "guobiao_data": 8,
        "guobiao_text": 7,
        "guobiao_image": 4,
        "guobiao_video": 6,
        "guobiao_audio": 6,
        "guobiao_model": 5,
    }

    for group_name, expected_size in expected_group_sizes.items():
        tc609_rules = [
            rule
            for rule in Model.rule_groups[group_name]
            if rule.__name__.startswith("Rule_TC609_")
        ]
        assert len(tc609_rules) == expected_size

    assert not any(
        rule.__name__.startswith("Rule_TC609_")
        for rule in Model.rule_groups.get("guobiao", [])
    )


def test_format_compliance_accepts_matching_record(monkeypatch):
    monkeypatch.setattr(
        Rule_TC609_0201_FormatCompliance,
        "dynamic_config",
        EvaluatorRuleArgs(
            field_schema={
                "data_id": "str",
                "content": "str",
                "type": "str",
                "dt": "str",
            }
        ),
    )

    result = Rule_TC609_0201_FormatCompliance.eval(
        Data(
            data_id="demo-001",
            content="example",
            type="medical",
            dt="2026-07-20 09:00:00",
        )
    )

    assert result.status is False
    assert result.label == [QualityLabel.QUALITY_GOOD]


def test_format_compliance_reports_missing_and_wrong_type(monkeypatch):
    monkeypatch.setattr(
        Rule_TC609_0201_FormatCompliance,
        "dynamic_config",
        EvaluatorRuleArgs(
            field_schema={
                "data_id": "str",
                "content": "str",
                "dt": "str",
            }
        ),
    )

    result = Rule_TC609_0201_FormatCompliance.eval(
        Data(data_id=1, content="example")
    )

    assert result.status is True
    assert result.label == [
        "QUALITY_BAD_TC609_0201.Rule_TC609_0201_FormatCompliance"
    ]
    assert result.reason == [
        "data_id: expected str, got int",
        "dt: required field is missing",
    ]


def test_format_compliance_reports_unexpected_fields(monkeypatch):
    monkeypatch.setattr(
        Rule_TC609_0201_FormatCompliance,
        "dynamic_config",
        EvaluatorRuleArgs(
            field_schema={"content": "str"},
            allow_extra=False,
        ),
    )

    result = Rule_TC609_0201_FormatCompliance.eval(
        Data(content="example", source="demo")
    )

    assert result.status is True
    assert result.reason == ["source: unexpected field"]


def test_format_compliance_allows_unexpected_fields_by_default(monkeypatch):
    monkeypatch.setattr(
        Rule_TC609_0201_FormatCompliance,
        "dynamic_config",
        EvaluatorRuleArgs(field_schema={"content": "str"}),
    )

    result = Rule_TC609_0201_FormatCompliance.eval(
        Data(content="example", source="demo")
    )

    assert result.status is False
    assert result.label == [QualityLabel.QUALITY_GOOD]


@pytest.mark.parametrize(
    "value, type_name",
    [
        (None, "Optional[str]"),
        ("text", "Optional[str]"),
        (None, "Optional[int]"),
        (1, "Optional[int]"),
        (None, "Optional[float]"),
        (1.5, "Optional[float]"),
        (None, "Optional[bool]"),
        (True, "Optional[bool]"),
        (None, "Optional[list]"),
        ([], "Optional[list]"),
        (None, "Optional[dict]"),
        ({}, "Optional[dict]"),
    ],
)
def test_format_compliance_accepts_optional_types(
    monkeypatch, value, type_name
):
    monkeypatch.setattr(
        Rule_TC609_0201_FormatCompliance,
        "dynamic_config",
        EvaluatorRuleArgs(field_schema={"value": type_name}),
    )

    result = Rule_TC609_0201_FormatCompliance.eval(Data(value=value))

    assert result.status is False
    assert result.label == [QualityLabel.QUALITY_GOOD]


def test_format_compliance_still_requires_optional_field(monkeypatch):
    monkeypatch.setattr(
        Rule_TC609_0201_FormatCompliance,
        "dynamic_config",
        EvaluatorRuleArgs(field_schema={"value": "Optional[str]"}),
    )

    result = Rule_TC609_0201_FormatCompliance.eval(Data())

    assert result.status is True
    assert result.reason == ["value: required field is missing"]

@pytest.mark.parametrize(
    "schema, error",
    [
        (None, "requires a non-empty dynamic_config.field_schema"),
        ({}, "requires a non-empty dynamic_config.field_schema"),
        ({"content": "string"}, "Unsupported schema type"),
        ({"content": {"type": "str"}}, "Unsupported schema type"),
        ({"content": "optional_string"}, "Unsupported schema type"),
        ({"content": "optional_str"}, "Unsupported schema type"),
        ({"content": "optional[str]"}, "Unsupported schema type"),
        ({"content": "typing.Optional[str]"}, "Unsupported schema type"),
        ({"content": "optianal[str]"}, "Unsupported schema type"),
    ],
)
def test_format_compliance_rejects_invalid_schema(monkeypatch, schema, error):
    monkeypatch.setattr(
        Rule_TC609_0201_FormatCompliance,
        "dynamic_config",
        EvaluatorRuleArgs(field_schema=schema),
    )

    with pytest.raises(ValueError, match=error):
        Rule_TC609_0201_FormatCompliance.eval(Data(content="example"))


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


def test_safety_compliance_passes_words_config_to_unsafe_rule(monkeypatch):
    class UnsafeWordsRule:
        dynamic_config = EvaluatorRuleArgs()
        _unsafe_words_list = None
        _unsafe_words_automaton = None

        @classmethod
        def eval(cls, input_data):
            if "unsafe" in cls.dynamic_config.key_list:
                return EvalDetail(
                    metric=cls.__name__,
                    status=True,
                    label=["QUALITY_BAD_SECURITY.UnsafeWordsRule"],
                    reason=["unsafe"],
                )
            return EvalDetail(
                metric=cls.__name__,
                label=[QualityLabel.QUALITY_GOOD],
            )

    class PassingRule:
        @classmethod
        def eval(cls, input_data):
            return EvalDetail(
                metric=cls.__name__,
                label=[QualityLabel.QUALITY_GOOD],
            )

    component_map = {
        Rule_TC609_0202_SafetyCompliance.component_rules[0]: UnsafeWordsRule,
        Rule_TC609_0202_SafetyCompliance.component_rules[1]: PassingRule,
        Rule_TC609_0202_SafetyCompliance.component_rules[2]: PassingRule,
    }
    monkeypatch.setattr(
        Rule_TC609_0202_SafetyCompliance,
        "_resolve_rule",
        classmethod(lambda cls, path: component_map[path]),
    )
    monkeypatch.setattr(
        Rule_TC609_0202_SafetyCompliance,
        "dynamic_config",
        EvaluatorRuleArgs(key_list=["unsafe"], refer_path=[]),
    )

    result = Rule_TC609_0202_SafetyCompliance.eval(
        Data(content="unsafe")
    )

    assert UnsafeWordsRule.dynamic_config.key_list == ["unsafe"]
    assert result.status is True
    assert result.reason == ["UnsafeWordsRule: unsafe"]


def test_annotation_compliance_accepts_allowed_content(monkeypatch):
    monkeypatch.setattr(
        Rule_TC609_0203_AnnotationCompliance,
        "dynamic_config",
        EvaluatorRuleArgs(key_list=["positive", "negative"]),
    )

    result = Rule_TC609_0203_AnnotationCompliance.eval(
        Data(content="positive")
    )

    assert result.status is False
    assert result.label == [QualityLabel.QUALITY_GOOD]


def test_annotation_compliance_rejects_unknown_content(monkeypatch):
    monkeypatch.setattr(
        Rule_TC609_0203_AnnotationCompliance,
        "dynamic_config",
        EvaluatorRuleArgs(key_list=["positive", "negative"]),
    )

    result = Rule_TC609_0203_AnnotationCompliance.eval(
        Data(content="neutral")
    )

    assert result.status is True
    assert result.label == [
        "QUALITY_BAD_TC609_0203.Rule_TC609_0203_AnnotationCompliance"
    ]
    assert result.reason == [
        "content: value 'neutral' is not in dynamic_config.key_list"
    ]


def test_annotation_compliance_requires_allowed_values(monkeypatch):
    monkeypatch.setattr(
        Rule_TC609_0203_AnnotationCompliance,
        "dynamic_config",
        EvaluatorRuleArgs(key_list=[]),
    )

    with pytest.raises(ValueError, match="non-empty dynamic_config.key_list"):
        Rule_TC609_0203_AnnotationCompliance.eval(Data(content="positive"))


def test_structural_completeness_accepts_present_values(monkeypatch):
    monkeypatch.setattr(
        Rule_TC609_0204_StructuralCompleteness,
        "dynamic_config",
        EvaluatorRuleArgs(
            key_list=["content", "labels", "metadata"],
            allow_none=False,
            allow_empty=False,
        ),
    )

    result = Rule_TC609_0204_StructuralCompleteness.eval(
        Data(content="example", labels=["valid"], metadata={"source": "demo"})
    )

    assert result.status is False
    assert result.label == [QualityLabel.QUALITY_GOOD]


def test_structural_completeness_reports_missing_none_and_empty(monkeypatch):
    monkeypatch.setattr(
        Rule_TC609_0204_StructuralCompleteness,
        "dynamic_config",
        EvaluatorRuleArgs(
            key_list=["missing", "nullable", "text", "items", "metadata"],
            allow_none=False,
            allow_empty=False,
        ),
    )

    result = Rule_TC609_0204_StructuralCompleteness.eval(
        Data(nullable=None, text="", items=[], metadata={})
    )

    assert result.status is True
    assert result.reason == [
        "missing: required field is missing",
        "nullable: None is not allowed",
        "text: empty value is not allowed",
        "items: empty value is not allowed",
        "metadata: empty value is not allowed",
    ]


def test_structural_completeness_allows_none_and_empty(monkeypatch):
    monkeypatch.setattr(
        Rule_TC609_0204_StructuralCompleteness,
        "dynamic_config",
        EvaluatorRuleArgs(
            key_list=["nullable", "text", "items", "metadata"],
            allow_none=True,
            allow_empty=True,
        ),
    )

    result = Rule_TC609_0204_StructuralCompleteness.eval(
        Data(nullable=None, text="", items=[], metadata={})
    )

    assert result.status is False
    assert result.label == [QualityLabel.QUALITY_GOOD]


def test_structural_completeness_requires_key_list(monkeypatch):
    monkeypatch.setattr(
        Rule_TC609_0204_StructuralCompleteness,
        "dynamic_config",
        EvaluatorRuleArgs(
            key_list=[],
            allow_none=False,
            allow_empty=False,
        ),
    )

    with pytest.raises(ValueError, match="non-empty dynamic_config.key_list"):
        Rule_TC609_0204_StructuralCompleteness.eval(Data(content="example"))


def test_uncovered_rule_is_explicit_placeholder():
    assert Rule_TC609_0301_ContentDiversity.group == ["guobiao_model"]
    with pytest.raises(NotImplementedError, match="placeholder"):
        Rule_TC609_0301_ContentDiversity.eval(
            Data(data_id="diversity", content="test")
        )
