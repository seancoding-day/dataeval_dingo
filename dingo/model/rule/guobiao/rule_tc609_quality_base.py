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


_text_embedding_components = {}


def _get_text_embedding_components(model_name, device):
    """Load and cache a transformer model used for text embeddings."""
    missing_packages = [
        package
        for package in ("torch", "transformers")
        if importlib.util.find_spec(package) is None
    ]
    if missing_packages:
        raise ImportError(
            "Text consistency evaluation requires optional packages: "
            f"{', '.join(missing_packages)}. "
            'Install them with: pip install "dingo-python[hhem]"'
        )

    import torch
    from transformers import AutoModel, AutoTokenizer

    if device == -1:
        torch_device = "cpu"
    elif isinstance(device, int):
        torch_device = f"cuda:{device}"
    else:
        torch_device = str(device)

    cache_key = (model_name, torch_device)
    if cache_key not in _text_embedding_components:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModel.from_pretrained(model_name)
        model.to(torch_device)
        model.eval()
        _text_embedding_components[cache_key] = (
            tokenizer,
            model,
            torch_device,
        )
    return _text_embedding_components[cache_key]


def _encode_texts(texts, model_name, device, batch_size, max_length):
    """Encode texts once in batches and return normalized sentence vectors."""
    import torch
    import torch.nn.functional as functional

    tokenizer, model, torch_device = _get_text_embedding_components(
        model_name,
        device,
    )
    embeddings = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]
        encoded = tokenizer(
            batch,
            padding=True,
            truncation=True,
            max_length=max_length,
            return_tensors="pt",
        )
        encoded = {
            key: value.to(torch_device)
            for key, value in encoded.items()
        }
        with torch.inference_mode():
            hidden_state = model(**encoded).last_hidden_state
        attention_mask = encoded["attention_mask"].unsqueeze(-1)
        pooled = (
            (hidden_state * attention_mask).sum(dim=1)
            / attention_mask.sum(dim=1).clamp(min=1)
        )
        embeddings.append(functional.normalize(pooled, p=2, dim=1).cpu())
    return torch.cat(embeddings, dim=0)


def calculate_text_consistency(
    texts,
    model_name,
    device=-1,
    threshold=0.5,
    batch_size=16,
    max_length=512,
    consensus_keep_ratio=0.8,
):
    """Calculate semantic consistency for two or more texts.

    Two texts are compared directly. For three or more texts, every text is
    compared with a robust semantic center so the calculation remains linear
    in the number of texts rather than evaluating all text pairs.
    """
    if (
        not isinstance(texts, list)
        or len(texts) < 2
        or any(not isinstance(text, str) or not text.strip() for text in texts)
    ):
        raise ValueError(
            "calculate_text_consistency requires at least two non-empty texts"
        )
    if (
        isinstance(threshold, bool)
        or not isinstance(threshold, (int, float))
        or not 0 <= threshold <= 1
    ):
        raise ValueError("threshold must be in [0, 1]")
    if isinstance(batch_size, bool) or not isinstance(batch_size, int) or batch_size <= 0:
        raise ValueError("batch_size must be a positive integer")
    if isinstance(max_length, bool) or not isinstance(max_length, int) or max_length <= 0:
        raise ValueError("max_length must be a positive integer")
    if not 0 < consensus_keep_ratio <= 1:
        raise ValueError("consensus_keep_ratio must be in (0, 1]")

    import torch
    import torch.nn.functional as functional

    normalized_texts = [text.strip() for text in texts]
    embeddings = _encode_texts(
        normalized_texts,
        model_name,
        device,
        batch_size,
        max_length,
    )

    if len(normalized_texts) == 2:
        score = float(torch.sum(embeddings[0] * embeddings[1]).item())
        item_scores = [score, score]
    else:
        initial_center = functional.normalize(
            embeddings.mean(dim=0),
            p=2,
            dim=0,
        )
        initial_scores = embeddings @ initial_center
        keep_count = max(
            2,
            math.ceil(len(normalized_texts) * consensus_keep_ratio),
        )
        keep_indexes = torch.topk(initial_scores, keep_count).indices
        robust_center = functional.normalize(
            embeddings[keep_indexes].mean(dim=0),
            p=2,
            dim=0,
        )
        similarities = embeddings @ robust_center
        score = float(torch.min(similarities).item())
        item_scores = [float(value) for value in similarities.tolist()]

    score = min(1.0, max(0.0, score))
    item_scores = [
        min(1.0, max(0.0, value))
        for value in item_scores
    ]
    return {
        "score": score,
        "is_consistent": score >= threshold,
        "item_scores": item_scores,
        "outlier_indexes": [
            index
            for index, item_score in enumerate(item_scores)
            if item_score < threshold
        ],
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
            except ValueError:
                # Invalid evaluator configuration must stop the composite
                # instead of being converted into a data-quality finding.
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
