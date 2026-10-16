import json
import re
from typing import Any, List

from dingo.config.input_args import EvaluatorRuleArgs
from dingo.io.input import Data
from dingo.io.output.eval_detail import EvalDetail, QualityLabel
from dingo.model.model import Model
from dingo.model.rule.base import BaseRule

MAX_CLAIMS_LENGTH = 1_000_000
IPC_SUBCLASS_RE = re.compile(r"^[A-H](?:0[1-9]|[1-9][0-9])[A-Z]$")
IPC_CODE_RE = re.compile(
    r"^(?P<section>[A-H])"
    r"(?P<class>0[1-9]|[1-9][0-9])"
    r"(?P<subclass>[A-Z]) "
    r"(?P<main_group>[1-9][0-9]{0,2})/"
    r"(?P<subgroup>[0-9]{2,6})$"
)
ASCII_ALNUM_RE = re.compile(r"^[A-Za-z0-9]+$")
JP_ERA_CITATION_RE = re.compile(
    r"^JP(?P<publication>特開|特公|実開|実公)"
    r"(?P<era>[平昭])"
    r"(?P<era_year>\d+)-"
    r"(?P<serial>\d+)"
    r"(?P<kind_code>[A-Z]\d?)?$"
)
JP_GREGORIAN_CITATION_RE = re.compile(
    r"^JP特開"
    r"(?P<year>\d{4})-"
    r"(?P<serial>\d+)"
    r"(?:\([^)]*\))?"
    r"(?P<kind_code>[A-Z]\d?)?$"
)
JP_REGISTRATION_CITATION_RE = re.compile(
    r"^JP(?:特許第|実用新案登録第|第)"
    r"(?P<registration_number>\d+)号"
    r"(?:\([^)]*\))?"
    r"(?P<kind_code>[A-Z]\d?)$"
)
JP_ERA_CODES = {"平": "H", "昭": "S"}
JP_PUBLICATION_DEFAULT_KIND_CODES = {
    "特開": "A",
    "特公": "B2",
    "実開": "U",
    "実公": "Y2",
}
ValidationResult = tuple[bool, List[str], List[str]]


def check_claims(claims: Any) -> ValidationResult:
    claims_length = len(str(claims))
    if claims_length > MAX_CLAIMS_LENGTH:
        return (
            True,
            ["too_long"],
            [
                f"string length {claims_length} exceeds the maximum "
                f"of {MAX_CLAIMS_LENGTH}"
            ],
        )
    return False, [], []


def check_ipc_unified(ipc_unified: Any) -> ValidationResult:
    if ipc_unified is None:
        return True, ["null"], ["value is null"]

    if isinstance(ipc_unified, str):
        try:
            ipc_unified = json.loads(ipc_unified, strict=False)
        except json.JSONDecodeError:
            return True, ["invalid_json"], ["value must be a JSON array"]

    if not isinstance(ipc_unified, list):
        return True, ["wrong_type"], ["value must be a list"]

    error_labels: List[str] = []
    reasons: List[str] = []

    for index, ipc_code in enumerate(ipc_unified):
        if not isinstance(ipc_code, str):
            if "wrong_type" not in error_labels:
                error_labels.append("wrong_type")
            reasons.append(f"item[{index}] must be a string")
            continue

        # IPC entries whose main group and subgroup are both zero are
        # normalized to the four-character subclass code (for example,
        # ``F03G 0/00`` becomes ``F03G``).
        if IPC_SUBCLASS_RE.fullmatch(ipc_code):
            continue

        match = IPC_CODE_RE.fullmatch(ipc_code)
        if match is None:
            if "invalid_format" not in error_labels:
                error_labels.append("invalid_format")
            reasons.append(
                f"item[{index}] value {ipc_code!r} must match IPC format "
                "'<A-H><01-99><A-Z>' or "
                "'<A-H><01-99><A-Z> <1-999>/<2-6 digits>'"
            )
            continue

        subgroup = match.group("subgroup")
        if subgroup != "00" and int(subgroup) == 0:
            if "invalid_format" not in error_labels:
                error_labels.append("invalid_format")
            reasons.append(
                f"item[{index}] value {ipc_code!r} subgroup may be zero only "
                "when written as '00'"
            )

    return bool(error_labels), error_labels, reasons


def _expected_jp_document_number(document_number: str) -> str | None:
    """Return the expected normalized value for supported JP citation forms."""
    match = JP_ERA_CITATION_RE.fullmatch(document_number)
    if match is not None:
        kind_code = match.group("kind_code") or JP_PUBLICATION_DEFAULT_KIND_CODES[
            match.group("publication")
        ]
        return (
            "JP"
            f"{JP_ERA_CODES[match.group('era')]}"
            f"{match.group('era_year').zfill(2)}"
            f"{match.group('serial').zfill(6)}"
            f"{kind_code}"
        )

    match = JP_GREGORIAN_CITATION_RE.fullmatch(document_number)
    if match is not None:
        kind_code = match.group("kind_code") or "A"
        return (
            "JP"
            f"{match.group('year')}"
            f"{match.group('serial').zfill(6)}"
            f"{kind_code}"
        )

    match = JP_REGISTRATION_CITATION_RE.fullmatch(document_number)
    if match is not None:
        return (
            "JP"
            f"{match.group('registration_number')}"
            f"{match.group('kind_code')}"
        )

    return None


def check_document_number_unifed(
    document_number_unifed: Any,
    document_number: Any = None,
) -> ValidationResult:
    error_labels: List[str] = []
    reasons: List[str] = []

    if not isinstance(document_number_unifed, str):
        return True, ["wrong_type"], ["value must be a string"]

    if ASCII_ALNUM_RE.fullmatch(document_number_unifed) is None:
        error_labels.append("invalid_format")
        reasons.append("value must contain only ASCII letters and digits")

    if isinstance(document_number, str):
        expected = _expected_jp_document_number(document_number)
        if expected is not None and document_number_unifed != expected:
            error_labels.append("incorrect_conversion")
            reasons.append(
                f"conversion from document_number {document_number!r} is incorrect: "
                f"expected {expected!r}, got {document_number_unifed!r}"
            )

    return bool(error_labels), error_labels, reasons


FIELD_VALIDATORS = {
    "claims": lambda record: check_claims(record.get("claims")),
    "ipc_unified": lambda record: check_ipc_unified(record.get("ipc_unified")),
    "document_number_unifed": lambda record: check_document_number_unifed(
        record.get("document_number_unifed"),
        record.get("document_number"),
    ),
}


@Model.rule_register("QUALITY_BAD_EFFECTIVENESS", ["xinghe", "quanliang"])
class RulePatentFieldValidation(BaseRule):
    _metric_info = {
        "category": "Rule-Based Metadata Quality Metrics",
        "quality_dimension": "EFFECTIVENESS",
        "metric_name": "RulePatentFieldValidation",
        "description": "Validate patent metadata fields and report invalid fields",
        "paper_title": "",
        "paper_url": "",
        "paper_authors": "",
        "evaluation_results": "",
    }

    _required_fields = []
    dynamic_config = EvaluatorRuleArgs(key_list=list(FIELD_VALIDATORS.keys()))

    def eval(self, input_data: Data) -> EvalDetail:
        res = EvalDetail(metric=self.__class__.__name__)
        record = input_data.to_dict()
        selected_fields = self.dynamic_config.key_list or []
        bad_fields: List[str] = []
        reasons: List[str] = []

        for field in selected_fields:
            if field not in FIELD_VALIDATORS:
                bad_fields.append(f"{field}.unsupported_field")
                reasons.append(f"{field}: unsupported field")
                continue
            if field not in record:
                bad_fields.append(f"{field}.missing_field")
                reasons.append(f"{field}: missing field")
                continue
            invalid, error_labels, detail_reasons = FIELD_VALIDATORS[field](record)
            if invalid:
                bad_fields.extend(f"{field}.{error_label}" for error_label in error_labels)
                reasons.extend(f"{field}: {reason}" for reason in detail_reasons)

        if bad_fields:
            res.status = True
            res.label = bad_fields
            res.reason = reasons
        else:
            res.label = [QualityLabel.QUALITY_GOOD]
        return res
