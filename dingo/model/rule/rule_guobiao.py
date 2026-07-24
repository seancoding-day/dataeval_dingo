import importlib.util
import math
import re

from dingo.config.input_args import EvaluatorRuleArgs
from dingo.io.input import Data, RequiredField
from dingo.io.output.eval_detail import EvalDetail, QualityLabel
from dingo.model.model import Model
from dingo.model.rule.base import BaseRule


@Model.rule_register("QUALITY_BAD_TYPE_CONSISTENCY", ["guobiao"])
class RuleDataTypeConsistency(BaseRule):
    """Check whether content belongs to the type declared in ``input_data.type``.

    A local zero-shot classifier evaluates the hypothesis ``这段文本属于{type}类型``.
    The declared type may be any non-empty string, such as ``医疗`` or ``金融``.
    """

    _metric_info = {
        "category": "National Standard Data Quality Metrics",
        "quality_dimension": "TYPE_CONSISTENCY",
        "metric_name": "RuleDataTypeConsistency",
        "description": (
            "Uses a local zero-shot classifier to check whether content belongs "
            "to the type declared in the record"
        ),
        "paper_title": "High-quality dataset classification guide",
        "paper_url": "",
        "paper_authors": "SAC/TC609",
        "evaluation_results": "",
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
                "RuleDataTypeConsistency requires optional packages: "
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
                "RuleDataTypeConsistency dynamic_config.threshold must be in (0, 1]"
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


@Model.rule_register("QUALITY_BAD_FLUENCY", ["pretrain", "guobiao"])
class RuleTextPerplexity(BaseRule):
    """Check whether text perplexity exceeds the configured threshold."""

    _metric_info = {
        "category": "National Standard Data Quality Metrics",
        "quality_dimension": "FLUENCY",
        "metric_name": "RuleTextPerplexity",
        "description": (
            "Calculates text perplexity with a causal language model and "
            "flags text whose PPL exceeds the configured threshold"
        ),
        "paper_title": "High-quality dataset quality evaluation specification",
        "paper_url": "",
        "paper_authors": "SAC/TC609",
        "evaluation_results": ""
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
                "RuleTextPerplexity requires optional packages: "
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
                "RuleTextPerplexity requires transformers and torch. "
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
                "RuleTextPerplexity requires transformers and torch. "
                'Install them with: pip install "dingo-python[hhem]"'
            ) from exc

        encodings = tokenizer(content, return_tensors="pt")
        input_ids = encodings["input_ids"]
        sequence_length = input_ids.size(1)
        if sequence_length < 2:
            raise ValueError(
                "RuleTextPerplexity requires at least two model tokens"
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
                "RuleTextPerplexity could not calculate loss for the input"
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
                "RuleTextPerplexity dynamic_config.threshold must be greater than 0"
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


class _RuleDatasetDocCompletenessBase(BaseRule):
    """Shared logic for dataset documentation completeness checks."""

    _required_fields = [RequiredField.CONTENT]
    _default_threshold = 0.8
    _default_semantic_threshold = 0.5
    _default_model = "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"
    _default_device = -1
    _default_dimension_name = "Dataset documentation"
    _default_aspect_keywords = {}
    dynamic_config = EvaluatorRuleArgs(
        threshold=_default_threshold,
        semantic_threshold=_default_semantic_threshold,
        model=_default_model,
        device=_default_device,
        dimension_name=_default_dimension_name,
        aspect_keywords=_default_aspect_keywords,
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
                f"{cls.__name__} requires optional packages: "
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
    def _calculate_aspect_score(cls, content, aspect_text, model_name, device):
        classifier = cls._get_classifier(model_name, device)
        result = classifier(
            content,
            candidate_labels=[aspect_text],
            hypothesis_template="这段文本包含{}相关说明。",
            multi_label=True,
            truncation=True,
        )
        labels = result.get("labels", [])
        scores = result.get("scores", [])
        if not labels or not scores or labels[0] != aspect_text:
            raise RuntimeError("Zero-shot classifier returned an invalid result")
        score = float(scores[0])
        if not math.isfinite(score) or not 0.0 <= score <= 1.0:
            raise RuntimeError(
                f"Zero-shot classifier returned an invalid score: {score}"
            )
        return score

    @classmethod
    def _match_aspects(
        cls,
        content,
        normalized_content,
        aspect_keywords,
        model_name,
        device,
        semantic_threshold,
    ):
        matched = {}
        missing = []
        for aspect_name, keywords in aspect_keywords.items():
            aspect_text = (
                f"{aspect_name}（关键词示例：{'、'.join(keywords)}）"
                if keywords
                else aspect_name
            )
            score = cls._calculate_aspect_score(
                content, aspect_text, model_name, device
            )
            evidence_keyword = next(
                (
                    keyword
                    for keyword in keywords
                    if keyword.lower() in normalized_content
                ),
                None,
            )
            if score >= semantic_threshold:
                matched[aspect_name] = {
                    "score": round(score, 4),
                    "keyword": evidence_keyword,
                }
            else:
                missing.append(aspect_name)
        return matched, missing

    @classmethod
    def eval(cls, input_data: Data) -> EvalDetail:
        res = EvalDetail(metric=cls.__name__)
        content = getattr(input_data, "content", None)
        if not isinstance(content, str) or not content.strip():
            res.status = True
            res.label = [f"{cls.metric_type}.{cls.__name__}"]
            res.reason = ["Content is missing or empty"]
            res.score = 0.0
            return res

        threshold = getattr(cls.dynamic_config, "threshold", cls._default_threshold)
        if threshold is None or not 0 < threshold <= 1:
            raise ValueError(
                f"{cls.__name__} dynamic_config.threshold must be in (0, 1]"
            )
        
        semantic_threshold = getattr(
            cls.dynamic_config,
            "semantic_threshold",
            cls._default_semantic_threshold,
        )
        if semantic_threshold is None or not 0 < semantic_threshold <= 1:
            raise ValueError(
                f"{cls.__name__} dynamic_config.semantic_threshold must be in (0, 1]"
            )

        aspect_keywords = getattr(
            cls.dynamic_config,
            "aspect_keywords",
            cls._default_aspect_keywords,
        )
        if not isinstance(aspect_keywords, dict) or not aspect_keywords:
            raise ValueError(
                f"{cls.__name__} dynamic_config.aspect_keywords must be a non-empty dict"
            )
        
        model_name = getattr(cls.dynamic_config, "model", cls._default_model)
        if not isinstance(model_name, str) or not model_name.strip():
            raise ValueError(
                f"{cls.__name__} dynamic_config.model must be a non-empty string"
            )
        
        device = getattr(cls.dynamic_config, "device", cls._default_device)
        
        dimension_name = getattr(
            cls.dynamic_config, "dimension_name", cls._default_dimension_name
        )

        normalized_content = re.sub(r"\s+", "", content).lower()
        matched, missing = cls._match_aspects(
            content=content,
            normalized_content=normalized_content,
            aspect_keywords=aspect_keywords,
            model_name=model_name,
            device=device,
            semantic_threshold=semantic_threshold,
        )

        total = len(aspect_keywords)
        matched_count = len(matched)
        score = matched_count / total if total else 0.0
        res.score = round(score, 4)
        matched_desc = (
            ", ".join(
                (
                    f"{aspect}(semantic_score={detail['score']:.4f}, "
                    f"keyword_hit={detail['keyword'] or 'None'})"
                )
                for aspect, detail in matched.items()
            )
            if matched
            else "None"
        )
        missing_desc = ", ".join(missing) if missing else "None"

        if score < threshold:
            res.status = True
            res.label = [f"{cls.metric_type}.{cls.__name__}"]
            res.reason = [
                f"{dimension_name} completeness score {score:.4f} is below "
                f"threshold {threshold:.4f} (A/B={matched_count}/{total}); "
                f"matched: {matched_desc}; missing: {missing_desc}"
            ]
        else:
            res.label = [QualityLabel.QUALITY_GOOD]
            res.reason = [
                f"{dimension_name} completeness score {score:.4f} meets "
                f"threshold {threshold:.4f} (A/B={matched_count}/{total}); "
                f"matched: {matched_desc}; missing: {missing_desc}"
            ]
        return res


@Model.rule_register("QUALITY_BAD_COMPLETENESS", ["guobiao"])
class RuleDocBasicInfoCompleteness(_RuleDatasetDocCompletenessBase):
    """0101: Basic information completeness in dataset documentation."""

    _metric_info = {
        "category": "National Standard Data Quality Metrics",
        "quality_dimension": "COMPLETENESS",
        "metric_name": "RuleDocBasicInfoCompleteness",
        "description": (
            "Checks whether dataset documentation covers basic information "
            "aspects such as scale, format, structure, access, and support"
        ),
        "paper_title": "High-quality dataset quality evaluation specification",
        "paper_url": "",
        "paper_authors": "SAC/TC609",
        "evaluation_results": "",
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


@Model.rule_register("QUALITY_BAD_COMPLETENESS", ["guobiao"])
class RuleDocContentFeatureCompleteness(_RuleDatasetDocCompletenessBase):
    """0102: Content feature completeness in dataset documentation."""

    _metric_info = {
        "category": "National Standard Data Quality Metrics",
        "quality_dimension": "COMPLETENESS",
        "metric_name": "RuleDocContentFeatureCompleteness",
        "description": (
            "Checks whether dataset documentation covers content-feature aspects "
            "such as modality, distribution, labels, examples, and limitations"
        ),
        "paper_title": "High-quality dataset quality evaluation specification",
        "paper_url": "",
        "paper_authors": "SAC/TC609",
        "evaluation_results": "",
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


@Model.rule_register("QUALITY_BAD_COMPLETENESS", ["guobiao"])
class RuleDocConstructionProcessCompleteness(_RuleDatasetDocCompletenessBase):
    """0103: Construction-process completeness in dataset documentation."""

    _metric_info = {
        "category": "National Standard Data Quality Metrics",
        "quality_dimension": "COMPLETENESS",
        "metric_name": "RuleDocConstructionProcessCompleteness",
        "description": (
            "Checks whether dataset documentation covers construction-process "
            "aspects such as data source, collection, processing, annotation, "
            "and version control"
        ),
        "paper_title": "High-quality dataset quality evaluation specification",
        "paper_url": "",
        "paper_authors": "SAC/TC609",
        "evaluation_results": "",
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


@Model.rule_register("QUALITY_BAD_COMPLETENESS", ["guobiao"])
class RuleDocApplicationCompleteness(_RuleDatasetDocCompletenessBase):
    """0104: Application-description completeness in dataset documentation."""

    _metric_info = {
        "category": "National Standard Data Quality Metrics",
        "quality_dimension": "COMPLETENESS",
        "metric_name": "RuleDocApplicationCompleteness",
        "description": (
            "Checks whether dataset documentation covers application aspects "
            "such as license, scenarios, evaluation method, benchmark, and cases"
        ),
        "paper_title": "High-quality dataset quality evaluation specification",
        "paper_url": "",
        "paper_authors": "SAC/TC609",
        "evaluation_results": "",
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
