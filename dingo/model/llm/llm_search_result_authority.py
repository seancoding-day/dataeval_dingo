"""Rule-based search result authority grader."""

from __future__ import annotations

import json
import math
import statistics
from dataclasses import dataclass
from typing import Any

from dingo.config.input_args import EvaluatorLLMArgs
from dingo.io.input import Data
from dingo.io.output.eval_detail import EvalDetail
from dingo.model import Model


HIGH_AUTHORITY_VENUE_HINTS = (
    "nature",
    "science",
    "cell",
    "nejm",
    "lancet",
    "jama",
    "acm",
    "ieee",
    "springer",
    "elsevier",
    "wiley",
    "neurips",
    "icml",
    "iclr",
    "cvpr",
    "acl",
    "emnlp",
    "aaai",
    "ijcai",
    "sigir",
)


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _normalize_text(text: Any) -> str:
    return " ".join(str(text or "").lower().split())


def extract_venue(result: dict[str, Any]) -> str:
    return str(
        result.get("publication_venue_name_unified")
        or result.get("publication_venue_name")
        or result.get("venue")
        or result.get("source")
        or ""
    )


def extract_citations(result: dict[str, Any], key: str = "citation_count") -> float:
    try:
        return float(result.get(key) or 0)
    except (TypeError, ValueError):
        return 0.0


@dataclass
class AuthorityGrade:
    """Structured authority score for one search result."""

    score: float = 0.0
    citation_score: float = 0.0
    influential_citation_score: float = 0.0
    venue_score: float = 0.0
    doi_score: float = 0.0
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": round(self.score, 5),
            "citation_score": round(self.citation_score, 5),
            "influential_citation_score": round(self.influential_citation_score, 5),
            "venue_score": round(self.venue_score, 5),
            "doi_score": round(self.doi_score, 5),
            "reason": self.reason,
        }


@dataclass
class AuthoritySummary:
    mean_score: float = 0.0
    median_score: float = 0.0
    mean_citation_score: float = 0.0
    mean_influential_citation_score: float = 0.0
    mean_venue_score: float = 0.0
    mean_doi_score: float = 0.0
    graded_pairs: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "authority_mean_score": round(self.mean_score, 5),
            "authority_median_score": round(self.median_score, 5),
            "authority_mean_citation_score": round(self.mean_citation_score, 5),
            "authority_mean_influential_citation_score": round(self.mean_influential_citation_score, 5),
            "authority_mean_venue_score": round(self.mean_venue_score, 5),
            "authority_mean_doi_score": round(self.mean_doi_score, 5),
            "authority_graded_pairs": self.graded_pairs,
        }


@Model.llm_register("LLMSearchResultAuthority")
class LLMSearchResultAuthority:
    """Authority scorer based on citation impact, venue, and DOI metadata."""

    dynamic_config = EvaluatorLLMArgs()
    default_threshold = 0.15

    def grade(self, *, result: dict[str, Any]) -> AuthorityGrade:
        venue = _normalize_text(extract_venue(result))
        venue_type = _normalize_text(result.get("publication_venue_type") or "")
        citations = extract_citations(result, "citation_count")
        influential = extract_citations(result, "influential_citation_count")

        citation_score = _clamp(math.log1p(citations) / math.log1p(500.0))
        influential_score = _clamp(math.log1p(influential) / math.log1p(50.0))

        venue_score = 0.25
        reason = "unknown_or_low_signal_venue"
        if any(hint in venue for hint in HIGH_AUTHORITY_VENUE_HINTS):
            venue_score = 0.85
            reason = "high_authority_venue_hint"
        elif "journal" in venue_type or "conference" in venue_type:
            venue_score = 0.65
            reason = "journal_or_conference"
        elif "repository" in venue_type or "preprint" in venue:
            venue_score = 0.45
            reason = "repository_or_preprint"

        doi_score = 1.0 if result.get("doi") or "doi.org" in json.dumps(result.get("locations", [])) else 0.0
        score = (
            0.45 * citation_score
            + 0.20 * influential_score
            + 0.25 * venue_score
            + 0.10 * doi_score
        )
        return AuthorityGrade(
            score=_clamp(score),
            citation_score=citation_score,
            influential_citation_score=influential_score,
            venue_score=venue_score,
            doi_score=doi_score,
            reason=reason,
        )

    @classmethod
    def _config_value(cls, name: str, default: Any = None) -> Any:
        return getattr(cls.dynamic_config, name, default)

    @classmethod
    def eval(cls, input_data: Data) -> EvalDetail:
        """Executor entry point: evaluate one flattened search result row."""
        result = getattr(input_data, "search_result", None)
        if not isinstance(result, dict):
            result = input_data.to_dict()

        grade = cls().grade(result=result)
        threshold = float(cls._config_value("threshold", cls.default_threshold) or cls.default_threshold)

        labels: list[str] = []
        if grade.score < threshold:
            labels.append("Authority.Error_Authority_Low")
            if grade.citation_score <= 0.0:
                labels.append("Authority.Error_Citation_Miss")
            if grade.venue_score <= 0.25:
                labels.append("Authority.Error_Venue_Low_Signal")
            if grade.doi_score <= 0.0:
                labels.append("Authority.Error_DOI_Miss")

        status = bool(labels)
        if not labels:
            labels = ["QUALITY_GOOD"]

        return EvalDetail(
            metric=cls.__name__,
            status=status,
            score=round(grade.score, 5),
            label=labels,
            reason=[grade.to_dict()],
        )


def aggregate_grades(grades: list[AuthorityGrade]) -> AuthoritySummary:
    if not grades:
        return AuthoritySummary()
    return AuthoritySummary(
        mean_score=statistics.mean(g.score for g in grades),
        median_score=statistics.median(g.score for g in grades),
        mean_citation_score=statistics.mean(g.citation_score for g in grades),
        mean_influential_citation_score=statistics.mean(g.influential_citation_score for g in grades),
        mean_venue_score=statistics.mean(g.venue_score for g in grades),
        mean_doi_score=statistics.mean(g.doi_score for g in grades),
        graded_pairs=len(grades),
    )
