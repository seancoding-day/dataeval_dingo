import pytest

from dingo.io.input import Data
from dingo.model.rule.scibase.rule_patent import MAX_CLAIMS_LENGTH, RulePatentFieldValidation, check_document_number_unifed, check_ipc_unified


def _claims_with_string_length(length: int) -> list[dict]:
    empty_claims = [{"text": ""}]
    return [{"text": "x" * (length - len(str(empty_claims)))}]


class TestRulePatentFieldValidation:
    def test_claims_at_maximum_length_is_valid(self):
        claims = _claims_with_string_length(MAX_CLAIMS_LENGTH)
        assert len(str(claims)) == MAX_CLAIMS_LENGTH

        result = RulePatentFieldValidation().eval(
            Data(
                claims=claims,
                ipc_unified=[],
                document_number="JP2013022164A",
                document_number_unifed="JP2013022164A",
            )
        )

        assert result.status is False
        assert result.label == ["QUALITY_GOOD"]

    def test_claims_over_maximum_length_is_invalid(self):
        claims = _claims_with_string_length(MAX_CLAIMS_LENGTH + 1)
        assert len(str(claims)) == MAX_CLAIMS_LENGTH + 1

        result = RulePatentFieldValidation().eval(
            Data(
                claims=claims,
                ipc_unified=[],
                document_number="JP2013022164A",
                document_number_unifed="JP2013022164A",
            )
        )

        assert result.status is True
        assert result.label == ["claims.too_long"]
        assert result.reason == [
            "claims: string length 1000001 exceeds the maximum of 1000000"
        ]

    def test_missing_claims_is_invalid(self):
        result = RulePatentFieldValidation().eval(
            Data(
                ipc_unified=[],
                document_number="JP2013022164A",
                document_number_unifed="JP2013022164A",
            )
        )

        assert result.status is True
        assert result.label == ["claims.missing_field"]

    @pytest.mark.parametrize(
        "ipc_unified",
        [
            [],
            ["F03G"],
            ["A01A 1/00"],
            ["B60T 8/48", "H99Z 999/999999"],
            '["B60T 8/48", "B60T 8/58"]',
        ],
    )
    def test_valid_ipc_unified(self, ipc_unified):
        assert check_ipc_unified(ipc_unified) == (False, [], [])

    @pytest.mark.parametrize(
        "ipc_code",
        [
            "I01A 1/00",       # Section must be A-H.
            "A00A 1/00",       # Class must be 01-99.
            "A1A 1/00",        # Class must contain exactly two digits.
            "A01a 1/00",       # Subclass must be uppercase A-Z.
            "A01A\u00a01/00",  # Separator must be one ASCII space.
            "A01A  1/00",      # Only one separator space is allowed.
            "A01A 01/00",      # Main group must not be zero-padded.
            "A01A 1000/00",    # Main group must be at most 999.
            "A01A 1/0",        # Subgroup must contain at least two digits.
            "A01A 1/000",      # A zero subgroup must be written as 00.
            "A01A 1/1234567",  # Subgroup must contain at most six digits.
            "A01A 1-00",       # Groups must be separated by a slash.
            "A01A 1/00 A",     # Extra suffixes are not allowed.
            "F03G 0/00",       # Zero groups must be reduced to "F03G".
        ],
    )
    def test_invalid_ipc_format(self, ipc_code):
        invalid, labels, reasons = check_ipc_unified([ipc_code])

        assert invalid is True
        assert labels == ["invalid_format"]
        assert reasons[0].startswith(f"item[0] value {ipc_code!r}")

    def test_reports_every_invalid_item_with_its_value(self):
        invalid, labels, reasons = check_ipc_unified(
            ["B01J 29/40", "C00C 5/27", "B01J 29/18", "C00C 15/08"]
        )

        assert invalid is True
        assert labels == ["invalid_format"]
        assert reasons == [
            "item[1] value 'C00C 5/27' must match IPC format "
            "'<A-H><01-99><A-Z>' or "
            "'<A-H><01-99><A-Z> <1-999>/<2-6 digits>'",
            "item[3] value 'C00C 15/08' must match IPC format "
            "'<A-H><01-99><A-Z>' or "
            "'<A-H><01-99><A-Z> <1-999>/<2-6 digits>'",
        ]

    def test_wrong_type_reason_does_not_include_value(self):
        invalid, labels, reasons = check_ipc_unified([123])

        assert invalid is True
        assert labels == ["wrong_type"]
        assert reasons == ["item[0] must be a string"]

    @pytest.mark.parametrize(
        ("ipc_unified", "expected_label"),
        [
            (None, "null"),
            ({"code": "A01A 1/00"}, "wrong_type"),
            ([1], "wrong_type"),
            ("not-json", "invalid_json"),
        ],
    )
    def test_invalid_ipc_unified_value(self, ipc_unified, expected_label):
        invalid, labels, reasons = check_ipc_unified(ipc_unified)

        assert invalid is True
        assert labels == [expected_label]
        assert reasons

    def test_rule_reports_invalid_ipc_unified(self):
        result = RulePatentFieldValidation().eval(
            Data(
                claims=[],
                ipc_unified=["A01A 01/00"],
                document_number="JP2013022164A",
                document_number_unifed="JP2013022164A",
            )
        )

        assert result.status is True
        assert result.label == ["ipc_unified.invalid_format"]
        assert result.reason[0].startswith("ipc_unified: item[0]")

    @pytest.mark.parametrize(
        ("document_number", "document_number_unifed"),
        [
            ("JP特開平11-73838A", "JPH11073838A"),
            ("JP特開平5-263266A", "JPH05263266A"),
            ("JP特開昭63-123456A", "JPS63123456A"),
            ("JP特開昭63-123456", "JPS63123456A"),
            ("JP特開2003-75095(P2003-75095A)A", "JP2003075095A"),
            ("JP特公平7-46852B2", "JPH07046852B2"),
            ("JP特公昭48-1234B2", "JPS48001234B2"),
            ("JP特許第3405959号(P3405959)B2", "JP3405959B2"),
            ("JP実用新案登録第3082161号(U3082161)U", "JP3082161U"),
            ("JP実開平6-10396U", "JPH06010396U"),
            ("JP実公平7-15070Y2", "JPH07015070Y2"),
            ("JP第2891579号B2", "JP2891579B2"),
        ],
    )
    def test_valid_document_number_conversion(
        self,
        document_number,
        document_number_unifed,
    ):
        assert check_document_number_unifed(
            document_number_unifed,
            document_number,
        ) == (False, [], [])

    @pytest.mark.parametrize(
        "document_number_unifed",
        [
            "",
            "JP特開平11-73838A",
            "JP2013-022164A",
            "JP2013022164 A",
        ],
    )
    def test_document_number_unifed_must_be_ascii_alphanumeric(
        self,
        document_number_unifed,
    ):
        invalid, labels, reasons = check_document_number_unifed(
            document_number_unifed
        )

        assert invalid is True
        assert labels == ["invalid_format"]
        assert reasons == ["value must contain only ASCII letters and digits"]

    @pytest.mark.parametrize("document_number_unifed", [None, 123, []])
    def test_document_number_unifed_must_be_string(
        self,
        document_number_unifed,
    ):
        assert check_document_number_unifed(document_number_unifed) == (
            True,
            ["wrong_type"],
            ["value must be a string"],
        )

    def test_reports_incorrect_document_number_conversion(self):
        invalid, labels, reasons = check_document_number_unifed(
            "JPH11073839A",
            "JP特開平11-73838A",
        )

        assert invalid is True
        assert labels == ["incorrect_conversion"]
        assert reasons == [
            "conversion from document_number 'JP特開平11-73838A' is incorrect: "
            "expected 'JPH11073838A', got 'JPH11073839A'"
        ]

    def test_rule_reports_invalid_document_number_unifed(self):
        result = RulePatentFieldValidation().eval(
            Data(
                claims=[],
                ipc_unified=[],
                document_number="JP特開平11-73838A",
                document_number_unifed="JPH11073839A",
            )
        )

        assert result.status is True
        assert result.label == ["document_number_unifed.incorrect_conversion"]
        assert result.reason == [
            "document_number_unifed: conversion from document_number "
            "'JP特開平11-73838A' is incorrect: expected 'JPH11073838A', "
            "got 'JPH11073839A'"
        ]

    def test_missing_document_number_unifed_is_invalid(self):
        result = RulePatentFieldValidation().eval(
            Data(
                claims=[],
                ipc_unified=[],
                document_number="JP2013022164A",
            )
        )

        assert result.status is True
        assert result.label == ["document_number_unifed.missing_field"]
        assert result.reason == ["document_number_unifed: missing field"]
