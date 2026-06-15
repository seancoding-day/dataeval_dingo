import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from dingo.config.input_args import EvaluatorRuleArgs
from dingo.io.input import Data, RequiredField
from dingo.io.output.eval_detail import EvalDetail, QualityLabel
from dingo.model.model import Model
from dingo.model.rule.base import BaseRule

URL_RE = re.compile(r"^[Hh][Tt][Tt][Pp][Ss]?://[^/$.?#][\s\S]*$")
DOI_RE = re.compile(r"^10\.\d{4,9}/([^A-Z\s\|]*)$")
INVISIBLE_RE = re.compile(r"[\u2000-\u200F\u202F\u205F\u3000\uFEFF\u00A0\u2060-\u206F\xa0]")
PAGE_RANGE_RE = re.compile(r"^\d+-\d+$")
ISSN_RE = re.compile(r"^\d{4}-\d{3}[\dX]$")
AUTHOR_SEP_RE = re.compile(r"[|;；]")
ORCID_URL_RE = re.compile(r"^[Hh][Tt][Tt][Pp][Ss]?://orcid\.org/\d{4}-\d{4}-\d{4}-\d{3}[\dXx]$")

OA_BOOL_VALUES = {"true", "false", "unknown"}
METADATA_TYPE_VALUES = {"paper", "ebook"}
OA_STATUS_VALUES = {"diamond", "gold", "green", "hybrid", "bronze", "closed", ""}
LOC_TYPE_VALUES = {"download", "reader", "display", ""}
JSON_LIST_FIELDS = {
    "isbns",
    "author",
    "contributors",
    "locations",
    "access_oa_url",
    "publication_venue_issn",
    "references",
    "related_works",
    "citations",
    "supplementary_material",
}
LICENSE_VALUES = {
    "cc-by",
    "cc-by-nc",
    "cc-by-sa",
    "cc-by-nd",
    "cc-by-nc-sa",
    "cc-by-nc-nd",
    "other-oa",
    "cc0",
    "",
    "public-domain",
    "publisher-specific-oa",
    "publisher-specific",
    "wiley-specific",
    "elsevier-specific",
    "oup-specific",
    "acs-specific",
    "rsc-specific",
    "iop-specific",
    "unspecified-oa",
    "implied-oa",
    "nonexclusive-distrib",
    "gpl-v1",
    "gpl-v2",
    "gpl-v3",
    "mit",
    "ogl-c",
    "pd",
}
ACCESS_LICENSE_VALUES = set(LICENSE_VALUES)
GRADE_CLASS_VALUES = {"k12", "higher-edu", "vocational-edu", "other", ""}
GRADE_VALUES = {"小学", "初中", "高中", ""}
XINGHE_REPOSITORY_MODEL_VERSION_MAP = {
    "mineru": {"1.3.1", "2", "2.5"},
    "llm-web-kit": {"4.1.1"},
}
XINGHE_REPOSITORY_MODEL_NAME_VALUES = set(XINGHE_REPOSITORY_MODEL_VERSION_MAP.keys())
XINGHE_REPOSITORY_MODEL_VERSION_VALUES = {
    version
    for versions in XINGHE_REPOSITORY_MODEL_VERSION_MAP.values()
    for version in versions
}

_DEFAULT_LANGUAGE_VALUES = {"zh", "en", "ja", "de", "fr", "es", "ru", "ko", "ar"}
ASSETS_DIR = Path(__file__).resolve().parent / "assets"


def _load_language_allowed_values() -> set[str]:
    base = ASSETS_DIR / "to_iso-639.json"
    if not base.exists():
        return set(_DEFAULT_LANGUAGE_VALUES)
    try:
        with base.open("r", encoding="utf-8") as f:
            values = json.load(f)
        if isinstance(values, dict):
            return set(str(v) for v in values.values() if isinstance(v, str))
    except (TypeError, ValueError, json.JSONDecodeError):
        return set(_DEFAULT_LANGUAGE_VALUES)
    return set(_DEFAULT_LANGUAGE_VALUES)


def _load_journal_mapping() -> Dict[str, str]:
    csv_path = ASSETS_DIR / "journal_name_mapping_execute_20260512.csv"
    if not csv_path.exists():
        return {}
    # Lazy import to avoid top-level optional dependency / heavier import.
    import csv

    mapping: Dict[str, str] = {}
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            source_name = row.get("source_journal_name")
            target_name = row.get("target_journal_name")
            if source_name and target_name:
                mapping[source_name] = target_name
    return mapping


LANGUAGE_ALLOWED_VALUES = _load_language_allowed_values()
JOURNAL_NAME_MAPPING = _load_journal_mapping()


def _valid_isbn10(code: str) -> bool:
    if not re.fullmatch(r"\d{9}[\dXx]", code):
        return False
    total = sum((10 - idx) * int(ch) for idx, ch in enumerate(code[:9]))
    check = code[9].upper()
    check_value = 10 if check == "X" else int(check)
    total += check_value
    return total % 11 == 0


def _valid_isbn13(code: str) -> bool:
    if not re.fullmatch(r"\d{13}", code):
        return False
    if not (code.startswith("978") or code.startswith("979")):
        return False
    total = sum(int(ch) * (1 if idx % 2 == 0 else 3) for idx, ch in enumerate(code))
    return total % 10 == 0


def _valid_issn(code: str) -> bool:
    if not ISSN_RE.fullmatch(code):
        return False
    digits = code.replace("-", "")
    total = sum(int(ch) * (8 - idx) for idx, ch in enumerate(digits[:7]))
    calculated = (11 - (total % 11)) % 11
    expected = "X" if calculated == 10 else str(calculated)
    return digits[7].upper() == expected


def check_metadata_type(metadata_type: Any) -> bool:
    if metadata_type is None:
        return True
    if not isinstance(metadata_type, str):
        return True
    if metadata_type.strip() == "":
        return True
    return metadata_type not in METADATA_TYPE_VALUES


def check_doi(doi: Any, metadata_type: Any) -> bool:
    if metadata_type not in METADATA_TYPE_VALUES:
        return False
    required = metadata_type == "paper"
    if doi is None:
        return required
    if not isinstance(doi, str):
        return True
    if doi == "":
        return required
    if doi != doi.lower():
        return True
    if "https://doi.org/" in doi.lower():
        return True
    if doi.startswith("10.0000/"):
        return True
    return not bool(DOI_RE.fullmatch(doi))


def check_isbns(isbns: Any, metadata_type: Any) -> bool:
    if metadata_type not in METADATA_TYPE_VALUES:
        return False
    required = metadata_type == "ebook"
    if isbns is None:
        return required
    if not (isinstance(isbns, list) and all(isinstance(x, str) for x in isbns)):
        return True
    if len(isbns) == 0:
        return required
    for item in isbns:
        if not (_valid_isbn10(item) or _valid_isbn13(item)):
            return True
    return False


def check_isbn13(isbn13: Any, metadata_type: Any) -> bool:
    if metadata_type not in METADATA_TYPE_VALUES:
        return False
    required = metadata_type == "ebook"
    if isbn13 is None:
        return required
    if not isinstance(isbn13, str):
        return True
    if isbn13 == "":
        return required
    return not _valid_isbn13(isbn13)


def check_title(title: Any) -> bool:
    if title is None:
        return True
    if not isinstance(title, str):
        return True
    if title == "":
        return False
    return bool(INVISIBLE_RE.search(title))


def check_abstract(abstract: Any) -> bool:
    if abstract is None:
        return True
    if not isinstance(abstract, str):
        return True
    if abstract == "":
        return False
    return bool(INVISIBLE_RE.search(abstract))


def check_language(language: Any) -> bool:
    if language is None:
        return True
    if not isinstance(language, str):
        return True
    if language == "":
        return False
    if not LANGUAGE_ALLOWED_VALUES:
        return False
    return language not in LANGUAGE_ALLOWED_VALUES


def check_author(author: Any) -> bool:
    if author is None:
        return True
    if not isinstance(author, list):
        return True
    if len(author) == 0:
        return False
    for item in author:
        if not isinstance(item, dict):
            return True
        if set(item.keys()) != {"name", "orcid"}:
            return True
        name = item.get("name")
        orcid = item.get("orcid")
        if not isinstance(name, str):
            return True
        if name == "":
            return True
        if AUTHOR_SEP_RE.search(name):
            return True
        if not isinstance(orcid, str):
            return True
        if orcid != "" and not ORCID_URL_RE.fullmatch(orcid):
            return True
    return False


def check_contributors(contributors: Any) -> bool:
    if contributors is None:
        return True
    if not (isinstance(contributors, list) and all(isinstance(x, str) for x in contributors)):
        return True
    if len(contributors) == 0:
        return False
    for item in contributors:
        if AUTHOR_SEP_RE.search(item):
            return True
    return False


def check_locations(locations: Any) -> bool:
    if locations is None:
        return True
    if not isinstance(locations, list):
        return True
    if len(locations) == 0:
        return False
    for item in locations:
        if not isinstance(item, dict):
            return True
        for key in ("type", "url", "license", "is_oa"):
            if key not in item:
                return True
        if item["type"] not in LOC_TYPE_VALUES:
            return True
        if not (isinstance(item["url"], str) and URL_RE.fullmatch(item["url"])):
            return True
        if item["license"] not in LICENSE_VALUES:
            return True
        if item["is_oa"] not in OA_BOOL_VALUES:
            return True
    return False


def check_access_is_oa(access_is_oa: Any, metadata_type: Any) -> bool:
    if metadata_type not in METADATA_TYPE_VALUES:
        return False
    required = metadata_type == "paper"
    if access_is_oa is None:
        return required
    if not isinstance(access_is_oa, str):
        return True
    if access_is_oa == "":
        return required
    return access_is_oa not in OA_BOOL_VALUES


def check_access_oa_status(access_oa_status: Any) -> bool:
    if access_oa_status is None:
        return True
    if not isinstance(access_oa_status, str):
        return True
    return access_oa_status not in OA_STATUS_VALUES


def check_access_oa_url(access_oa_url: Any) -> bool:
    if access_oa_url is None:
        return True
    if not (isinstance(access_oa_url, list) and all(isinstance(x, str) for x in access_oa_url)):
        return True
    if len(access_oa_url) == 0:
        return False
    return any(not bool(URL_RE.fullmatch(item)) for item in access_oa_url)


def check_access_license(access_license: Any) -> bool:
    if access_license is None:
        return True
    if not isinstance(access_license, str):
        return True
    if access_license == "":
        return False
    return access_license not in ACCESS_LICENSE_VALUES


def check_publication_published_date(publication_published_date: Any) -> bool:
    if publication_published_date is None:
        return True
    if not isinstance(publication_published_date, str):
        return True
    if publication_published_date == "":
        return False
    if not bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", publication_published_date)):
        return True
    try:
        datetime.strptime(publication_published_date, "%Y-%m-%d")
        return False
    except ValueError:
        return True


def check_publication_published_year(publication_published_year: Any) -> bool:
    if publication_published_year is None:
        return False
    if not isinstance(publication_published_year, int) or isinstance(publication_published_year, bool):
        return True
    return not (0 < publication_published_year < 2100)


def check_publication_venue_issn(publication_venue_issn: Any) -> bool:
    if publication_venue_issn is None:
        return True
    if not (isinstance(publication_venue_issn, list) and all(isinstance(x, str) for x in publication_venue_issn)):
        return True
    if len(publication_venue_issn) == 0:
        return False
    for item in publication_venue_issn:
        if not _valid_issn(item):
            return True
    return False


def check_publication_venue_biblio_volume(publication_venue_biblio_volume: Any) -> bool:
    if publication_venue_biblio_volume is None:
        return True
    if not isinstance(publication_venue_biblio_volume, str):
        return True
    if publication_venue_biblio_volume == "":
        return False
    try:
        int(publication_venue_biblio_volume)
        return False
    except (TypeError, ValueError):
        return True


def check_publication_venue_biblio_issue(publication_venue_biblio_issue: Any) -> bool:
    if publication_venue_biblio_issue is None:
        return True
    if not isinstance(publication_venue_biblio_issue, str):
        return True
    if publication_venue_biblio_issue == "":
        return False
    try:
        int(publication_venue_biblio_issue)
        return False
    except (TypeError, ValueError):
        return True


def check_publication_venue_biblio_pages(publication_venue_biblio_pages: Any) -> bool:
    if publication_venue_biblio_pages is None:
        return True
    if not isinstance(publication_venue_biblio_pages, str):
        return True
    if publication_venue_biblio_pages == "":
        return False
    if not PAGE_RANGE_RE.fullmatch(publication_venue_biblio_pages):
        return True
    start, end = [int(x.strip()) for x in publication_venue_biblio_pages.split("-")]
    return start <= 0 or end <= 0 or start > end


def check_publication_pages(publication_pages: Any) -> bool:
    if publication_pages is None:
        return False
    if not isinstance(publication_pages, int) or isinstance(publication_pages, bool):
        return True
    return publication_pages <= 0


def check_publication_venue_name_unified(
    publication_venue_name_unified: Any, publication_venue_name: Any
) -> bool:
    if publication_venue_name_unified is None:
        return True
    if not isinstance(publication_venue_name_unified, str):
        return True
    if publication_venue_name is not None and not isinstance(publication_venue_name, str):
        return True
    expected_target = None
    if isinstance(publication_venue_name, str) and publication_venue_name != "":
        expected_target = JOURNAL_NAME_MAPPING.get(publication_venue_name, publication_venue_name)
    if publication_venue_name_unified == "":
        return False
    if expected_target is None:
        return True
    return publication_venue_name_unified != expected_target


def check_grade_class(grade_class: Any) -> bool:
    if grade_class is None:
        return True
    if not isinstance(grade_class, str):
        return True
    if grade_class == "":
        return False
    return grade_class not in GRADE_CLASS_VALUES


def check_grade(grade: Any, grade_class: Any) -> bool:
    if grade is None:
        return True
    if not isinstance(grade, str):
        return True
    if grade_class is not None and not isinstance(grade_class, str):
        return True
    if grade == "":
        return False
    if grade not in GRADE_VALUES:
        return True
    if grade_class != "k12" and grade != "":
        return True
    return False


def _check_id_type_id_title_items(items: Any) -> bool:
    if items is None:
        return True
    if not isinstance(items, list):
        return True
    if len(items) == 0:
        return False
    required_keys = {"id_type", "id", "title"}
    for item in items:
        if not isinstance(item, dict):
            return True
        if set(item.keys()) != required_keys:
            return True
        id_type = item.get("id_type")
        citation_id = item.get("id")
        title = item.get("title")
        if not isinstance(id_type, str) or id_type == "":
            return True
        if check_title(title):
            return True
        if id_type == "doi":
            if check_doi(citation_id, "paper"):
                return True
        elif not isinstance(citation_id, str) or citation_id == "":
            return True
    return False


def check_references(references: Any) -> bool:
    return _check_id_type_id_title_items(references)


def check_related_works(related_works: Any) -> bool:
    return _check_id_type_id_title_items(related_works)


def check_citations(citations: Any) -> bool:
    return _check_id_type_id_title_items(citations)


def check_supplementary_material(supplementary_material: Any) -> bool:
    if supplementary_material is None:
        return True
    if not isinstance(supplementary_material, list):
        return True
    if len(supplementary_material) == 0:
        return False
    required_keys = {
        "supplementary_material_name",
        "supplementary_material_url",
        "supplementary_material_path",
    }
    for item in supplementary_material:
        if not isinstance(item, dict):
            return True
        if set(item.keys()) != required_keys:
            return True
        if not all(isinstance(item.get(key), str) for key in required_keys):
            return True
    return False


def check_cited_by_api_url(cited_by_api_url: Any) -> bool:
    if cited_by_api_url is None:
        return True
    if not isinstance(cited_by_api_url, str):
        return True
    if cited_by_api_url == "":
        return False
    return not bool(URL_RE.fullmatch(cited_by_api_url))


def check_access_xinghe_repository_sha256(
    access_xinghe_repository_sha256: Any, access_xinghe_repository_has_fulltext: Any
) -> bool:
    if access_xinghe_repository_sha256 is None:
        return True
    if not isinstance(access_xinghe_repository_has_fulltext, bool):
        return True
    has_fulltext = access_xinghe_repository_has_fulltext
    if isinstance(access_xinghe_repository_sha256, str):
        if not has_fulltext:
            return False
        return access_xinghe_repository_sha256 == ""
    if not (
        isinstance(access_xinghe_repository_sha256, list)
        and all(isinstance(x, str) for x in access_xinghe_repository_sha256)
    ):
        return True
    if not has_fulltext:
        return False
    return len(access_xinghe_repository_sha256) == 0


def check_access_xinghe_repository_origin_path(
    access_xinghe_repository_origin_path: Any, access_xinghe_repository_has_fulltext: Any
) -> bool:
    if not isinstance(access_xinghe_repository_origin_path, str):
        return True
    if not isinstance(access_xinghe_repository_has_fulltext, bool):
        return True
    if not access_xinghe_repository_has_fulltext:
        return False
    return access_xinghe_repository_origin_path.strip() == ""


def check_access_xinghe_repository_model_name(
    access_xinghe_repository_model_name: Any, access_xinghe_repository_process_status: Any
) -> bool:
    if not isinstance(access_xinghe_repository_model_name, str):
        return True
    if access_xinghe_repository_model_name == "":
        return access_xinghe_repository_process_status in (1, "1")
    return access_xinghe_repository_model_name not in XINGHE_REPOSITORY_MODEL_NAME_VALUES


def check_access_xinghe_repository_model_version(
    access_xinghe_repository_model_version: Any,
    access_xinghe_repository_model_name: Any,
    access_xinghe_repository_process_status: Any,
) -> bool:
    if not isinstance(access_xinghe_repository_model_version, str):
        return True
    if access_xinghe_repository_model_version == "":
        if access_xinghe_repository_process_status in (1, "1"):
            return True
        if (
            isinstance(access_xinghe_repository_model_name, str)
            and access_xinghe_repository_model_name in XINGHE_REPOSITORY_MODEL_NAME_VALUES
            and "" not in XINGHE_REPOSITORY_MODEL_VERSION_MAP[access_xinghe_repository_model_name]
        ):
            return True
        return False
    if access_xinghe_repository_model_version not in XINGHE_REPOSITORY_MODEL_VERSION_VALUES:
        return True
    if (
        isinstance(access_xinghe_repository_model_name, str)
        and access_xinghe_repository_model_name in XINGHE_REPOSITORY_MODEL_NAME_VALUES
    ):
        return (
            access_xinghe_repository_model_version
            not in XINGHE_REPOSITORY_MODEL_VERSION_MAP[access_xinghe_repository_model_name]
        )
    return False


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
        cleaned = stripped.replace("\r", " ").replace("\n", " ").replace("\t", " ")
        cleaned = "".join(ch if ord(ch) >= 32 else " " for ch in cleaned)
        invalid_escape_re = re.compile(r'\\(?!["\\/bfnrtu])')
        for _ in range(10):
            next_cleaned = invalid_escape_re.sub(r"\\\\", cleaned)
            if next_cleaned == cleaned:
                break
            cleaned = next_cleaned
        try:
            return json.loads(cleaned)
        except (TypeError, ValueError, json.JSONDecodeError):
            return value


def _normalize_bool_field(value: Any) -> Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        if value in (0, 1):
            return bool(value)
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ("1", "true"):
            return True
        if lowered in ("0", "false"):
            return False
    return value


def normalize_record(record: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(record)
    for field in JSON_LIST_FIELDS:
        if field in normalized:
            normalized[field] = _normalize_json_like_field(normalized.get(field))
    normalized["access_xinghe_repository_has_fulltext"] = _normalize_bool_field(
        normalized.get("access_xinghe_repository_has_fulltext")
    )
    return normalized


FIELD_VALIDATORS = {
    "metadata_type": lambda record: check_metadata_type(record.get("metadata_type")),
    "doi": lambda record: check_doi(record.get("doi"), record.get("metadata_type")),
    "isbns": lambda record: check_isbns(record.get("isbns"), record.get("metadata_type")),
    "isbn13": lambda record: check_isbn13(record.get("isbn13"), record.get("metadata_type")),
    "title": lambda record: check_title(record.get("title")),
    "abstract": lambda record: check_abstract(record.get("abstract")),
    "language": lambda record: check_language(record.get("language")),
    "author": lambda record: check_author(record.get("author")),
    "contributors": lambda record: check_contributors(record.get("contributors")),
    "locations": lambda record: check_locations(record.get("locations")),
    "access_is_oa": lambda record: check_access_is_oa(record.get("access_is_oa"), record.get("metadata_type")),
    "access_oa_status": lambda record: check_access_oa_status(record.get("access_oa_status")),
    "access_oa_url": lambda record: check_access_oa_url(record.get("access_oa_url")),
    "access_license": lambda record: check_access_license(record.get("access_license")),
    "publication_published_date": lambda record: check_publication_published_date(
        record.get("publication_published_date")
    ),
    "publication_published_year": lambda record: check_publication_published_year(
        record.get("publication_published_year")
    ),
    "publication_venue_issn": lambda record: check_publication_venue_issn(record.get("publication_venue_issn")),
    "publication_venue_biblio_volume": lambda record: check_publication_venue_biblio_volume(
        record.get("publication_venue_biblio_volume")
    ),
    "publication_venue_biblio_issue": lambda record: check_publication_venue_biblio_issue(
        record.get("publication_venue_biblio_issue")
    ),
    "publication_venue_biblio_pages": lambda record: check_publication_venue_biblio_pages(
        record.get("publication_venue_biblio_pages")
    ),
    "publication_pages": lambda record: check_publication_pages(record.get("publication_pages")),
    "publication_venue_name_unified": lambda record: check_publication_venue_name_unified(
        record.get("publication_venue_name_unified"),
        record.get("publication_venue_name"),
    ),
    "grade_class": lambda record: check_grade_class(record.get("grade_class")),
    "grade": lambda record: check_grade(record.get("grade"), record.get("grade_class")),
    "references": lambda record: check_references(record.get("references")),
    "related_works": lambda record: check_related_works(record.get("related_works")),
    "citations": lambda record: check_citations(record.get("citations")),
    "supplementary_material": lambda record: check_supplementary_material(
        record.get("supplementary_material")
    ),
    "cited_by_api_url": lambda record: check_cited_by_api_url(record.get("cited_by_api_url")),
    "access_xinghe_repository_sha256": lambda record: check_access_xinghe_repository_sha256(
        record.get("access_xinghe_repository_sha256"),
        record.get("access_xinghe_repository_has_fulltext"),
    ),
    "access_xinghe_repository_origin_path": lambda record: check_access_xinghe_repository_origin_path(
        record.get("access_xinghe_repository_origin_path"),
        record.get("access_xinghe_repository_has_fulltext"),
    ),
    "access_xinghe_repository_model_name": lambda record: check_access_xinghe_repository_model_name(
        record.get("access_xinghe_repository_model_name"),
        record.get("access_xinghe_repository_process_status"),
    ),
    "access_xinghe_repository_model_version": lambda record: check_access_xinghe_repository_model_version(
        record.get("access_xinghe_repository_model_version"),
        record.get("access_xinghe_repository_model_name"),
        record.get("access_xinghe_repository_process_status"),
    ),
}


@Model.rule_register("QUALITY_BAD_EFFECTIVENESS", ["xinghe", "quanliang"])
class RuleQuanliangFieldValidation(BaseRule):
    _metric_info = {
        "category": "Rule-Based Metadata Quality Metrics",
        "quality_dimension": "EFFECTIVENESS",
        "metric_name": "RuleQuanliangFieldValidation",
        "description": "Validate Quanliang metadata fields and report invalid fields",
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
                reasons.append("unsupported field")
                continue
            if field not in normalized:
                bad_fields.append(field)
                reasons.append("missing field")
                continue
            if FIELD_VALIDATORS[field](normalized):
                bad_fields.append(field)
                reasons.append(f"{field} invalid")

        if bad_fields:
            res.status = True
            res.label = bad_fields
            res.reason = reasons
        else:
            res.label = [QualityLabel.QUALITY_GOOD]
        return res
