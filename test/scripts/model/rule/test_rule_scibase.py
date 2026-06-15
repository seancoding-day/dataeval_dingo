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
