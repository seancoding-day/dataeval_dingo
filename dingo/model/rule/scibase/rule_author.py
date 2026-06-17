import json
import re
from datetime import datetime
from typing import Any, Dict, List

from dingo.config.input_args import EvaluatorRuleArgs
from dingo.io.input import Data
from dingo.io.output.eval_detail import EvalDetail, QualityLabel
from dingo.model.model import Model
from dingo.model.rule.base import BaseRule

URL_RE = re.compile(r"^[Hh][Tt][Tt][Pp][Ss]?://[^/$.?#][\s\S]*$")

ValidationResult = tuple[bool, str]

JSON_LIKE_FIELDS = {
    "affiliations",
    "last_known_institutions",
    "topics",
    "topic_share",
    "x_concepts",
    "sources",
    "counts_by_year",
}


def _ok() -> ValidationResult:
    return False, ""


def _fail(reason: str) -> ValidationResult:
    return True, reason


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _normalize_json_like_field(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    stripped = value.strip()
    if not stripped:
        return value
    if stripped[0] not in ("[", "{"):
        return value
    try:
        return json.loads(stripped)
    except (TypeError, ValueError, json.JSONDecodeError):
        return value


def normalize_record(record: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(record)
    for field in JSON_LIKE_FIELDS:
        if field in normalized:
            normalized[field] = _normalize_json_like_field(normalized.get(field))
    return normalized


def check_id(author_id: Any) -> ValidationResult:
    if author_id is None:
        return _fail("value is null")
    if not isinstance(author_id, str):
        return _fail("value must be a string")
    if author_id == "":
        return _fail("value must be a non-empty string")
    if not URL_RE.fullmatch(author_id):
        return _fail("value is not a valid URL")
    return _ok()


def check_orcid(orcid: Any) -> ValidationResult:
    if orcid is None:
        return _fail("value is null")
    if not isinstance(orcid, str):
        return _fail("value must be a string")
    if orcid == "":
        return _ok()
    if not URL_RE.fullmatch(orcid):
        return _fail("value is not a valid URL")
    return _ok()


def check_affiliations(affiliations: Any) -> ValidationResult:
    if affiliations is None:
        return _fail("value is null")
    if not isinstance(affiliations, list):
        return _fail("value must be a list")
    for idx, item in enumerate(affiliations):
        if not isinstance(item, dict):
            return _fail(f"item[{idx}] must be an object")
        institution = item.get("institution")
        years = item.get("years")
        if not isinstance(institution, dict):
            return _fail(f"item[{idx}].institution must be an object")
        if not isinstance(years, list):
            return _fail(f"item[{idx}].years must be a list")
        for year_idx, year in enumerate(years):
            if not _is_int(year):
                return _fail(f"item[{idx}].years[{year_idx}] must be an integer")
    return _ok()


def check_last_known_institutions(last_known_institutions: Any) -> ValidationResult:
    if last_known_institutions is None:
        return _fail("value is null")
    if not isinstance(last_known_institutions, list):
        return _fail("value must be a list")
    required_keys = {"id", "ror", "display_name", "country_code", "type", "lineage"}
    for idx, item in enumerate(last_known_institutions):
        if not isinstance(item, dict):
            return _fail(f"item[{idx}] must be an object")
        missing = required_keys - set(item.keys())
        if missing:
            return _fail(f"item[{idx}] missing keys {sorted(missing)}")
    return _ok()


def _check_topic_item(item: Any, idx: int, field_name: str) -> ValidationResult:
    if not isinstance(item, dict):
        return _fail(f"{field_name}[{idx}] must be an object")
    required_keys = {"id", "display_name", "count", "subfield", "field", "domain"}
    missing = required_keys - set(item.keys())
    if missing:
        return _fail(f"{field_name}[{idx}] missing keys {sorted(missing)}")
    return _ok()


def check_topics(topics: Any) -> ValidationResult:
    if topics is None:
        return _fail("value is null")
    if not isinstance(topics, list):
        return _fail("value must be a list")
    for idx, item in enumerate(topics):
        invalid, reason = _check_topic_item(item, idx, "topics")
        if invalid:
            return _fail(reason)
    return _ok()


def check_topic_share(topic_share: Any) -> ValidationResult:
    if topic_share is None:
        return _fail("value is null")
    if not isinstance(topic_share, list):
        return _fail("value must be a list")
    for idx, item in enumerate(topic_share):
        if not isinstance(item, dict):
            return _fail(f"topic_share[{idx}] must be an object")
        required_keys = {"id", "display_name", "value", "subfield", "field", "domain"}
        missing = required_keys - set(item.keys())
        if missing:
            return _fail(f"topic_share[{idx}] missing keys {sorted(missing)}")
    return _ok()


def check_x_concepts(x_concepts: Any) -> ValidationResult:
    if x_concepts is None:
        return _fail("value is null")
    if not isinstance(x_concepts, list):
        return _fail("value must be a list")
    required_keys = {"id", "wikidata", "display_name", "level", "score", "count"}
    for idx, item in enumerate(x_concepts):
        if not isinstance(item, dict):
            return _fail(f"x_concepts[{idx}] must be an object")
        missing = required_keys - set(item.keys())
        if missing:
            return _fail(f"x_concepts[{idx}] missing keys {sorted(missing)}")
    return _ok()


def check_sources(sources: Any) -> ValidationResult:
    if sources is None:
        return _fail("value is null")
    if not isinstance(sources, list):
        return _fail("value must be a list")
    required_keys = {
        "id",
        "display_name",
        "issn_l",
        "issn",
        "is_oa",
        "is_in_doaj",
        "host_organization",
        "type",
    }
    for idx, item in enumerate(sources):
        if not isinstance(item, dict):
            return _fail(f"sources[{idx}] must be an object")
        missing = required_keys - set(item.keys())
        if missing:
            return _fail(f"sources[{idx}] missing keys {sorted(missing)}")
    return _ok()


def check_counts_by_year(counts_by_year: Any) -> ValidationResult:
    if counts_by_year is None:
        return _fail("value is null")
    if not isinstance(counts_by_year, list):
        return _fail("value must be a list")
    required_keys = {"year", "works_count", "oa_works_count", "cited_by_count"}
    for idx, item in enumerate(counts_by_year):
        if not isinstance(item, dict):
            return _fail(f"counts_by_year[{idx}] must be an object")
        missing = required_keys - set(item.keys())
        if missing:
            return _fail(f"counts_by_year[{idx}] missing keys {sorted(missing)}")
        for key in ("year", "works_count", "oa_works_count", "cited_by_count"):
            if not _is_int(item.get(key)):
                return _fail(f"counts_by_year[{idx}].{key} must be an integer")
    return _ok()


def check_works_api_url(works_api_url: Any) -> ValidationResult:
    if works_api_url is None:
        return _fail("value is null")
    if not isinstance(works_api_url, str):
        return _fail("value must be a string")
    if works_api_url == "":
        return _fail("value must be a non-empty string")
    if not URL_RE.fullmatch(works_api_url):
        return _fail("value is not a valid URL")
    return _ok()


def _check_date_yyyy_mm_dd(value: Any, field_name: str) -> ValidationResult:
    if value is None:
        return _fail("value is null")
    if not isinstance(value, str):
        return _fail("value must be a string")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return _fail("value must match YYYY-MM-DD")
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return _fail("value is not a valid calendar date")
    return _ok()


def check_updated_date(updated_date: Any) -> ValidationResult:
    return _check_date_yyyy_mm_dd(updated_date, "updated_date")


def check_created_date(created_date: Any) -> ValidationResult:
    return _check_date_yyyy_mm_dd(created_date, "created_date")


FIELD_VALIDATORS = {
    "id": lambda record: check_id(record.get("id")),
    "orcid": lambda record: check_orcid(record.get("orcid")),
    "affiliations": lambda record: check_affiliations(record.get("affiliations")),
    "last_known_institutions": lambda record: check_last_known_institutions(
        record.get("last_known_institutions")
    ),
    "topics": lambda record: check_topics(record.get("topics")),
    "topic_share": lambda record: check_topic_share(record.get("topic_share")),
    "x_concepts": lambda record: check_x_concepts(record.get("x_concepts")),
    "sources": lambda record: check_sources(record.get("sources")),
    "counts_by_year": lambda record: check_counts_by_year(record.get("counts_by_year")),
    "works_api_url": lambda record: check_works_api_url(record.get("works_api_url")),
    "updated_date": lambda record: check_updated_date(record.get("updated_date")),
    "created_date": lambda record: check_created_date(record.get("created_date")),
}


@Model.rule_register("QUALITY_BAD_EFFECTIVENESS", ["xinghe", "quanliang"])
class RuleAuthorFieldValidation(BaseRule):
    _metric_info = {
        "category": "Rule-Based Metadata Quality Metrics",
        "quality_dimension": "EFFECTIVENESS",
        "metric_name": "RuleAuthorFieldValidation",
        "description": "Validate OpenAlex author fields and report invalid fields",
        "paper_title": "",
        "paper_url": "",
        "paper_authors": "",
        "evaluation_results": "",
    }

    _required_fields = []
    dynamic_config = EvaluatorRuleArgs(key_list=list(FIELD_VALIDATORS.keys()))

    def eval(self, input_data: Data) -> EvalDetail:
        res = EvalDetail(metric=self.__class__.__name__)
        normalized = normalize_record(input_data.to_dict())
        selected_fields = self.dynamic_config.key_list or []
        bad_fields: List[str] = []
        reasons: List[str] = []

        for field in selected_fields:
            if field not in FIELD_VALIDATORS:
                bad_fields.append(field)
                reasons.append(f"{field}: unsupported field")
                continue
            if field not in normalized:
                bad_fields.append(field)
                reasons.append(f"{field}: missing field")
                continue
            invalid, detail_reason = FIELD_VALIDATORS[field](normalized)
            if invalid:
                bad_fields.append(field)
                reasons.append(f"{field}: {detail_reason or 'failed field validation'}")

        if bad_fields:
            res.status = True
            res.label = bad_fields
            res.reason = reasons
        else:
            res.label = [QualityLabel.QUALITY_GOOD]
        return res
