import importlib
import importlib.util
import math
import re

from dingo.config.input_args import EvaluatorRuleArgs
from dingo.io.input import Data, RequiredField
from dingo.io.output.eval_detail import EvalDetail, QualityLabel
from dingo.model.rule.base import BaseRule


def _tc609_metric_info(code, name, description, coverage):
    """Build consistent documentation metadata for TC609 rules."""
    return {
        "category": "SAC/TC609 High-quality Dataset Metrics",
        "quality_dimension": code,
        "metric_name": name,
        "description": description,
        "paper_title": "High-quality dataset quality evaluation specification",
        "paper_url": "",
        "paper_authors": "SAC/TC609",
        "evaluation_results": "",
        "standard_code": code,
        "coverage": coverage,
    }


class Rule_TC609_Composite(BaseRule):
    """Base class for a TC609 metric composed from existing Dingo rules."""

    component_rules = ()
    composition_mode = "all"

    @classmethod
    def _resolve_rule(cls, dotted_path):
        module_name, class_name = dotted_path.rsplit(".", 1)
        module = importlib.import_module(module_name)
        return getattr(module, class_name)

    @classmethod
    def eval(cls, input_data: Data) -> EvalDetail:
        res = EvalDetail(metric=cls.__name__)
        reasons = []
        scores = []
        passed_count = 0
        for dotted_path in cls.component_rules:
            rule = cls._resolve_rule(dotted_path)
            try:
                component_res = rule.eval(input_data)
            except (ImportError, ModuleNotFoundError):
                raise
            except Exception as exc:
                reasons.append(f"{rule.__name__}: {type(exc).__name__}: {exc}")
                continue
            if component_res.score is not None:
                scores.append(component_res.score)
            if component_res.status:
                component_reasons = component_res.reason or ["quality check failed"]
                reasons.extend(
                    f"{rule.__name__}: {reason}" for reason in component_reasons
                )
            else:
                passed_count += 1

        if scores:
            res.score = sum(scores) / len(scores)
        if cls.composition_mode == "any":
            res.status = passed_count == 0
        else:
            res.status = passed_count != len(cls.component_rules)
        if res.status:
            res.label = [f"{cls.metric_type}.{cls.__name__}"]
            res.reason = reasons
        else:
            res.label = [QualityLabel.QUALITY_GOOD]
        return res


class _TC609PlaceholderBase(BaseRule):
    """Base class for registered TC609 metrics that are not implemented yet."""

    @classmethod
    def eval(cls, input_data: Data) -> EvalDetail:
        raise NotImplementedError(
            f"{cls.__name__} is a TC609 placeholder and is not implemented yet"
        )


class Rule_TC609_01_DocCompleteness(BaseRule):
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
