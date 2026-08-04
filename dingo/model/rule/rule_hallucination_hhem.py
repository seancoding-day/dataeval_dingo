"""
MiniCheck Hallucination Detection Rule

This module provides local, API-free hallucination (ungrounded-claim) detection
for RAG-style data by checking whether a response is supported by its context.

Model: `lytang/MiniCheck-Flan-T5-Large` (EMNLP 2024, arXiv:2404.10774).

Why MiniCheck instead of Vectara HHEM-2.1-Open (the original backing model):
- Stronger grounding accuracy: MiniCheck-Flan-T5-Large scores 75.0 vs HHEM's
  71.8 on the LLM-AggreFact benchmark (llm-aggrefact.github.io).
- Robust across transformers versions: MiniCheck is a *standard*
  `T5ForConditionalGeneration` (config `model_type: t5`, no `auto_map` /
  `trust_remote_code`). HHEM shipped custom remote code that breaks on
  transformers >= 4.49 (AttributeError: `all_tied_weights_keys`), which forced
  a `<4.49` pin. MiniCheck removes that constraint.
- Still efficient and CPU-friendly (0.8B params), no API costs or rate limits.

The class name is kept as `RuleHallucinationHHEM` for backward compatibility
(the registered rule id `QUALITY_BAD_HALLUCINATION` and existing configs are
unaffected).

Inference is replicated faithfully from the official MiniCheck source
(Liyan06/MiniCheck): input `"predict: " + doc + </s> + claim`, a single-step
decoder forward, then a 2-way softmax over label token ids [3, 209] where
index 1 is P(supported). Long documents are split into word chunks and the
support probability is aggregated by max.
"""

import json
from threading import Lock
from typing import List

from dingo.config.input_args import EvaluatorRuleArgs
from dingo.io.input import Data, RequiredField
from dingo.io.output.eval_detail import EvalDetail
from dingo.model import Model
from dingo.model.rule.base import BaseRule
from dingo.utils import log


@Model.rule_register("QUALITY_BAD_HALLUCINATION", ["hallucination", "rag"])
class RuleHallucinationHHEM(BaseRule):
    """
    MiniCheck-based hallucination detection rule.

    Detects ungrounded claims by checking whether the response (content) is
    supported by the provided context, using `lytang/MiniCheck-Flan-T5-Large`:
    - Strong grounding accuracy (75.0 on LLM-AggreFact, > HHEM's 71.8)
    - Standard T5 model -> no transformers version pin, no remote code
    - Local inference, CPU-friendly, no API costs or rate limits

    Note: the class is still named `RuleHallucinationHHEM` for backward
    compatibility; the underlying model was upgraded from Vectara HHEM-2.1-Open
    to MiniCheck.
    """

    # Metadata for documentation generation
    _metric_info = {
        "category": "SFT Data Assessment Metrics",
        "quality_dimension": "HALLUCINATION",
        "metric_name": "RuleHallucinationHHEM",
        "description": "Uses the MiniCheck-Flan-T5-Large model for local hallucination "
                       "detection by checking whether the response is grounded in the context",
        "paper_title": "MiniCheck: Efficient Fact-Checking of LLMs on Grounding Documents",
        "paper_url": "https://arxiv.org/abs/2404.10774",
        "paper_authors": "Liyan Tang, Philippe Laban, Greg Durrett"
    }

    # CONTENT = the response/claim to verify; CONTEXT = the grounding document.
    # These are exactly the two inputs MiniCheck needs (claim vs. document), so
    # they remain the most fitting required fields.
    _required_fields = [RequiredField.CONTENT, RequiredField.CONTEXT]
    dynamic_config = EvaluatorRuleArgs(threshold=0.5)
    model = None
    tokenizer = None
    _load_lock = Lock()
    _model_repo_id = "lytang/MiniCheck-Flan-T5-Large"
    # MiniCheck flan-t5 inference config (from Liyan06/MiniCheck)
    _chunk_size = 500        # words per document chunk before max-aggregation
    _max_input_length = 2048  # tokenizer truncation length

    @classmethod
    def load_model(cls):
        """Load the MiniCheck-Flan-T5-Large model and tokenizer."""
        if cls.model is None:
            with cls._load_lock:
                if cls.model is not None:
                    return
                try:
                    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

                    log.info("Loading MiniCheck-Flan-T5-Large model...")
                    # MiniCheck is a standard T5 model: no trust_remote_code
                    # needed, and it loads on any modern transformers version.
                    try:
                        # Prefer offline / cached load first
                        cls.model = AutoModelForSeq2SeqLM.from_pretrained(
                            cls._model_repo_id, local_files_only=True,
                        )
                        cls.tokenizer = AutoTokenizer.from_pretrained(
                            cls._model_repo_id, local_files_only=True,
                        )
                    except Exception:
                        # Fall back to downloading from the Hub
                        cls.model = AutoModelForSeq2SeqLM.from_pretrained(
                            cls._model_repo_id,
                        )
                        cls.tokenizer = AutoTokenizer.from_pretrained(
                            cls._model_repo_id,
                        )
                    cls.model.eval()
                    log.info("✅ MiniCheck-Flan-T5-Large model loaded successfully")

                except ImportError:
                    raise ImportError(
                        "transformers is required for the MiniCheck model. "
                        "Install with: pip install transformers torch sentencepiece"
                    )
                except Exception as e:
                    raise RuntimeError(
                        "Failed to load MiniCheck model. "
                        "The first run requires network access to download "
                        f"'{cls._model_repo_id}', or a populated Hugging Face cache. "
                        f"Original error: {e}"
                    ) from e

    @staticmethod
    def _chunk_document(document: str, chunk_size: int) -> List[str]:
        """Split a document into consecutive chunks of ~chunk_size words.

        Lightweight, dependency-free approximation of MiniCheck's sentence-based
        chunking (the official code uses nltk sent_tokenize). RAG contexts
        usually fit in a single chunk, so this rarely changes behavior; long
        documents are still split so no content is silently truncated.
        """
        text = document.strip()
        if not text:
            return []
        words = text.split()
        if len(words) <= chunk_size:
            return [text]
        return [" ".join(words[i:i + chunk_size])
                for i in range(0, len(words), chunk_size)]

    @classmethod
    def _support_prob(cls, document: str, claim: str) -> float:
        """Probability that `claim` is supported by `document` (0=unsupported, 1=supported).

        Faithful replication of the official MiniCheck flan-t5 inference:
          input   = "predict: " + doc_chunk + tokenizer.eos_token + claim
          forward = model(input_ids, attention_mask, decoder_input_ids=zeros(B,1))
          logits  = outputs.logits.squeeze(1)
          probs   = softmax(logits[:, [3, 209]])   # 3=no support, 209=support
          support = probs[:, 1]
        Aggregated by max over document chunks.
        """
        import torch

        chunks = cls._chunk_document(document, cls._chunk_size) or [""]
        texts = ["predict: " + cls.tokenizer.eos_token.join([chunk, claim])
                 for chunk in chunks]
        enc = cls.tokenizer(
            texts,
            max_length=cls._max_input_length,
            truncation=True,
            padding=True,
            return_tensors="pt",
        )
        decoder_input_ids = torch.zeros(
            (enc["input_ids"].size(0), 1), dtype=torch.long)
        with torch.no_grad():
            logits = cls.model(
                input_ids=enc["input_ids"],
                attention_mask=enc["attention_mask"],
                decoder_input_ids=decoder_input_ids,
            ).logits.squeeze(1)
        # Label token ids from the official MiniCheck code: 3=no support, 209=support
        label_probs = torch.nn.functional.softmax(
            logits[:, torch.tensor([3, 209])], dim=-1)
        support_probs = label_probs[:, 1]
        return float(support_probs.max().item())

    @classmethod
    def eval(cls, input_data: Data) -> EvalDetail:
        """
        Evaluate hallucination using the MiniCheck-Flan-T5-Large model.

        Args:
            input_data: Data object containing content and context

        Returns:
            EvalDetail with hallucination detection results
        """
        # Check if context is available
        if not hasattr(input_data, 'context') or not input_data.context:
            # Try to get context from raw_data as fallback
            if hasattr(input_data, 'raw_data') and input_data.raw_data and 'context' in input_data.raw_data:
                contexts = input_data.raw_data['context']
            else:
                # No context available - cannot evaluate
                result = EvalDetail(metric=cls.__name__)
                result.status = True
                # result.type = cls.metric_type
                # result.name = "MISSING_CONTEXT"
                # result.reason = ["Context is required for hallucination detection but was not provided"]
                result.label = [f"{cls.metric_type}.MISSING_CONTEXT"]
                result.reason = ["Context is required for hallucination detection but was not provided"]
                return result
        else:
            contexts = input_data.context

        # Load model if not already loaded
        cls.load_model()

        # Prepare context(s)
        if isinstance(contexts, list):
            context_list = contexts
        else:
            # Try to parse as JSON list, fallback to single context
            try:
                context_list = json.loads(contexts)
                if not isinstance(context_list, list):
                    context_list = [str(contexts)]
            except (json.JSONDecodeError, ValueError):
                context_list = [str(contexts)]

        response = input_data.content

        try:
            # Score each context with MiniCheck: P(response supported by context).
            # support prob in [0,1], 1 = fully grounded / consistent.
            consistency_scores = [
                cls._support_prob(context, response) for context in context_list
            ]

            # Convert support probabilities to hallucination scores
            # (1 = hallucinated / ungrounded, 0 = consistent)
            hallucination_scores = [1.0 - score for score in consistency_scores]

            # Average hallucination score across all contexts
            avg_hallucination_score = sum(hallucination_scores) / len(hallucination_scores)

            # Create result
            result = EvalDetail(metric=cls.__name__)
            result.score = avg_hallucination_score

            # Determine if hallucination detected based on threshold
            if avg_hallucination_score > cls.dynamic_config.threshold:
                result.status = True
                # result.type = cls.metric_type
                # result.name = "HALLUCINATION_DETECTED"
                result.label = [f"{cls.metric_type}.HALLUCINATION_DETECTED"]

                # Generate detailed analysis
                analysis_parts = [
                    "🔍 MiniCheck 幻觉检测分析",
                    f"📊 平均幻觉分数: {avg_hallucination_score:.3f} (阈值: {cls.dynamic_config.threshold})",
                    f"📝 评估上下文数量: {len(context_list)}"
                ]

                # Add per-context analysis
                contradictions = []
                consistent_contexts = []

                for i, (context, consistency_score, hallucination_score) in enumerate(
                    zip(context_list, consistency_scores, hallucination_scores), 1
                ):
                    if hallucination_score > cls.dynamic_config.threshold:
                        contradictions.append(
                            f"  {i}. 上下文: \"{context[:100]}{'...' if len(context) > 100 else ''}\"\n"
                            f"     一致性分数: {consistency_score:.3f}, 幻觉分数: {hallucination_score:.3f}"
                        )
                    else:
                        consistent_contexts.append(
                            f"  {i}. 上下文: \"{context[:100]}{'...' if len(context) > 100 else ''}\"\n"
                            f"     一致性分数: {consistency_score:.3f}, 幻觉分数: {hallucination_score:.3f}"
                        )

                if contradictions:
                    analysis_parts.append(f"❌ 发现 {len(contradictions)} 个潜在矛盾:")
                    analysis_parts.extend(contradictions)

                if consistent_contexts:
                    analysis_parts.append(f"✅ {len(consistent_contexts)} 个上下文与回答一致:")
                    analysis_parts.extend(consistent_contexts)

                analysis_parts.extend([
                    f"🚨 结论: 检测到幻觉 (分数 {avg_hallucination_score:.3f} > 阈值 {cls.dynamic_config.threshold})",
                    "   回答与提供的上下文存在显著矛盾",
                    "",
                    "💡 模型信息: 使用 MiniCheck-Flan-T5-Large (本地推理)"
                ])

                # result.reason = ["\n".join(analysis_parts)]
                result.reason = ["\n".join(analysis_parts)]
            else:
                result.status = False
                # result.type = "QUALITY_GOOD"
                # result.name = "NO_HALLUCINATION"
                result.label = ['QUALITY_GOOD.NO_HALLUCINATION']

                # Generate analysis for non-hallucination case
                analysis = (
                    f"✅ MiniCheck 幻觉检测分析\n"
                    f"📊 平均幻觉分数: {avg_hallucination_score:.3f} (阈值: {cls.dynamic_config.threshold})\n"
                    f"📝 评估上下文数量: {len(context_list)}\n"
                    f"🎉 结论: 未检测到幻觉，回答与上下文基本一致\n"
                    f"💡 模型信息: 使用 MiniCheck-Flan-T5-Large (本地推理)"
                )
                # result.reason = [analysis]
                result.reason = [analysis]

            return result

        except Exception as e:
            # Handle model inference errors
            result = EvalDetail(metric=cls.__name__)
            result.status = True
            # result.type = cls.metric_type
            # result.name = "MINICHECK_ERROR"
            # result.reason = [f"MiniCheck model inference failed: {str(e)}"]
            result.label = [f"{cls.metric_type}.MINICHECK_ERROR"]
            result.reason = [f"MiniCheck model inference failed: {str(e)}"]
            return result

    @classmethod
    def evaluate_with_detailed_output(cls, input_data: Data) -> dict:
        """
        Evaluate with detailed output for analysis.

        Returns:
            Dictionary with detailed evaluation metrics
        """
        result = cls.eval(input_data)

        return {
            # "overall_score": getattr(result, 'score', 0.0),
            "is_hallucinated": result.eval_status,
            "threshold": cls.dynamic_config.threshold,
            # "assessment_type": result.type,
            # "assessment_name": result.name,
            "analysis": result.reason[0] if result.reason else "",
            "model_info": "MiniCheck-Flan-T5-Large"
        }

    @classmethod
    def batch_evaluate(cls, data_list: List[Data]) -> List[EvalDetail]:
        """
        Batch evaluation for efficiency.

        Args:
            data_list: List of Data objects to evaluate

        Returns:
            List of EvalDetail objects
        """
        # Load model once for batch processing
        cls.load_model()

        results = []
        for data in data_list:
            result = cls.eval(data)
            results.append(result)

        return results
