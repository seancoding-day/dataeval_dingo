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
    "societies",
    "topics",
    "topic_share",
    "counts_by_year",
}


def _ok() -> ValidationResult:
    return False, ""


def _fail(reason: str) -> ValidationResult:
    return True, reason


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


def check_id(source_id: Any) -> ValidationResult:
    if source_id is None:
        return _fail("value is null")
    if not isinstance(source_id, str):
        return _fail("value must be a string")
    if source_id == "":
        return _fail("value must be a non-empty string")
    if not URL_RE.fullmatch(source_id):
        return _fail("value is not a valid URL")
    return _ok()


def check_host_organization(host_organization: Any) -> ValidationResult:
    if host_organization is None:
        return _fail("value is null")
    if not isinstance(host_organization, str):
        return _fail("value must be a string")
    if host_organization == "":
        return _ok()
    if not URL_RE.fullmatch(host_organization):
        return _fail("value is not a valid URL")
    return _ok()


def check_societies(societies: Any) -> ValidationResult:
    if societies is None:
        return _fail("value is null")
    if not isinstance(societies, list):
        return _fail("value must be a list")
    required_keys = {"url", "organization"}
    for idx, item in enumerate(societies):
        if not isinstance(item, dict):
            return _fail(f"societies[{idx}] must be an object")
        missing = required_keys - set(item.keys())
        if missing:
            return _fail(f"societies[{idx}] missing keys {sorted(missing)}")
    return _ok()


def check_topics(topics: Any) -> ValidationResult:
    if topics is None:
        return _fail("value is null")
    if not isinstance(topics, list):
        return _fail("value must be a list")
    required_keys = {"id", "display_name", "count", "subfield", "field", "domain"}
    for idx, item in enumerate(topics):
        if not isinstance(item, dict):
            return _fail(f"topics[{idx}] must be an object")
        missing = required_keys - set(item.keys())
        if missing:
            return _fail(f"topics[{idx}] missing keys {sorted(missing)}")
    return _ok()


def check_topic_share(topic_share: Any) -> ValidationResult:
    if topic_share is None:
        return _fail("value is null")
    if not isinstance(topic_share, list):
        return _fail("value must be a list")
    required_keys = {"id", "display_name", "value", "subfield", "field", "domain"}
    for idx, item in enumerate(topic_share):
        if not isinstance(item, dict):
            return _fail(f"topic_share[{idx}] must be an object")
        missing = required_keys - set(item.keys())
        if missing:
            return _fail(f"topic_share[{idx}] missing keys {sorted(missing)}")
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


def _check_date_yyyy_mm_dd(value: Any) -> ValidationResult:
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
    return _check_date_yyyy_mm_dd(updated_date)


def check_created_date(created_date: Any) -> ValidationResult:
    if created_date == "":
        return _ok()
    return _check_date_yyyy_mm_dd(created_date)


FIELD_VALIDATORS = {
    "id": lambda record: check_id(record.get("id")),
    "host_organization": lambda record: check_host_organization(record.get("host_organization")),
    "societies": lambda record: check_societies(record.get("societies")),
    "topics": lambda record: check_topics(record.get("topics")),
    "topic_share": lambda record: check_topic_share(record.get("topic_share")),
    "counts_by_year": lambda record: check_counts_by_year(record.get("counts_by_year")),
    "works_api_url": lambda record: check_works_api_url(record.get("works_api_url")),
    "updated_date": lambda record: check_updated_date(record.get("updated_date")),
    "created_date": lambda record: check_created_date(record.get("created_date")),
}


@Model.rule_register("QUALITY_BAD_EFFECTIVENESS", ["xinghe", "quanliang"])
class RuleSourceFieldValidation(BaseRule):
    _metric_info = {
        "category": "Rule-Based Metadata Quality Metrics",
        "quality_dimension": "EFFECTIVENESS",
        "metric_name": "RuleSourceFieldValidation",
        "description": "Validate OpenAlex source fields and report invalid fields",
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
