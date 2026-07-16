"""Search result effectiveness grader.

This grader scores whether a returned search result has enough usable
bibliographic content for a user to judge and consume it. Missing-field and
basic information-density checks are deterministic. Readability and corruption
checks can be delegated to an LLM judge to avoid over-penalizing normal academic
formulas, units, and symbols.

It intentionally does not judge topical relevance; use
``LLMSearchResultRelevance`` for that.
"""

from __future__ import annotations
import json
import logging
import re
import statistics
import time
from dataclasses import dataclass
from typing import Any

from dingo.config.input_args import EvaluatorLLMArgs
from dingo.io.input import Data
from dingo.io.output.eval_detail import EvalDetail
from dingo.model import Model

logger = logging.getLogger(__name__)


RULE_SPECIAL_CHARACTER_PATTERNS = (
    r"u200e",
    r"&#247;|\? :",
    r"[锟解枴閿熻В鏋碷�]|\{\/U\}",
    r"U\+26[0-F][0-D]|U\+273[3-4]|U\+1F[3-6][0-4][0-F]|U\+1F6[8-F][0-F]",
    r"<\|.*?\|>",
    r"<[^>]+>",
)
RULE_INVISIBLE_CHAR_PATTERN = r"[\u0080-\u009F\u2000-\u200F\u202F\u205F\u3000\uFEFF\u00A0\u2060-\u206F\uFEFF\xa0]"
RULE_ABNORMAL_CHAR_THRESHOLD = 0.01
HTML_TAG_PATTERN = r"<[^>]+>"
MOJIBAKE_EVIDENCE_PATTERN = r"[閿熻В鏋撮柨鐔恍掗弸纰凤拷�]|\{\/U\}|u[0-9a-fA-F]{4}"
UTF8_LATIN1_SEQUENCE_PATTERN = re.compile(r"[\u00C2\u00C3\u00D0\u00D1][\u0080-\u00BF]")
C1_CONTROL_PATTERN = re.compile(r"[\u0080-\u009F]")
UNICODE_REPLACEMENT_CHARACTER = "\ufffd"


LLM_FIELD_QUALITY_SYSTEM_PROMPT = """You are a strict but practical data quality evaluator for
academic search result metadata.

Judge whether each supplied metadata field is readable and clean enough to show to users.
Focus on real text-quality problems:
- missing or empty field
- invisible/control characters
- mojibake or garbled encoding, such as replacement characters, unreadable CJK mojibake,
  or UTF-8 text decoded as Latin-1 with repeated sequences like Ð... or Ñ...
- raw HTML/XML markup leaked into visible text, such as <span class='highlight'>...</span>
- suspicious special-character noise that materially hurts readability

Do NOT penalize normal academic content:
- mathematical formulas, LaTeX, chemical symbols, units, Greek letters
- punctuation, pipes used as separators, parentheses, slashes, hyphens
- mixed Chinese/English titles, journal names, abbreviations, DOI-like text

Return compact JSON only. Do not use markdown. Keep each reason within 12 words
and do not use double quotes inside reasons.
Schema:
{
  "fields": {
    "title": {"score": 0.0-1.0, "issues": ["..."], "reason": "..."},
    "abstract": {"score": 0.0-1.0, "issues": ["..."], "reason": "..."},
    "keywords": {"score": 0.0-1.0, "issues": ["..."], "reason": "..."},
    "venue": {"score": 0.0-1.0, "issues": ["..."], "reason": "..."},
    "author": {"score": 0.0-1.0, "issues": ["..."], "reason": "..."}
  },
  "overall_issues": ["..."],
  "reason": "short overall reason"
}

Use issue names from:
- missing_field
- invisible_char
- mojibake
- html_tag
- unreadable_text
- special_char_noise
- none

Scoring guidance:
- 1.0: clean, readable field; normal formulas and units are allowed.
- 0.7: mostly readable with minor display artifacts.
- 0.4: readable but contains visible markup or notable noise requiring cleanup.
- 0.1: unreadable garbled text, heavy mojibake, or severe invisible/control-character corruption.
- 0.0: missing/empty field.
"""


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _presence_quality(value: Any) -> float:
    """Score field presence without using content length as a quality proxy."""
    return 1.0 if str(value or "").strip() else 0.0


def _suspicious_latin1_mojibake_count(text: str) -> int:
    return len(UTF8_LATIN1_SEQUENCE_PATTERN.findall(text)) + len(C1_CONTROL_PATTERN.findall(text))


def _looks_like_utf8_latin1_mojibake(text: str) -> bool:
    """Detect UTF-8 text accidentally decoded as Latin-1.

    Literal characters such as ``Ð`` and ``Ñ`` can be valid text, so they are
    not sufficient evidence by themselves. A value is treated as suspicious
    when it contains repeated UTF-8/Latin-1 byte-shaped sequences or C1 control
    characters and a reversible Latin-1-to-UTF-8 repair removes that evidence.
    """
    value = str(text or "")
    if not value:
        return False

    suspicious_before = _suspicious_latin1_mojibake_count(value)
    if suspicious_before == 0:
        return False

    c1_count = len(C1_CONTROL_PATTERN.findall(value))
    repeated_sequences = len(UTF8_LATIN1_SEQUENCE_PATTERN.findall(value)) >= 2
    if not repeated_sequences and c1_count / max(1, len(value)) < RULE_ABNORMAL_CHAR_THRESHOLD:
        return False

    try:
        repaired = value.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        # Mixed-language metadata may contain legitimate non-Latin-1 text next
        # to a corrupted fragment. Repeated byte-shaped pairs plus C1 controls
        # are enough to send that field to the LLM judge for confirmation.
        return repeated_sequences and c1_count > 0

    suspicious_after = _suspicious_latin1_mojibake_count(repaired)
    return repaired != value and suspicious_after < suspicious_before


def _has_mojibake_evidence(text: str) -> bool:
    value = str(text or "")
    return (
        UNICODE_REPLACEMENT_CHARACTER in value
        or bool(re.search(MOJIBAKE_EVIDENCE_PATTERN, value))
        or _looks_like_utf8_latin1_mojibake(value)
    )


def _rule_abnormal_char_issues(text: str) -> list[str]:
    value = str(text or "")
    if not value:
        return []

    issues: list[str] = []
    special_matches: list[str] = []
    for pattern in RULE_SPECIAL_CHARACTER_PATTERNS:
        special_matches.extend(re.findall(pattern, value))
    has_html_tag = bool(re.search(HTML_TAG_PATTERN, value))
    if has_html_tag or len(special_matches) / len(value) >= RULE_ABNORMAL_CHAR_THRESHOLD:
        issues.append("RuleSpecialCharacter")

    has_mojibake = _has_mojibake_evidence(value)
    if has_mojibake:
        issues.append("RuleMojibake")

    invisible_matches = re.findall(RULE_INVISIBLE_CHAR_PATTERN, value)
    if not has_mojibake and len(invisible_matches) / len(value) >= RULE_ABNORMAL_CHAR_THRESHOLD:
        issues.append("RuleInvisibleChar")
    return issues


def _has_confirmed_llm_issue(issues: list[str] | None) -> bool:
    if not issues:
        return False
    ignored = {"none", "missing_field"}
    return any(str(issue).split(":")[-1].strip().lower() not in ignored for issue in issues)


def _filter_llm_field_issues(field: str, value: str, issues: list[str]) -> list[str]:
    """Keep only LLM issues supported by field-level evidence."""
    text = str(value or "")
    filtered: list[str] = []
    for issue in issues:
        issue_type = str(issue).split(":")[-1].strip().lower()
        keep = False
        if issue_type == "html_tag":
            keep = bool(re.search(HTML_TAG_PATTERN, text))
        elif issue_type == "invisible_char":
            keep = bool(re.search(RULE_INVISIBLE_CHAR_PATTERN, text))
        elif issue_type in {"mojibake", "unreadable_text"}:
            keep = _has_mojibake_evidence(text)
        elif issue_type == "special_char_noise":
            keep = bool(_rule_abnormal_char_issues(text))
        else:
            keep = True

        if keep and issue not in filtered:
            filtered.append(issue)
    return filtered


def _strip_json_fence(text: str) -> str:
    value = (text or "").strip()
    if value.startswith("```json"):
        value = value[7:].strip()
    elif value.startswith("```"):
        value = value[3:].strip()
    if value.endswith("```"):
        value = value[:-3].strip()
    return value


def _extract_json_object(text: str) -> str:
    value = _strip_json_fence(text)
    start = value.find("{")
    end = value.rfind("}")
    if start >= 0 and end > start:
        return value[start:end + 1]
    return value


def _safe_float(value: Any, default: float = 1.0) -> float:
    try:
        return _clamp(float(value))
    except (TypeError, ValueError):
        return default


def _normalize_issues(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        return [] if value.lower() == "none" else [value]
    if isinstance(value, list):
        issues = []
        for item in value:
            item_text = str(item).strip()
            if item_text and item_text.lower() != "none":
                issues.append(item_text)
        return issues
    return [str(value)]


EFFECTIVENESS_LABEL_MAP = {
    "missing_title": "Effectiveness.Error_Title_Miss",
    "missing_abstract": "Effectiveness.Error_Abstract_Miss",
    "missing_keywords": "Effectiveness.Error_Keywords_Miss",
    "missing_author": "Effectiveness.Error_Author_Miss",
    "html_tag": "Effectiveness.Error_HTML_Tag",
    "mojibake": "Effectiveness.Error_Mojibake",
    "invisible_char": "Effectiveness.Error_Invisible_Char",
    "unreadable_text": "Effectiveness.Error_Unreadable_Text",
    "special_char_noise": "Effectiveness.Error_Special_Char_Noise",
    "llm_quality_parse_error": "Effectiveness.Error_LLM_Quality_Parse",
    "RuleSpecialCharacter": "Effectiveness.Error_Rule_Special_Character",
    "RuleInvisibleChar": "Effectiveness.Error_Rule_Invisible_Char",
    "RuleMojibake": "Effectiveness.Error_Mojibake",
}


def _issue_to_label(issue: str) -> str | None:
    issue_text = str(issue or "").strip()
    if not issue_text:
        return None
    issue_type = issue_text.split(":")[-1]
    return EFFECTIVENESS_LABEL_MAP.get(issue_type)


def _issues_to_labels(issues: list[str] | None) -> list[str]:
    """Map issues to final business labels.

    RuleSpecialCharacter and RuleInvisibleChar are candidate triggers. When LLM
    confirms a concrete issue such as title:html_tag, keep the concrete
    business label and suppress the intermediate rule label to avoid duplicate
    output files for the same problem.
    """
    labels: list[str] = []
    normalized_issues = [str(issue or "").strip() for issue in (issues or []) if str(issue or "").strip()]
    has_confirmed_quality_issue = any(
        ":" in issue and _issue_to_label(issue) is not None
        for issue in normalized_issues
    )

    for issue in normalized_issues:
        issue_type = issue.split(":")[-1]
        if has_confirmed_quality_issue and issue_type in {
            "RuleSpecialCharacter",
            "RuleInvisibleChar",
            "RuleMojibake",
        }:
            continue
        label = _issue_to_label(issue)
        if label and label not in labels:
            labels.append(label)
    return labels


def _truncate_for_llm(value: str, max_chars: int = 1000) -> str:
    text = str(value or "")
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "...[truncated]"


def extract_keywords(result: dict[str, Any]) -> list[str]:
    value = result.get("keywords") or result.get("keyword") or result.get("concepts") or []
    if isinstance(value, str):
        return [item.strip() for item in re.split(r"[,;|]", value) if item.strip()]
    if isinstance(value, list):
        keywords: list[str] = []
        for item in value:
            if isinstance(item, dict):
                name = item.get("name") or item.get("display_name") or item.get("keyword")
                if name:
                    keywords.append(str(name))
            elif item not in (None, ""):
                keywords.append(str(item))
        return keywords
    return []


def extract_venue(result: dict[str, Any]) -> str:
    return str(
        result.get("publication_venue_name_unified")
        or result.get("publication_venue_name")
        or result.get("venue")
        or result.get("source")
        or ""
    )


def extract_authors(result: dict[str, Any]) -> list[str]:
    """Extract author names from common search API response shapes."""
    value = result.get("author") or result.get("authors") or []
    if isinstance(value, str):
        return [item.strip() for item in re.split(r"[;|]", value) if item.strip()]
    if isinstance(value, dict):
        value = [value]
    if not isinstance(value, list):
        return []

    authors: list[str] = []
    for item in value:
        if isinstance(item, dict):
            name = item.get("name") or item.get("display_name") or item.get("author_name")
            if name:
                authors.append(str(name).strip())
        elif item not in (None, ""):
            authors.append(str(item).strip())
    return [author for author in authors if author]


@dataclass
class LLMFieldQuality:
    """LLM readability and corruption judgment for one search result."""

    title_score: float = 1.0
    abstract_score: float = 1.0
    keywords_score: float = 1.0
    venue_score: float = 1.0
    author_score: float = 1.0
    issues: list[str] | None = None
    reason: str = ""
    error: str = ""

    def field_score(self, field: str) -> float:
        return {
            "title": self.title_score,
            "abstract": self.abstract_score,
            "keywords": self.keywords_score,
            "venue": self.venue_score,
            "author": self.author_score,
        }.get(field, 1.0)


def _parse_llm_field_quality_response(text: str) -> LLMFieldQuality:
    candidate = _extract_json_object(text)
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError as e:
        return LLMFieldQuality(error=f"JSON parse failed: {e}. Text: {text[:200]}")

    fields = data.get("fields") if isinstance(data, dict) else {}
    if not isinstance(fields, dict):
        return LLMFieldQuality(error=f"Missing fields object. Text: {candidate[:200]}")

    issues: list[str] = []
    scores: dict[str, float] = {}
    reasons: list[str] = []
    for field in ("title", "abstract", "keywords", "venue", "author"):
        field_data = fields.get(field) or {}
        if not isinstance(field_data, dict):
            field_data = {}
        scores[field] = _safe_float(field_data.get("score"), default=1.0)
        for issue in _normalize_issues(field_data.get("issues")):
            issues.append(f"{field}:{issue}")
        reason = str(field_data.get("reason") or "").strip()
        if reason:
            reasons.append(f"{field}: {reason}")

    for issue in _normalize_issues(data.get("overall_issues")):
        issues.append(issue)

    return LLMFieldQuality(
        title_score=scores["title"],
        abstract_score=scores["abstract"],
        keywords_score=scores["keywords"],
        venue_score=scores["venue"],
        author_score=scores["author"],
        issues=issues,
        reason=str(data.get("reason") or "; ".join(reasons))[:500],
    )


@dataclass
class EffectivenessGrade:
    """Structured score for one search result."""

    score: float = 0.0
    title_score: float = 0.0
    abstract_score: float = 0.0
    keywords_score: float = 0.0
    venue_score: float = 0.0
    author_score: float = 0.0
    issues: list[str] | None = None
    llm_quality_reason: str = ""
    llm_quality_error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": round(self.score, 5),
            "title_score": round(self.title_score, 5),
            "abstract_score": round(self.abstract_score, 5),
            "keywords_score": round(self.keywords_score, 5),
            "venue_score": round(self.venue_score, 5),
            "author_score": round(self.author_score, 5),
            "issues": self.issues or [],
            "llm_quality_reason": self.llm_quality_reason,
            "llm_quality_error": self.llm_quality_error,
        }


@dataclass
class EffectivenessSummary:
    mean_score: float = 0.0
    median_score: float = 0.0
    mean_title_score: float = 0.0
    mean_abstract_score: float = 0.0
    mean_keywords_score: float = 0.0
    mean_venue_score: float = 0.0
    mean_author_score: float = 0.0
    graded_pairs: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "effectiveness_mean_score": round(self.mean_score, 5),
            "effectiveness_median_score": round(self.median_score, 5),
            "effectiveness_mean_title_score": round(self.mean_title_score, 5),
            "effectiveness_mean_abstract_score": round(self.mean_abstract_score, 5),
            "effectiveness_mean_keywords_score": round(self.mean_keywords_score, 5),
            "effectiveness_mean_venue_score": round(self.mean_venue_score, 5),
            "effectiveness_mean_author_score": round(self.mean_author_score, 5),
            "effectiveness_graded_pairs": self.graded_pairs,
        }


@Model.llm_register("LLMSearchResultEffectiveness")
class LLMSearchResultEffectiveness:
    """Effectiveness scorer for title, abstract, keywords, and authors.

    Venue text is still scanned for corruption, but venue presence and quality
    belong to the authority metric and do not affect the effectiveness score.
    """

    dynamic_config = EvaluatorLLMArgs()
    default_threshold = 0.15

    def __init__(
        self,
        *,
        model: str | None = None,
        api_key: str | None = None,
        api_url: str | None = None,
        max_tokens: int = 512,
        temperature: float = 0.0,
        timeout: float | None = None,
        enable_llm_quality: bool = False,
    ):
        self.model = model or "gpt-4o"
        self.api_key = api_key
        self.api_url = api_url
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self.enable_llm_quality = enable_llm_quality
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI

            kwargs: dict[str, Any] = {}
            if self.api_key:
                kwargs["api_key"] = self.api_key
            if self.api_url:
                kwargs["base_url"] = self.api_url
            self._client = OpenAI(**kwargs)
        return self._client

    def _build_llm_quality_user_message(
        self,
        *,
        title: str,
        abstract: str,
        keywords: list[str],
        venue: str,
        authors: list[str],
        candidate_fields: set[str] | None = None,
    ) -> str:
        all_fields = {
            "title": title,
            "abstract": abstract,
            "keywords": " | ".join(keywords),
            "venue": venue,
            "author": " | ".join(authors),
        }
        selected = candidate_fields or set(all_fields)
        payload = {
            field: _truncate_for_llm(value)
            for field, value in all_fields.items()
            if field in selected
        }
        return (
            "Evaluate only the supplied fields for readability and corruption. "
            "Omitted fields should not be judged. Return compact JSON.\n\n"
            f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
        )

    def _judge_llm_field_quality(
        self,
        *,
        title: str,
        abstract: str,
        keywords: list[str],
        venue: str,
        authors: list[str],
        candidate_fields: set[str] | None = None,
    ) -> LLMFieldQuality:
        if not self.enable_llm_quality:
            return LLMFieldQuality()
        client = self._get_client()
        last_result = LLMFieldQuality(error="LLM field quality judgment failed")
        for attempt in range(3):
            try:
                completion = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": LLM_FIELD_QUALITY_SYSTEM_PROMPT},
                        {
                            "role": "user",
                            "content": self._build_llm_quality_user_message(
                                title=title,
                                abstract=abstract,
                                keywords=keywords,
                                venue=venue,
                                authors=authors,
                                candidate_fields=candidate_fields,
                            ),
                        },
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    timeout=self.timeout,
                )
                response_text = completion.choices[0].message.content or ""
                last_result = _parse_llm_field_quality_response(response_text)
                if not last_result.error:
                    return last_result
                error: Exception | str = last_result.error
            except Exception as exc:
                error = exc
                last_result = LLMFieldQuality(error=str(exc))

            logger.warning(
                "LLM field quality attempt %s/3 failed for title=%r: %s",
                attempt + 1,
                title,
                error,
            )
            if attempt < 2:
                time.sleep(attempt + 1)
        return last_result

    def grade(
        self,
        *,
        title: str = "",
        abstract: str = "",
        keywords: list[str] | str | None = None,
        venue: str = "",
        authors: list[str] | str | None = None,
        result: dict[str, Any] | None = None,
    ) -> EffectivenessGrade:
        if result is not None:
            title = str(result.get("title") or result.get("display_name") or title or "")
            abstract = str(result.get("abstract") or abstract or "")
            keywords = extract_keywords(result) if keywords is None else keywords
            venue = extract_venue(result) or venue
            authors = extract_authors(result) if authors is None else authors

        keyword_items = (
            [item.strip() for item in re.split(r"[,;|]", keywords) if item.strip()]
            if isinstance(keywords, str)
            else [str(item).strip() for item in (keywords or []) if str(item).strip()]
        )
        author_items = (
            [item.strip() for item in re.split(r"[;|]", authors) if item.strip()]
            if isinstance(authors, str)
            else [str(item).strip() for item in (authors or []) if str(item).strip()]
        )

        title_score = _presence_quality(title)
        abstract_score = _presence_quality(abstract)
        keywords_score = 1.0 if keyword_items else 0.0
        venue_score = _presence_quality(venue)
        author_score = 1.0 if author_items else 0.0

        issues: list[str] = []
        if not str(title or "").strip():
            issues.append("missing_title")
        if not str(abstract or "").strip():
            issues.append("missing_abstract")
        if not keyword_items:
            issues.append("missing_keywords")
        if not author_items:
            issues.append("missing_author")

        field_values = {
            "title": str(title or ""),
            "abstract": str(abstract or ""),
            "keywords": " | ".join(keyword_items),
            "venue": str(venue or ""),
            "author": " | ".join(author_items),
        }
        rule_candidate_issues = {
            field: _rule_abnormal_char_issues(value)
            for field, value in field_values.items()
            if value
        }
        rule_candidate_issues = {
            field: field_issues
            for field, field_issues in rule_candidate_issues.items()
            if field_issues
        }

        llm_quality = LLMFieldQuality()
        if rule_candidate_issues and self.enable_llm_quality:
            llm_quality = self._judge_llm_field_quality(
                title=str(title or ""),
                abstract=str(abstract or ""),
                keywords=keyword_items,
                venue=str(venue or ""),
                authors=author_items,
                candidate_fields=set(rule_candidate_issues),
            )

        def apply_confirmed_field_issue(field: str, score: float) -> float:
            field_rule_issues = rule_candidate_issues.get(field) or []
            if not field_rule_issues:
                return score

            if not self.enable_llm_quality:
                issues.extend(field_rule_issues)
                return min(score, 0.1)

            if llm_quality.error:
                return score

            field_llm_issues = [
                issue for issue in (llm_quality.issues or [])
                if str(issue).startswith(f"{field}:")
            ]
            field_llm_issues = _filter_llm_field_issues(
                field,
                field_values.get(field, ""),
                field_llm_issues,
            )
            llm_field_score = llm_quality.field_score(field)
            if llm_field_score < 1.0 or _has_confirmed_llm_issue(field_llm_issues):
                issues.extend(field_rule_issues)
                issues.extend(field_llm_issues)
                return min(score, llm_field_score)
            return score

        title_score = apply_confirmed_field_issue("title", title_score)
        abstract_score = apply_confirmed_field_issue("abstract", abstract_score)
        keywords_score = apply_confirmed_field_issue("keywords", keywords_score)
        venue_score = apply_confirmed_field_issue("venue", venue_score)
        author_score = apply_confirmed_field_issue("author", author_score)

        if rule_candidate_issues and self.enable_llm_quality and llm_quality.error:
            issues.append("llm_quality_parse_error")

        score = (
            0.30 * title_score
            + 0.50 * abstract_score
            + 0.10 * keywords_score
            + 0.10 * author_score
        )
        return EffectivenessGrade(
            score=_clamp(score),
            title_score=_clamp(title_score),
            abstract_score=_clamp(abstract_score),
            keywords_score=_clamp(keywords_score),
            venue_score=_clamp(venue_score),
            author_score=_clamp(author_score),
            issues=issues,
            llm_quality_reason=llm_quality.reason,
            llm_quality_error=llm_quality.error,
        )

    @classmethod
    def _config_value(cls, name: str, default: Any = None) -> Any:
        return getattr(cls.dynamic_config, name, default)

    @classmethod
    def _build_from_config(cls) -> "LLMSearchResultEffectiveness":
        return cls(
            model=cls.dynamic_config.model,
            api_key=cls.dynamic_config.key,
            api_url=cls.dynamic_config.api_url,
            max_tokens=int(cls._config_value("max_tokens", 512) or 512),
            temperature=float(cls._config_value("temperature", 0.0) or 0.0),
            timeout=cls._config_value("timeout", None),
            enable_llm_quality=bool(cls._config_value("enable_llm_quality", False)),
        )

    @classmethod
    def eval(cls, input_data: Data) -> EvalDetail:
        """Executor entry point: evaluate one flattened search result row."""
        result = getattr(input_data, "search_result", None)
        if not isinstance(result, dict):
            result = input_data.to_dict()

        grader = cls._build_from_config()
        grade = grader.grade(result=result)
        threshold = float(cls._config_value("threshold", cls.default_threshold) or cls.default_threshold)

        labels = _issues_to_labels(grade.issues)

        if grade.score < threshold and "Effectiveness.Error_Effectiveness_Low" not in labels:
            labels.append("Effectiveness.Error_Effectiveness_Low")

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


def aggregate_grades(grades: list[EffectivenessGrade]) -> EffectivenessSummary:
    if not grades:
        return EffectivenessSummary()
    return EffectivenessSummary(
        mean_score=statistics.mean(g.score for g in grades),
        median_score=statistics.median(g.score for g in grades),
        mean_title_score=statistics.mean(g.title_score for g in grades),
        mean_abstract_score=statistics.mean(g.abstract_score for g in grades),
        mean_keywords_score=statistics.mean(g.keywords_score for g in grades),
        mean_venue_score=statistics.mean(g.venue_score for g in grades),
        mean_author_score=statistics.mean(g.author_score for g in grades),
        graded_pairs=len(grades),
    )
