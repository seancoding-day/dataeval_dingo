import importlib.util
import math

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
