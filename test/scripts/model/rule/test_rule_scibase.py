import json
from pathlib import Path

from dingo.io.input import Data
from dingo.model.rule.scibase.rule_quanliang import RuleQuanliangFieldValidation


class TestRuleQuanliangFieldValidation:
    def test_rule_quanliang_cases_from_jsonl(self):
        data_path = (
            Path(__file__).parent.parent.parent.parent / "data" / "scibase" / "rule_quanliang_cases.jsonl"
        )
        assert data_path.exists(), f"missing test data file: {data_path}"

        original_key_list = RuleQuanliangFieldValidation.dynamic_config.key_list
        try:
            with data_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    row = json.loads(line)
                    model = RuleQuanliangFieldValidation()
                    model.dynamic_config = model.dynamic_config.model_copy(deep=True)
                    model.dynamic_config.key_list = row["key_list"]
                    result = model.eval(Data(**row["input"]))

                    assert result.metric == "RuleQuanliangFieldValidation"
                    assert result.status is row["expected_status"], row["case"]
                    assert result.label == row["expected_labels"], row["case"]

                    expected_reasons = row["expected_reasons"]
                    if expected_reasons:
                        assert result.reason == expected_reasons, row["case"]
                    else:
                        assert result.reason in (None, []), row["case"]
        finally:
            RuleQuanliangFieldValidation.dynamic_config.key_list = original_key_list

    def test_title_and_abstract_return_hierarchical_multi_labels(self):
        value = (
            "<i>layout</i> <mml:math>x</mml:math> <!--note--> <![CDATA[x]]> "
            "&amp; &#39; &#x0D; \u200b \ufffd \x08 [!sub]"
        )
        model = RuleQuanliangFieldValidation()
        model.dynamic_config = model.dynamic_config.model_copy(deep=True)
        model.dynamic_config.key_list = ["title", "abstract"]

        result = model.eval(Data(title=value, abstract=value))

        expected_error_labels = [
            "html_tag_layout",
            "html_tag_math",
            "html_tag_xml_comment",
            "html_tag_cdata",
            "html_entity_named",
            "html_entity_decimal",
            "html_entity_hex",
            "special_char_invisible",
            "special_char_replacement",
            "special_char_control",
            "special_char_markup",
        ]
        assert result.status is True
        assert result.label == [
            f"{field}.{error_label}"
            for field in ("title", "abstract")
            for error_label in expected_error_labels
        ]

    def test_high_false_positive_patterns_are_not_enabled(self):
        model = RuleQuanliangFieldValidation()
        model.dynamic_config = model.dynamic_config.model_copy(deep=True)
        model.dynamic_config.key_list = ["title", "abstract"]

        result = model.eval(
            Data(
                title="Comparison of <candidate> values with amp and gt proteins",
                abstract="A legitimate [sic!] quotation with lt as an abbreviation.",
            )
        )

        assert result.status is False
        assert result.label == ["QUALITY_GOOD"]

    def test_reference_title_propagates_multiple_error_labels(self):
        model = RuleQuanliangFieldValidation()
        model.dynamic_config = model.dynamic_config.model_copy(deep=True)
        model.dynamic_config.key_list = ["references"]

        result = model.eval(
            Data(
                references=[
                    {
                        "id_type": "other",
                        "id": "source-1",
                        "title": "<i>formatted</i> &amp;",
                    }
                ]
            )
        )

        assert result.label == [
            "references.title_html_tag_layout",
            "references.title_html_entity_named",
        ]

    def test_text_issue_reason_contains_all_distinct_matches(self):
        model = RuleQuanliangFieldValidation()
        model.dynamic_config = model.dynamic_config.model_copy(deep=True)
        model.dynamic_config.key_list = ["title"]

        result = model.eval(Data(title="<i>A</i> <i>B</i> &amp; &amp; \u200b"))

        assert result.reason == [
            'title: contains HTML layout tag: ["<i>", "</i>"]',
            'title: contains named HTML entity: ["&amp;"]',
            'title: contains invisible unicode character: ["\\u200b"]',
        ]
