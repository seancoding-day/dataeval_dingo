import pytest
from dingo.io import Data
from dingo.config.input_args import EvaluatorRuleArgs
from dingo.io.output.eval_detail import QualityLabel
from dingo.model.rule.rule_guobiao import (
    RuleDataTypeConsistency,
    RuleDocApplicationCompleteness,
    RuleDocBasicInfoCompleteness,
    RuleDocConstructionProcessCompleteness,
    RuleDocContentFeatureCompleteness,
    RuleTextPerplexity,
)
from dingo.model.rule.rule_common import (
    RuleDocFormulaRepeat,
    RulePIIDetection,
    RuleUnsafeWords,
)


class TestRuleDocFormulaRepeat:
    def test_rule_doc_formula_repeat(self):
        data = Data(data_id="1",content="we are a $$x^2 + y^2 + z^2 == z^\\sqrt{4}\\dots\\dots\\dots\\dots\\dots\\dots\\dots\\dots\\dots\\dots\\dots\\dots\\dots\\dots\\dots\\dots\\dots\\dots\\dots\\dots\\dots\\dots\\dots\\dots\\dots\\dots$$ , we are a $$x^2 + y^2 = z^2$$ ")
        res = RuleDocFormulaRepeat.eval(data)
        # print(res)
        assert res.status is True
        assert res.label == ["QUALITY_BAD_SIMILARITY.RuleDocFormulaRepeat"]
        assert res.metric == "RuleDocFormulaRepeat"
        assert res.reason == ["Formula has too many consecutive repeated characters, total repeat length: 130, found 1 repeat patterns"]

    def test_rule_unsafe_words(self):
        data = Data(data_id="", prompt="", content="java is good\n \n \n \n hello \n \n but python is better")
        r = RuleUnsafeWords
        r.dynamic_config.key_list = ['av', 'b', 'java']
        tmp = r.eval(data)
        assert tmp.status is True
        assert 'av' not in tmp.reason
        assert 'b' not in tmp.reason
        assert 'java' in tmp.reason


class TestRuleTextPerplexity:
    @staticmethod
    def _mock_model(monkeypatch, perplexity):
        monkeypatch.setattr(
            RuleTextPerplexity,
            "_check_dependencies",
            classmethod(lambda cls: None),
        )
        monkeypatch.setattr(
            RuleTextPerplexity,
            "_get_model_components",
            classmethod(lambda cls, model_name: (object(), object())),
        )
        monkeypatch.setattr(
            RuleTextPerplexity,
            "_calculate_perplexity",
            classmethod(
                lambda cls, content, tokenizer, model, stride: perplexity
            ),
        )

    def test_high_perplexity_is_bad(self, monkeypatch):
        self._mock_model(monkeypatch, 125.5)
        monkeypatch.setattr(
            RuleTextPerplexity,
            "dynamic_config",
            EvaluatorRuleArgs(
                threshold=100.0,
                model="test-model",
                stride=64,
            ),
        )

        res = RuleTextPerplexity.eval(
            Data(data_id="ppl-high", content="A valid piece of text.")
        )

        assert res.status is True
        assert res.label == ["QUALITY_BAD_FLUENCY.RuleTextPerplexity"]
        assert "125.5000" in res.reason[0]
        assert "test-model" in res.reason[0]

    def test_low_perplexity_is_good(self, monkeypatch):
        self._mock_model(monkeypatch, 42.25)
        monkeypatch.setattr(
            RuleTextPerplexity,
            "dynamic_config",
            EvaluatorRuleArgs(
                threshold=100.0,
                model="test-model",
                stride=64,
            ),
        )

        res = RuleTextPerplexity.eval(
            Data(data_id="ppl-low", content="A fluent piece of text.")
        )

        assert res.status is False
        assert res.label == [QualityLabel.QUALITY_GOOD]
        assert "42.2500" in res.reason[0]

    def test_empty_content_is_bad_without_loading_model(self, monkeypatch):
        monkeypatch.setattr(
            RuleTextPerplexity,
            "_check_dependencies",
            classmethod(lambda cls: None),
        )

        def fail_if_called(cls, model_name):
            raise AssertionError("model should not be loaded for empty content")

        monkeypatch.setattr(
            RuleTextPerplexity,
            "_get_model_components",
            classmethod(fail_if_called),
        )

        res = RuleTextPerplexity.eval(Data(data_id="ppl-empty", content="  "))

        assert res.status is True
        assert res.label == ["QUALITY_BAD_FLUENCY.RuleTextPerplexity"]
        assert "empty content" in res.reason[0]

    def test_missing_dependencies_raise_clear_error(self, monkeypatch):
        monkeypatch.setattr(
            "dingo.model.rule.rule_common.importlib.util.find_spec",
            lambda package: None if package == "transformers" else object(),
        )

        try:
            RuleTextPerplexity.eval(
                Data(data_id="ppl-dependency", content="A piece of text.")
            )
        except ImportError as exc:
            assert "transformers" in str(exc)
            assert "dingo-python[hhem]" in str(exc)
        else:
            raise AssertionError("expected ImportError for missing transformers")


class TestRuleDataTypeConsistency:
    @staticmethod
    def _mock_match_score(monkeypatch, score):
        monkeypatch.setattr(
            RuleDataTypeConsistency,
            "_calculate_match_score",
            classmethod(lambda cls, *args: score),
        )
        monkeypatch.setattr(
            RuleDataTypeConsistency,
            "dynamic_config",
            EvaluatorRuleArgs(threshold=0.6, model="test-model", device=-1),
        )

    def test_content_matching_declared_type_is_good(self, monkeypatch):
        self._mock_match_score(monkeypatch, 0.85)
        result = RuleDataTypeConsistency.eval(
            Data(data_id="type-match", type="medical", content="Clinical treatment")
        )

        assert result.status is False
        assert result.score == 0.85
        assert result.label == [QualityLabel.QUALITY_GOOD]

    def test_content_not_matching_declared_type_is_bad(self, monkeypatch):
        self._mock_match_score(monkeypatch, 0.25)
        result = RuleDataTypeConsistency.eval(
            Data(data_id="type-mismatch", type="medical", content="Stock prices")
        )

        assert result.status is True
        assert result.score == 0.25
        assert result.label == [
            "QUALITY_BAD_TYPE_CONSISTENCY.RuleDataTypeConsistency"
        ]

    def test_missing_type_is_bad(self):
        result = RuleDataTypeConsistency.eval(
            Data(data_id="type-missing", content="Ordinary text")
        )

        assert result.status is True
        assert "missing or empty" in result.reason[0]


class TestRulePIIDetection:
    """PII 检测规则测试"""

    def test_no_pii_content(self):
        """测试不包含 PII 的正常内容"""
        data = Data(data_id="1", content="这是一段普通的文本，没有任何敏感信息。")
        res = RulePIIDetection.eval(data)
        assert res.status is False
        assert res.label == [QualityLabel.QUALITY_GOOD]
        assert res.metric == "RulePIIDetection"

    def test_chinese_id_card(self):
        """测试中国身份证号检测"""
        data = Data(data_id="2", content="我的身份证号是 110101199001011234。")
        res = RulePIIDetection.eval(data)
        assert res.status is True
        assert res.label == ["QUALITY_BAD_SECURITY.RulePIIDetection"]
        assert res.metric == "RulePIIDetection"
        assert res.reason is not None
        assert len(res.reason) > 0
        # 验证已脱敏
        assert "110101********1234" in str(res.reason) or "***" in str(res.reason)

    def test_chinese_phone(self):
        """测试中国手机号检测"""
        data = Data(data_id="3", content="请联系我：13812345678")
        res = RulePIIDetection.eval(data)
        assert res.status is True
        assert res.label == ["QUALITY_BAD_SECURITY.RulePIIDetection"]
        assert "138****5678" in str(res.reason)

    def test_email_address(self):
        """测试电子邮件检测"""
        data = Data(data_id="4", content="我的邮箱是 user@example.com")
        res = RulePIIDetection.eval(data)
        assert res.status is True
        assert res.label == ["QUALITY_BAD_SECURITY.RulePIIDetection"]
        assert "@example.com" in str(res.reason)

    def test_credit_card_valid(self):
        """测试有效信用卡号检测（通过 Luhn 验证）- 16位"""
        # 4532148803436464 是一个通过 Luhn 验证的测试卡号
        data = Data(data_id="5", content="信用卡号：4532 1488 0343 6464")
        res = RulePIIDetection.eval(data)
        assert res.status is True
        assert res.label == ["QUALITY_BAD_SECURITY.RulePIIDetection"]
        assert "6464" in str(res.reason)

    def test_credit_card_15_digits(self):
        """测试15位信用卡号检测（Amex）"""
        # 378282246310005 是一个有效的15位 Amex 测试卡号
        data = Data(data_id="5b", content="Card: 378282246310005")
        res = RulePIIDetection.eval(data)
        assert res.status is True
        assert res.label == ["QUALITY_BAD_SECURITY.RulePIIDetection"]
        assert "0005" in str(res.reason)

    def test_credit_card_invalid_luhn(self):
        """测试无效信用卡号（不通过 Luhn 验证）"""
        data = Data(data_id="6", content="卡号：1234 5678 9012 3456")
        res = RulePIIDetection.eval(data)
        # 不通过 Luhn 验证，应该不被检测为 PII
        assert res.status is False
        assert res.label == [QualityLabel.QUALITY_GOOD]

    def test_us_ssn(self):
        """测试美国社会安全号检测"""
        data = Data(data_id="7", content="SSN: 123-45-6789")
        res = RulePIIDetection.eval(data)
        assert res.status is True
        assert res.label == ["QUALITY_BAD_SECURITY.RulePIIDetection"]

    def test_chinese_passport(self):
        """测试中国护照号检测"""
        data = Data(data_id="8", content="护照号码：E12345678")
        res = RulePIIDetection.eval(data)
        assert res.status is True
        assert res.label == ["QUALITY_BAD_SECURITY.RulePIIDetection"]

    def test_ip_address_valid(self):
        """测试有效 IP 地址检测"""
        data = Data(data_id="9", content="服务器 IP：192.168.1.100")
        res = RulePIIDetection.eval(data)
        assert res.status is True
        assert res.label == ["QUALITY_BAD_SECURITY.RulePIIDetection"]
        # IP 是低风险，应该在 reason 中
        assert "192" in str(res.reason)

    def test_ip_address_invalid(self):
        """测试无效 IP 地址（不应检测）"""
        data = Data(data_id="10", content="IP: 300.400.500.600")
        res = RulePIIDetection.eval(data)
        # 无效 IP 不应被检测
        assert res.status is False
        assert res.label == [QualityLabel.QUALITY_GOOD]

    def test_multiple_pii_types(self):
        """测试混合多种 PII 类型"""
        data = Data(
            data_id="11",
            content="张三，身份证 110101199001011234，手机 13812345678，邮箱 zhangsan@qq.com"
        )
        res = RulePIIDetection.eval(data)
        assert res.status is True
        assert res.label == ["QUALITY_BAD_SECURITY.RulePIIDetection"]
        # 应该检测到多种 PII
        assert res.reason is not None
        assert len(res.reason) > 0
        # 验证包含高风险和中风险
        reason_str = str(res.reason)
        assert "High Risk" in reason_str or "Medium Risk" in reason_str

    def test_pii_masking_id_card(self):
        """测试身份证号脱敏"""
        masked = RulePIIDetection._mask_pii("110101199001011234", "cn_id_card")
        assert masked == "110101********1234"
        assert "199001011234" not in masked  # 确保中间部分被隐藏

    def test_pii_masking_phone(self):
        """测试手机号脱敏"""
        masked = RulePIIDetection._mask_pii("13812345678", "cn_phone")
        assert masked == "138****5678"
        assert "1234" not in masked  # 确保中间部分被隐藏

    def test_pii_masking_email(self):
        """测试邮箱脱敏"""
        masked = RulePIIDetection._mask_pii("user@example.com", "email")
        assert "@example.com" in masked
        assert "user" not in masked or masked.startswith("u")

    def test_pii_masking_credit_card(self):
        """测试信用卡号脱敏"""
        masked = RulePIIDetection._mask_pii("4532148803436464", "credit_card")
        assert masked.endswith("6464")
        assert "4532148803436464" not in masked  # 确保不显示完整卡号

    def test_luhn_validation_valid(self):
        """测试 Luhn 算法验证 - 有效卡号"""
        assert RulePIIDetection._validate_luhn("4532148803436464") is True

    def test_luhn_validation_invalid(self):
        """测试 Luhn 算法验证 - 无效卡号"""
        assert RulePIIDetection._validate_luhn("1234567890123456") is False

    def test_luhn_validation_with_spaces(self):
        """测试 Luhn 算法验证 - 带空格的卡号"""
        assert RulePIIDetection._validate_luhn("4532 1488 0343 6464") is True

    def test_ip_validation_valid(self):
        """测试 IP 地址验证 - 有效 IP"""
        assert RulePIIDetection._validate_ip("192.168.1.1") is True
        assert RulePIIDetection._validate_ip("10.0.0.1") is True

    def test_ip_validation_invalid(self):
        """测试 IP 地址验证 - 无效 IP"""
        assert RulePIIDetection._validate_ip("300.400.500.600") is False
        assert RulePIIDetection._validate_ip("256.1.1.1") is False
        assert RulePIIDetection._validate_ip("1.1.1") is False

    def test_severity_levels(self):
        """测试不同严重等级的 PII"""
        # 高风险：身份证
        data_high = Data(data_id="12", content="身份证：110101199001011234")
        res_high = RulePIIDetection.eval(data_high)
        assert "High Risk" in str(res_high.reason)

        # 中风险：手机号
        data_medium = Data(data_id="13", content="手机：13812345678")
        res_medium = RulePIIDetection.eval(data_medium)
        assert "Medium Risk" in str(res_medium.reason)

        # 低风险：IP
        data_low = Data(data_id="14", content="IP：192.168.1.1")
        res_low = RulePIIDetection.eval(data_low)
        assert "Low Risk" in str(res_low.reason)


class TestRuleDatasetDocCompleteness:
    def test_basic_info_completeness_good(self):
        content = (
            "本数据集说明包含数据集规模与样本数量，给出格式规范和文件结构，"
            "提供访问渠道，并说明技术支持联系方式。"
        )
        res = RuleDocBasicInfoCompleteness.eval(
            Data(data_id="doc-basic-good", content=content)
        )
        assert res.status is False
        assert res.label == [QualityLabel.QUALITY_GOOD]
        assert res.score == 1.0

    def test_basic_info_completeness_bad(self):
        content = "仅提到样本数量和文件结构，未说明访问渠道。"
        res = RuleDocBasicInfoCompleteness.eval(
            Data(data_id="doc-basic-bad", content=content)
        )
        assert res.status is True
        assert res.label == [
            "QUALITY_BAD_COMPLETENESS.RuleDocBasicInfoCompleteness"
        ]
        assert res.score < 0.8

    def test_content_feature_completeness_good(self):
        content = (
            "文档包含模态类型、数据分布情况、标签类别统计、样本示例以及局限性说明。"
        )
        res = RuleDocContentFeatureCompleteness.eval(
            Data(data_id="doc-content-good", content=content)
        )
        assert res.status is False
        assert res.label == [QualityLabel.QUALITY_GOOD]
        assert res.score == 1.0

    def test_construction_process_completeness_good(self):
        content = (
            "建设过程包括数据来源、采集方法、加工处理流程、标注规范和版本控制记录。"
        )
        res = RuleDocConstructionProcessCompleteness.eval(
            Data(data_id="doc-process-good", content=content)
        )
        assert res.status is False
        assert res.label == [QualityLabel.QUALITY_GOOD]
        assert res.score == 1.0

    def test_application_completeness_good(self):
        content = (
            "应用说明提供使用许可、目标应用场景、评估方法、基准测试结果与典型应用案例。"
        )
        res = RuleDocApplicationCompleteness.eval(
            Data(data_id="doc-application-good", content=content)
        )
        assert res.status is False
        assert res.label == [QualityLabel.QUALITY_GOOD]
        assert res.score == 1.0

    def test_empty_content_is_bad(self):
        res = RuleDocApplicationCompleteness.eval(
            Data(data_id="doc-empty", content="   ")
        )
        assert res.status is True
        assert res.label == [
            "QUALITY_BAD_COMPLETENESS.RuleDocApplicationCompleteness"
        ]
        assert "missing or empty" in res.reason[0]
