import pytest
from dingo.model.rule.rule_common import RuleDocFormulaRepeat
from dingo.io import Data

class TestRuleDocFormulaRepeat:
  def test_rule_doc_formula_repeat(self):
        data = Data(data_id="1",content="we are a $$x^2 + y^2 + z^2 == z^\sqrt{4}\dots\dots\dots\dots\dots\dots\dots\dots\dots\dots\dots\dots\dots\dots\dots\dots\dots\dots\dots\dots\dots\dots\dots\dots\dots\dots$$ , we are a $$x^2 + y^2 = z^2$$ ")
        res = RuleDocFormulaRepeat.eval(data)
        assert res.error_status == True
        assert res.type == "QUALITY_BAD_SIMILARITY"
        assert res.name == "RuleDocFormulaRepeat"
        assert res.reason == ["Formula has too many consecutive repeated characters, total repeat length: 130, found 1 repeat patterns"]