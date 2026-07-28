import importlib.util
import math
from datetime import datetime, timezone

from dingo.config.input_args import EvaluatorRuleArgs
from dingo.io.input import Data, RequiredField
from dingo.io.output.eval_detail import EvalDetail, QualityLabel
from dingo.model.model import Model
from dingo.model.rule.guobiao.rule_tc609_quality_base import (
    _tc609_metric_info,
    Rule_TC609_Composite,
    Rule_TC609_01_DocCompleteness,
    _TC609PlaceholderBase,
)
from dingo.model.rule.base import BaseRule


@Model.rule_register("QUALITY_BAD_TC609_0101", ["guobiao"])
class Rule_TC609_0101_DocBasicInfoCompleteness(Rule_TC609_01_DocCompleteness):
    """0101: Basic information completeness in dataset documentation."""

    _metric_info = {
        "category": "National Standard Data Quality Metrics",
        "quality_dimension": "COMPLETENESS",
        "metric_name": "Rule_TC609_0101_DocBasicInfoCompleteness",
        "description": (
            "Checks whether dataset documentation covers basic information "
            "aspects such as scale, format, structure, access, and support"
        ),
        "paper_title": "High-quality dataset quality evaluation specification",
        "paper_url": "",
        "paper_authors": "SAC/TC609",
        "evaluation_results": "",
        "standard_code": "0101",
        "coverage": "covered",
    }
    _default_dimension_name = "Basic information"
    _default_aspect_keywords = {
        "dataset_scale": ["数据集规模", "样本数量", "样本规模", "数据量", "存储体积", "数据体量"],
        "format_specification": ["格式规范", "数据格式", "文件格式", "编码格式", "字段格式"],
        "file_structure": ["文件结构", "目录结构", "文件组织", "数据组织结构"],
        "access_channel": ["访问渠道", "获取方式", "下载方式", "访问方式", "获取渠道"],
        "technical_support": ["技术支持", "支持方式", "联系方式", "问题反馈", "维护方式"],
    }
    dynamic_config = EvaluatorRuleArgs(
        threshold=0.8,
        dimension_name=_default_dimension_name,
        aspect_keywords=_default_aspect_keywords,
    )


@Model.rule_register("QUALITY_BAD_TC609_0102", ["guobiao"])
class Rule_TC609_0102_DocContentFeatureCompleteness(Rule_TC609_01_DocCompleteness):
    """0102: Content feature completeness in dataset documentation."""

    _metric_info = {
        "category": "National Standard Data Quality Metrics",
        "quality_dimension": "COMPLETENESS",
        "metric_name": "Rule_TC609_0102_DocContentFeatureCompleteness",
        "description": (
            "Checks whether dataset documentation covers content-feature aspects "
            "such as modality, distribution, labels, examples, and limitations"
        ),
        "paper_title": "High-quality dataset quality evaluation specification",
        "paper_url": "",
        "paper_authors": "SAC/TC609",
        "evaluation_results": "",
        "standard_code": "0102",
        "coverage": "covered",
    }
    _default_dimension_name = "Content feature"
    _default_aspect_keywords = {
        "modality_type": ["模态类型", "数据模态", "文本图像", "多模态", "音频视频"],
        "data_distribution": ["数据分布", "分布情况", "分布特征", "类别分布", "统计分布"],
        "label_statistics": ["标签类别统计", "标签统计", "类别统计", "标签分布"],
        "sample_examples": ["样本示例", "样例", "示例数据", "样本展示", "案例样本"],
        "limitations": ["局限性说明", "局限性", "限制说明", "不足", "已知问题"],
    }
    dynamic_config = EvaluatorRuleArgs(
        threshold=0.8,
        dimension_name=_default_dimension_name,
        aspect_keywords=_default_aspect_keywords,
    )


@Model.rule_register("QUALITY_BAD_TC609_0103", ["guobiao"])
class Rule_TC609_0103_DocConstructionProcessCompleteness(
    Rule_TC609_01_DocCompleteness
):
    """0103: Construction-process completeness in dataset documentation."""

    _metric_info = {
        "category": "National Standard Data Quality Metrics",
        "quality_dimension": "COMPLETENESS",
        "metric_name": "Rule_TC609_0103_DocConstructionProcessCompleteness",
        "description": (
            "Checks whether dataset documentation covers construction-process "
            "aspects such as data source, collection, processing, annotation, "
            "and version control"
        ),
        "paper_title": "High-quality dataset quality evaluation specification",
        "paper_url": "",
        "paper_authors": "SAC/TC609",
        "evaluation_results": "",
        "standard_code": "0103",
        "coverage": "covered",
    }
    _default_dimension_name = "Construction process"
    _default_aspect_keywords = {
        "data_source": ["数据来源", "来源说明", "数据源", "来源渠道"],
        "collection_method": ["采集方法", "采集方式", "收集方法", "获取流程"],
        "processing_pipeline": ["加工处理流程", "处理流程", "清洗流程", "预处理流程"],
        "annotation_specification": ["标注规范", "标注标准", "标注规则", "标注说明"],
        "version_control": ["版本控制", "版本记录", "变更记录", "版本管理"],
    }
    dynamic_config = EvaluatorRuleArgs(
        threshold=0.8,
        dimension_name=_default_dimension_name,
        aspect_keywords=_default_aspect_keywords,
    )


@Model.rule_register("QUALITY_BAD_TC609_0104", ["guobiao"])
class Rule_TC609_0104_DocApplicationCompleteness(Rule_TC609_01_DocCompleteness):
    """0104: Application-description completeness in dataset documentation."""

    _metric_info = {
        "category": "National Standard Data Quality Metrics",
        "quality_dimension": "COMPLETENESS",
        "metric_name": "Rule_TC609_0104_DocApplicationCompleteness",
        "description": (
            "Checks whether dataset documentation covers application aspects "
            "such as license, scenarios, evaluation method, benchmark, and cases"
        ),
        "paper_title": "High-quality dataset quality evaluation specification",
        "paper_url": "",
        "paper_authors": "SAC/TC609",
        "evaluation_results": "",
        "standard_code": "0104",
        "coverage": "covered",
    }
    _default_dimension_name = "Application description"
    _default_aspect_keywords = {
        "license": ["使用许可", "许可协议", "授权协议", "license", "开源协议"],
        "target_scenarios": ["目标应用场景", "应用场景", "使用场景", "场景说明"],
        "evaluation_method": ["评估方法", "评价方法", "评测方法", "评估方案"],
        "benchmark_results": ["基准测试结果", "基准结果", "benchmark", "基线结果"],
        "typical_cases": ["典型应用案例", "应用案例", "典型案例", "落地案例"],
    }
    dynamic_config = EvaluatorRuleArgs(
        threshold=0.8,
        dimension_name=_default_dimension_name,
        aspect_keywords=_default_aspect_keywords,
    )


@Model.rule_register("QUALITY_BAD_TC609_0201", ["guobiao"])
class Rule_TC609_0201_FormatCompliance(Rule_TC609_Composite):
    """0201: Format compliance, partially covered by existing format rules."""

    component_rules = (
        "dingo.model.rule.rule_common.RuleNlpDataFormat",
        "dingo.model.rule.rule_common.RuleSftDataFormat",
        "dingo.model.rule.rule_common.RuleImageDataFormat",
        "dingo.model.rule.rule_common.RuleAudioDataFormat",
        "dingo.model.rule.rule_common.RuleVedioDataFormat",
    )
    composition_mode = "any"
    _metric_info = _tc609_metric_info(
        "0201",
        "Rule_TC609_0201_FormatCompliance",
        "Combines existing NLP, SFT, image, audio, and video format rules.",
        "partial",
    )


@Model.rule_register("QUALITY_BAD_TC609_0202", ["guobiao"])
class Rule_TC609_0202_SafetyCompliance(Rule_TC609_Composite):
    """0202: Safety compliance, composed from safety and PII rules."""

    component_rules = (
        "dingo.model.rule.rule_common.RuleUnsafeWords",
        "dingo.model.rule.rule_common.RulePIIDetection",
        "dingo.model.rule.rule_common.RuleIDCard",
    )
    _required_fields = [RequiredField.CONTENT]
    _metric_info = _tc609_metric_info(
        "0202",
        "Rule_TC609_0202_SafetyCompliance",
        "Combines unsafe-word, PII, and identity-card detection.",
        "partial",
    )


@Model.rule_register("QUALITY_BAD_TC609_0203", ["guobiao"])
class Rule_TC609_0203_AnnotationCompliance(Rule_TC609_Composite):
    """0203: Annotation compliance, partially covered by image label rules."""

    component_rules = (
        "dingo.model.rule.rule_image.RuleImageLabelOverlap",
        "dingo.model.rule.rule_image.RuleImageLabelVisualization",
    )
    _required_fields = [RequiredField.IMAGE]
    _metric_info = _tc609_metric_info(
        "0203",
        "Rule_TC609_0203_AnnotationCompliance",
        "Combines image-label overlap and visualization checks.",
        "partial",
    )


@Model.rule_register("QUALITY_BAD_TC609_0204", ["guobiao"])
class Rule_TC609_0204_StructuralCompleteness(Rule_TC609_Composite):
    """0204: Structural completeness, composed from content checks."""

    component_rules = (
        "dingo.model.rule.rule_common.RuleContentNull",
        "dingo.model.rule.rule_common.RuleContentShort",
    )
    _required_fields = [RequiredField.CONTENT]
    _metric_info = _tc609_metric_info(
        "0204",
        "Rule_TC609_0204_StructuralCompleteness",
        "Combines null-content and short-content checks.",
        "partial",
    )


@Model.rule_register("QUALITY_BAD_TC609_0205", ["guobiao"])
class Rule_TC609_0205_ContentAuthenticity(Rule_TC609_Composite):
    """0205: Content authenticity, partially covered by HHEM."""

    component_rules = (
        "dingo.model.rule.rule_hallucination_hhem.RuleHallucinationHHEM",
    )
    _metric_info = _tc609_metric_info(
        "0205",
        "Rule_TC609_0205_ContentAuthenticity",
        "Uses HHEM consistency checking as partial evidence of authenticity.",
        "partial",
    )


@Model.rule_register("QUALITY_BAD_TC609_0206", ["guobiao"])
class Rule_TC609_0206_ContentConsistency(Rule_TC609_Composite):
    """0206: Content consistency, composed from dict and image-text checks."""

    component_rules = (
        "dingo.model.rule.rule_common.RuleDictConsistency",
        "dingo.model.rule.rule_image.RuleImageTextSimilarity",
    )
    composition_mode = "any"
    _metric_info = _tc609_metric_info(
        "0206",
        "Rule_TC609_0206_ContentConsistency",
        "Combines structured-field and image-text consistency checks.",
        "partial",
    )


@Model.rule_register("QUALITY_BAD_TC609_0207", ["guobiao"])
class Rule_TC609_0207_DataTypeConsistency(BaseRule):
    """Check whether content belongs to the type declared in ``input_data.type``.

    A local zero-shot classifier evaluates the hypothesis ``这段文本属于{type}类型``.
    The declared type may be any non-empty string, such as ``医疗`` or ``金融``.
    """

    _metric_info = {
        "category": "National Standard Data Quality Metrics",
        "quality_dimension": "TYPE_CONSISTENCY",
        "metric_name": "Rule_TC609_0207_DataTypeConsistency",
        "description": (
            "Uses a local zero-shot classifier to check whether content belongs "
            "to the type declared in the record"
        ),
        "paper_title": "High-quality dataset quality evaluation specification",
        "paper_url": "",
        "paper_authors": "SAC/TC609",
        "evaluation_results": "",
        "standard_code": "0207",
        "coverage": "partial",
    }

    _required_fields = [RequiredField.CONTENT, RequiredField.TYPE]
    dynamic_config = EvaluatorRuleArgs(
        threshold=0.5,
        model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli",
        device=-1,
    )

    _model_name = None
    _model_device = None
    _classifier = None

    @classmethod
    def _get_classifier(cls, model_name, device):
        if (
            cls._model_name == model_name
            and cls._model_device == device
            and cls._classifier is not None
        ):
            return cls._classifier

        required_packages = ("torch", "transformers")
        missing_packages = [
            package
            for package in required_packages
            if importlib.util.find_spec(package) is None
        ]
        if missing_packages:
            raise ImportError(
                "Rule_TC609_0207_DataTypeConsistency requires optional packages: "
                f"{', '.join(missing_packages)}. "
                'Install them with: pip install "dingo-python[hhem]"'
            )

        from transformers import pipeline

        cls._classifier = pipeline(
            "zero-shot-classification",
            model=model_name,
            device=device,
        )
        cls._model_name = model_name
        cls._model_device = device
        return cls._classifier

    @classmethod
    def _calculate_match_score(
        cls, content, declared_type, model_name, device
    ):
        classifier = cls._get_classifier(model_name, device)
        result = classifier(
            content,
            candidate_labels=[declared_type],
            hypothesis_template="这段文本属于{}类型。",
            multi_label=True,
            truncation=True,
        )
        labels = result.get("labels", [])
        scores = result.get("scores", [])
        if not labels or not scores or labels[0] != declared_type:
            raise RuntimeError("Zero-shot classifier returned an invalid result")
        score = float(scores[0])
        if not math.isfinite(score) or not 0.0 <= score <= 1.0:
            raise RuntimeError(
                f"Zero-shot classifier returned an invalid score: {score}"
            )
        return score

    @classmethod
    def eval(cls, input_data: Data) -> EvalDetail:
        res = EvalDetail(metric=cls.__name__)
        declared_type = getattr(input_data, "type", None)
        content = getattr(input_data, "content", None)

        if not isinstance(declared_type, str) or not declared_type.strip():
            res.status = True
            res.label = [f"{cls.metric_type}.{cls.__name__}"]
            res.reason = ["Data type is missing or empty"]
            return res

        if not isinstance(content, str) or not content.strip():
            res.status = True
            res.label = [f"{cls.metric_type}.{cls.__name__}"]
            res.reason = ["Content is missing or empty"]
            return res

        threshold = cls.dynamic_config.threshold
        if threshold is None or not 0 < threshold <= 1:
            raise ValueError(
                "Rule_TC609_0207_DataTypeConsistency dynamic_config.threshold must be in (0, 1]"
            )

        model_name = cls.dynamic_config.model
        device = cls.dynamic_config.device
        score = cls._calculate_match_score(
            content, declared_type, model_name, device
        )
        res.score = score

        if score >= threshold:
            res.label = [QualityLabel.QUALITY_GOOD]
            res.reason = [
                f"Content matches declared type {declared_type} "
                f"(score: {score:.4f}, threshold: {threshold:.4f})"
            ]
        else:
            res.status = True
            res.label = [f"{cls.metric_type}.{cls.__name__}"]
            res.reason = [
                f"Content does not match declared type {declared_type} "
                f"(score: {score:.4f}, threshold: {threshold:.4f})"
            ]
        return res


@Model.rule_register("QUALITY_BAD_TC609_0208", ["guobiao"])
class Rule_TC609_0208_ContentCleanliness(Rule_TC609_Composite):
    """0208: Content cleanliness, composed from available cleaning rules."""

    component_rules = (
        "dingo.model.rule.rule_common.RuleAbnormalChar",
        "dingo.model.rule.rule_common.RuleAbnormalHtml",
        "dingo.model.rule.rule_common.RuleDocRepeat",
        "dingo.model.rule.rule_common.RuleContentNull",
        "dingo.model.rule.rule_common.RuleWatermark",
    )
    _required_fields = [RequiredField.CONTENT]
    _metric_info = _tc609_metric_info(
        "0208",
        "Rule_TC609_0208_ContentCleanliness",
        "Combines available text cleanliness checks; modality coverage is partial.",
        "partial",
    )


@Model.rule_register("QUALITY_BAD_TC609_02080101", ["pretrain", "guobiao"])
class Rule_TC609_02080101_TextPerplexity(BaseRule):
    """Check whether text perplexity exceeds the configured threshold."""

    _metric_info = {
        "category": "National Standard Data Quality Metrics",
        "quality_dimension": "FLUENCY",
        "metric_name": "Rule_TC609_02080101_TextPerplexity",
        "description": (
            "Calculates text perplexity with a causal language model and "
            "flags text whose PPL exceeds the configured threshold"
        ),
        "paper_title": "High-quality dataset quality evaluation specification",
        "paper_url": "",
        "paper_authors": "SAC/TC609",
        "evaluation_results": "",
        "standard_code": "02080101",
        "coverage": "covered",
    }

    _required_fields = [RequiredField.CONTENT]
    dynamic_config = EvaluatorRuleArgs(
        threshold=100.0,
        model="uer/gpt2-chinese-cluecorpussmall",
        stride=512,
    )

    _model_name = None
    _tokenizer = None
    _model = None

    @classmethod
    def _check_dependencies(cls):
        required_packages = ("torch", "transformers")
        missing_packages = [
            package
            for package in required_packages
            if importlib.util.find_spec(package) is None
        ]
        if missing_packages:
            raise ImportError(
                "Rule_TC609_02080101_TextPerplexity requires optional packages: "
                f"{', '.join(missing_packages)}. "
                'Install them with: pip install "dingo-python[hhem]"'
            )

    @classmethod
    def _get_model_components(cls, model_name):
        if (
            cls._model_name == model_name
            and cls._tokenizer is not None
            and cls._model is not None
        ):
            return cls._tokenizer, cls._model

        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise ImportError(
                "Rule_TC609_02080101_TextPerplexity requires transformers and torch. "
                'Install them with: pip install "dingo-python[hhem]"'
            ) from exc

        cls._tokenizer = AutoTokenizer.from_pretrained(model_name)
        cls._model = AutoModelForCausalLM.from_pretrained(model_name)
        cls._model.eval()
        cls._model_name = model_name
        return cls._tokenizer, cls._model

    @classmethod
    def _calculate_perplexity(cls, content, tokenizer, model, stride):
        try:
            import torch
        except ImportError as exc:
            raise ImportError(
                "Rule_TC609_02080101_TextPerplexity requires transformers and torch. "
                'Install them with: pip install "dingo-python[hhem]"'
            ) from exc

        encodings = tokenizer(content, return_tensors="pt")
        input_ids = encodings["input_ids"]
        sequence_length = input_ids.size(1)
        if sequence_length < 2:
            raise ValueError(
                "Rule_TC609_02080101_TextPerplexity requires at least two model tokens"
            )

        model_config = getattr(model, "config", None)
        max_length = getattr(model_config, "n_positions", None)
        if max_length is None:
            max_length = getattr(model_config, "max_position_embeddings", 1024)
        max_length = int(max_length)
        stride = max(1, min(int(stride), max_length))

        try:
            device = next(model.parameters()).device
        except StopIteration:
            device = torch.device("cpu")

        total_negative_log_likelihood = 0.0
        total_loss_tokens = 0
        previous_end = 0

        for begin in range(0, sequence_length, stride):
            end = min(begin + max_length, sequence_length)
            target_length = end - previous_end
            window = input_ids[:, begin:end].to(device)
            targets = window.clone()
            targets[:, :-target_length] = -100

            with torch.no_grad():
                output = model(window, labels=targets)

            loss_tokens = int((targets[:, 1:] != -100).sum().item())
            if loss_tokens > 0:
                total_negative_log_likelihood += output.loss.item() * loss_tokens
                total_loss_tokens += loss_tokens

            previous_end = end
            if end == sequence_length:
                break

        if total_loss_tokens == 0:
            raise ValueError(
                "Rule_TC609_02080101_TextPerplexity could not calculate loss for the input"
            )

        mean_loss = total_negative_log_likelihood / total_loss_tokens
        try:
            return math.exp(mean_loss)
        except OverflowError:
            return float("inf")

    @classmethod
    def eval(cls, input_data: Data) -> EvalDetail:
        cls._check_dependencies()

        res = EvalDetail(metric=cls.__name__)
        content = input_data.content
        if not isinstance(content, str) or not content.strip():
            res.status = True
            res.label = [f"{cls.metric_type}.{cls.__name__}"]
            res.reason = ["Text perplexity cannot be calculated for empty content"]
            return res

        threshold = cls.dynamic_config.threshold
        if threshold is None or threshold <= 0:
            raise ValueError(
                "Rule_TC609_02080101_TextPerplexity dynamic_config.threshold must be greater than 0"
            )

        model_name = getattr(
            cls.dynamic_config,
            "model",
            "uer/gpt2-chinese-cluecorpussmall",
        )
        stride = getattr(cls.dynamic_config, "stride", 512)
        tokenizer, model = cls._get_model_components(model_name)
        perplexity = cls._calculate_perplexity(
            content,
            tokenizer,
            model,
            stride,
        )

        if perplexity > threshold:
            res.status = True
            res.label = [f"{cls.metric_type}.{cls.__name__}"]
            res.reason = [
                f"Text perplexity {perplexity:.4f} exceeds threshold "
                f"{threshold:.4f} (model: {model_name})"
            ]
        else:
            res.label = [QualityLabel.QUALITY_GOOD]
            res.reason = [
                f"Text perplexity: {perplexity:.4f} "
                f"(threshold: {threshold:.4f}, model: {model_name})"
            ]
        return res


@Model.rule_register("QUALITY_BAD_TC609_02080102", ["guobiao"])
class Rule_TC609_02080102_KnowledgeInformationDensity(Rule_TC609_Composite):
    component_rules = (
        "dingo.model.rule.rule_common.RuleAlphaWords",
        "dingo.model.rule.rule_common.RuleStopWord",
        "dingo.model.rule.rule_common.RuleUniqueWords",
    )
    _required_fields = [RequiredField.CONTENT]
    _metric_info = _tc609_metric_info(
        "02080102",
        "Rule_TC609_02080102_KnowledgeInformationDensity",
        "Combines alphabetic-word, stop-word, and unique-word ratio checks.",
        "partial",
    )


@Model.rule_register("QUALITY_BAD_TC609_02080103", ["guobiao"])
class Rule_TC609_02080103_RepeatedContent(Rule_TC609_Composite):
    component_rules = (
        "dingo.model.rule.rule_common.RuleDocRepeat",
        "dingo.model.rule.rule_common.RuleDocFormulaRepeat",
    )
    _required_fields = [RequiredField.CONTENT]
    _metric_info = _tc609_metric_info(
        "02080103",
        "Rule_TC609_02080103_RepeatedContent",
        "Combines document-text and formula repetition checks.",
        "covered",
    )


@Model.rule_register("QUALITY_BAD_TC609_02080104", ["guobiao"])
class Rule_TC609_02080104_TextCompleteness(Rule_TC609_Composite):
    component_rules = (
        "dingo.model.rule.rule_common.RuleContentNull",
        "dingo.model.rule.rule_common.RuleContentShort",
        "dingo.model.rule.rule_common.RuleLineEndWithEllipsis",
        "dingo.model.rule.rule_common.RuleLineEndWithTerminal",
    )
    _required_fields = [RequiredField.CONTENT]
    _metric_info = _tc609_metric_info(
        "02080104",
        "Rule_TC609_02080104_TextCompleteness",
        "Combines null, short, ellipsis-ending, and terminal-ending checks.",
        "covered",
    )


@Model.rule_register("QUALITY_BAD_TC609_02080105", ["guobiao"])
class Rule_TC609_02080105_InformationMissing(Rule_TC609_Composite):
    component_rules = (
        "dingo.model.rule.rule_common.RuleContentNull",
        "dingo.model.rule.rule_common.RuleContentShort",
        "dingo.model.rule.rule_common.RuleSentenceNumber",
        "dingo.model.rule.rule_common.RuleWordNumber",
    )
    _required_fields = [RequiredField.CONTENT]
    _metric_info = _tc609_metric_info(
        "02080105",
        "Rule_TC609_02080105_InformationMissing",
        "Uses content length and sentence/word counts as partial missing-information checks.",
        "partial",
    )


@Model.rule_register("QUALITY_BAD_TC609_02080106", ["guobiao"])
class Rule_TC609_02080106_TextPurity(Rule_TC609_Composite):
    component_rules = (
        "dingo.model.rule.rule_common.RuleAbnormalChar",
        "dingo.model.rule.rule_common.RuleAbnormalHtml",
        "dingo.model.rule.rule_common.RuleInvisibleChar",
        "dingo.model.rule.rule_common.RuleSpecialCharacter",
        "dingo.model.rule.rule_common.RuleWatermark",
    )
    _required_fields = [RequiredField.CONTENT]
    _metric_info = _tc609_metric_info(
        "02080106",
        "Rule_TC609_02080106_TextPurity",
        "Combines abnormal HTML, character, invisible-content, and watermark checks.",
        "partial",
    )


@Model.rule_register("QUALITY_BAD_TC609_02080107", ["guobiao"])
class Rule_TC609_02080107_TextCoherence(Rule_TC609_Composite):
    component_rules = (
        "dingo.model.rule.rule_common.RuleNoPunc",
        "dingo.model.rule.rule_common.RuleWordSplit",
        "dingo.model.rule.rule_common.RuleWordStuck",
        "dingo.model.rule.rule_common.RuleEnterAndSpace",
        "dingo.model.rule.rule_common.RuleEnterMore",
    )
    _required_fields = [RequiredField.CONTENT]
    _metric_info = _tc609_metric_info(
        "02080107",
        "Rule_TC609_02080107_TextCoherence",
        "Combines punctuation, word-boundary, and line-break fluency checks.",
        "partial",
    )


@Model.rule_register("QUALITY_BAD_TC609_02080201", ["guobiao"])
class Rule_TC609_02080201_ImageResolution(Rule_TC609_Composite):
    component_rules = ("dingo.model.rule.rule_image.RuleImageSizeValid",)
    _required_fields = [RequiredField.IMAGE]
    _metric_info = _tc609_metric_info(
        "02080201",
        "Rule_TC609_02080201_ImageResolution",
        "Uses image aspect-ratio validation as partial resolution coverage.",
        "partial",
    )


@Model.rule_register("QUALITY_BAD_TC609_02080202", ["guobiao"])
class Rule_TC609_02080202_ImageDuplication(Rule_TC609_Composite):
    component_rules = ("dingo.model.rule.rule_image.RuleImageRepeat",)
    _required_fields = [RequiredField.CONTENT]
    _metric_info = _tc609_metric_info(
        "02080202",
        "Rule_TC609_02080202_ImageDuplication",
        "Uses PHash and CNN duplicate-image detection.",
        "covered",
    )


@Model.rule_register("QUALITY_BAD_TC609_02080203", ["guobiao"])
class Rule_TC609_02080203_ImageSignalNoiseRatio(Rule_TC609_Composite):
    component_rules = ("dingo.model.rule.rule_image.RuleImageQuality",)
    _required_fields = [RequiredField.IMAGE]
    _metric_info = _tc609_metric_info(
        "02080203",
        "Rule_TC609_02080203_ImageSignalNoiseRatio",
        "Uses NIMA image quality as partial evidence; it is not a true SNR metric.",
        "partial",
    )


@Model.rule_register("QUALITY_BAD_TC609_02080204", ["guobiao"])
class Rule_TC609_02080204_ImageClarity(Rule_TC609_Composite):
    component_rules = (
        "dingo.model.rule.rule_image.RuleImageValid",
        "dingo.model.rule.rule_image.RuleImageQuality",
    )
    _required_fields = [RequiredField.IMAGE]
    _metric_info = _tc609_metric_info(
        "02080204",
        "Rule_TC609_02080204_ImageClarity",
        "Combines image validity and NIMA quality as partial clarity coverage.",
        "partial",
    )


@Model.rule_register("QUALITY_BAD_TC609_02080301", ["guobiao_placeholder"])
class Rule_TC609_02080301_VideoResolution(_TC609PlaceholderBase):
    _metric_info = _tc609_metric_info(
        "02080301", "Rule_TC609_02080301_VideoResolution",
        "Placeholder: video resolution is not implemented.", "uncovered"
    )


@Model.rule_register("QUALITY_BAD_TC609_02080302", ["guobiao_placeholder"])
class Rule_TC609_02080302_VideoDuplication(_TC609PlaceholderBase):
    _metric_info = _tc609_metric_info(
        "02080302", "Rule_TC609_02080302_VideoDuplication",
        "Placeholder: duplicate-video detection is not implemented.", "uncovered"
    )


@Model.rule_register("QUALITY_BAD_TC609_02080303", ["guobiao_placeholder"])
class Rule_TC609_02080303_VideoFrameRate(_TC609PlaceholderBase):
    _metric_info = _tc609_metric_info(
        "02080303", "Rule_TC609_02080303_VideoFrameRate",
        "Placeholder: video FPS validation is not implemented.", "uncovered"
    )


@Model.rule_register("QUALITY_BAD_TC609_02080304", ["guobiao_placeholder"])
class Rule_TC609_02080304_VideoDuration(_TC609PlaceholderBase):
    _metric_info = _tc609_metric_info(
        "02080304", "Rule_TC609_02080304_VideoDuration",
        "Placeholder: video duration validation is not implemented.", "uncovered"
    )


@Model.rule_register("QUALITY_BAD_TC609_02080305", ["guobiao_placeholder"])
class Rule_TC609_02080305_VideoClarity(_TC609PlaceholderBase):
    _metric_info = _tc609_metric_info(
        "02080305", "Rule_TC609_02080305_VideoClarity",
        "Placeholder: video clarity evaluation is not implemented.", "uncovered"
    )


@Model.rule_register("QUALITY_BAD_TC609_02080306", ["guobiao_placeholder"])
class Rule_TC609_02080306_VideoDynamicRange(_TC609PlaceholderBase):
    _metric_info = _tc609_metric_info(
        "02080306", "Rule_TC609_02080306_VideoDynamicRange",
        "Placeholder: video dynamic-range evaluation is not implemented.", "uncovered"
    )


@Model.rule_register("QUALITY_BAD_TC609_02080401", ["guobiao"])
class Rule_TC609_02080401_AudioSignalNoiseRatio(Rule_TC609_Composite):
    # Existing RuleAudioDuration currently contains the SNR implementation.
    component_rules = ("dingo.model.rule.rule_audio.RuleAudioDuration",)
    _required_fields = [RequiredField.CONTENT]
    _metric_info = _tc609_metric_info(
        "02080401",
        "Rule_TC609_02080401_AudioSignalNoiseRatio",
        "Uses the existing Welch power-spectrum SNR implementation.",
        "covered",
    )


@Model.rule_register("QUALITY_BAD_TC609_02080402", ["guobiao_placeholder"])
class Rule_TC609_02080402_SignalDistortionRatio(_TC609PlaceholderBase):
    _metric_info = _tc609_metric_info(
        "02080402", "Rule_TC609_02080402_SignalDistortionRatio",
        "Placeholder: signal distortion ratio is not implemented.", "uncovered"
    )


@Model.rule_register("QUALITY_BAD_TC609_02080403", ["guobiao_placeholder"])
class Rule_TC609_02080403_AudioSampleRate(_TC609PlaceholderBase):
    _metric_info = _tc609_metric_info(
        "02080403", "Rule_TC609_02080403_AudioSampleRate",
        "Placeholder: sample-rate quality validation is not implemented.", "uncovered"
    )


@Model.rule_register("QUALITY_BAD_TC609_02080404", ["guobiao_placeholder"])
class Rule_TC609_02080404_AudioBitDepth(_TC609PlaceholderBase):
    _metric_info = _tc609_metric_info(
        "02080404", "Rule_TC609_02080404_AudioBitDepth",
        "Placeholder: audio bit-depth validation is not implemented.", "uncovered"
    )


@Model.rule_register("QUALITY_BAD_TC609_02080405", ["guobiao_placeholder"])
class Rule_TC609_02080405_AudioBitRate(_TC609PlaceholderBase):
    _metric_info = _tc609_metric_info(
        "02080405", "Rule_TC609_02080405_AudioBitRate",
        "Placeholder: audio bit-rate validation is not implemented.", "uncovered"
    )


@Model.rule_register("QUALITY_BAD_TC609_02080406", ["guobiao"])
class Rule_TC609_02080406_AudioDuration(Rule_TC609_Composite):
    # Existing RuleAudioSnrQuality currently contains the duration implementation.
    component_rules = ("dingo.model.rule.rule_audio.RuleAudioSnrQuality",)
    _required_fields = [RequiredField.CONTENT]
    _metric_info = _tc609_metric_info(
        "02080406",
        "Rule_TC609_02080406_AudioDuration",
        "Uses the existing WAV duration implementation.",
        "covered",
    )


@Model.rule_register("QUALITY_BAD_TC609_0301", ["guobiao_placeholder"])
class Rule_TC609_0301_ContentDiversity(_TC609PlaceholderBase):
    """0301: Placeholder for content diversity."""

    _metric_info = _tc609_metric_info(
        "0301",
        "Rule_TC609_0301_ContentDiversity",
        "Placeholder: target-scenario distribution coverage is not implemented.",
        "uncovered",
    )


@Model.rule_register("QUALITY_BAD_TC609_0302", ["guobiao_placeholder"])
class Rule_TC609_0302_ScaleCompleteness(_TC609PlaceholderBase):
    """0302: Placeholder for scale completeness."""

    _metric_info = _tc609_metric_info(
        "0302",
        "Rule_TC609_0302_ScaleCompleteness",
        "Placeholder: dataset scale versus model requirements is not implemented.",
        "uncovered",
    )


@Model.rule_register("QUALITY_BAD_TC609_0303", ["guobiao"])
class Rule_TC609_0303_DataTimeRange(BaseRule):
    """Check whether creation/update time fields are within configured ranges."""

    _metric_info = {
        "category": "National Standard Data Quality Metrics",
        "quality_dimension": "TIMELINESS",
        "metric_name": "Rule_TC609_0303_DataTimeRange",
        "description": (
            "Checks whether created and updated timestamps are within configured "
            "time ranges"
        ),
        "paper_title": "High-quality dataset quality evaluation specification",
        "paper_url": "",
        "paper_authors": "SAC/TC609",
        "evaluation_results": "",
        "standard_code": "0303",
        "coverage": "covered",
    }

    _required_fields = [RequiredField.DT]
    dynamic_config = EvaluatorRuleArgs(
        dt_start=None,
        dt_end=None,
    )

    @classmethod
    def _parse_datetime(cls, value, field_name):
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value
            return value.astimezone(timezone.utc).replace(tzinfo=None)

        if isinstance(value, str):
            text = value.strip()
            if not text:
                raise ValueError(f"{field_name} is empty")

            iso_text = text.replace("Z", "+00:00")
            try:
                parsed = datetime.fromisoformat(iso_text)
                if parsed.tzinfo is None:
                    return parsed
                return parsed.astimezone(timezone.utc).replace(tzinfo=None)
            except ValueError:
                raise ValueError(
                    f"{field_name} has unsupported datetime format: {value!r}"
                ) from None

        raise ValueError(
            f"{field_name} has unsupported datetime format: {value!r}"
        )

    @classmethod
    def _validate_time_range(
        cls,
        dt_value,
        start_value,
        end_value,
    ):
        parsed_dt = cls._parse_datetime(dt_value, "time_value")
        parsed_dt_start = (
            cls._parse_datetime(start_value, "start_time")
            if start_value is not None
            else None
        )
        parsed_dt_end = (
            cls._parse_datetime(end_value, "end_time")
            if end_value is not None
            else None
        )

        if (
            parsed_dt_start is not None
            and parsed_dt_end is not None
            and parsed_dt_start > parsed_dt_end
        ):
            raise ValueError("time range is invalid: start is later than end")

        if parsed_dt_start is not None and parsed_dt < parsed_dt_start:
            return False, parsed_dt, parsed_dt_start, parsed_dt_end
        if parsed_dt_end is not None and parsed_dt > parsed_dt_end:
            return False, parsed_dt, parsed_dt_start, parsed_dt_end
        return True, parsed_dt, parsed_dt_start, parsed_dt_end

    @classmethod
    def eval(cls, input_data: Data) -> EvalDetail:
        res = EvalDetail(metric=cls.__name__)

        dt_start = getattr(cls.dynamic_config, "dt_start", None)
        dt_end = getattr(cls.dynamic_config, "dt_end", None)

        if dt_start is None and dt_end is None:
            raise ValueError(
                "Rule_TC609_0303_DataTimeRange requires at least one configured range boundary in dynamic_config"
            )

        dt_value = getattr(input_data, "dt", None)
        if dt_value is None:
            res.status = True
            res.label = [f"{cls.metric_type}.{cls.__name__}"]
            res.reason = ["dt is missing"]
            return res

        try:
            is_valid, parsed_dt, parsed_dt_start, parsed_dt_end = cls._validate_time_range(
                dt_value=dt_value,
                start_value=dt_start,
                end_value=dt_end,
            )
        except ValueError as exc:
            res.status = True
            res.label = [f"{cls.metric_type}.{cls.__name__}"]
            res.reason = [f"dt: {exc}"]
            return res

        if not is_valid:
            res.status = True
            res.label = [f"{cls.metric_type}.{cls.__name__}"]
            if parsed_dt_start is not None and parsed_dt < parsed_dt_start:
                res.reason = [
                    f"dt {parsed_dt.isoformat(sep=' ')} is earlier than "
                    f"allowed start {parsed_dt_start.isoformat(sep=' ')}"
                ]
            else:
                res.reason = [
                    f"dt {parsed_dt.isoformat(sep=' ')} is later than "
                    f"allowed end {parsed_dt_end.isoformat(sep=' ')}"
                ]
            return res

        res.label = [QualityLabel.QUALITY_GOOD]
        return res


@Model.rule_register("QUALITY_BAD_TC609_0304", ["guobiao"])
class Rule_TC609_0304_AnnotationAccuracy(Rule_TC609_Composite):
    """0304: Annotation accuracy, partially covered by label checks."""

    component_rules = (
        "dingo.model.rule.rule_image.RuleImageLabelOverlap",
        "dingo.model.rule.rule_image.RuleImageLabelVisualization",
    )
    _required_fields = [RequiredField.IMAGE]
    _metric_info = _tc609_metric_info(
        "0304",
        "Rule_TC609_0304_AnnotationAccuracy",
        "Uses image annotation checks as partial evidence of annotation accuracy.",
        "partial",
    )


@Model.rule_register("QUALITY_BAD_TC609_0305", ["guobiao_placeholder"])
class Rule_TC609_0305_ModelAdaptability(_TC609PlaceholderBase):
    """0305: Placeholder for model adaptability."""

    _metric_info = _tc609_metric_info(
        "0305",
        "Rule_TC609_0305_ModelAdaptability",
        "Placeholder: before/after model performance comparison is not implemented.",
        "uncovered",
    )
