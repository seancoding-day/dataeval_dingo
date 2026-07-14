from dingo.model.llm.llm_search_result_effectiveness import (
    LLMSearchResultEffectiveness,
    _filter_llm_field_issues,
    _issues_to_labels,
    _looks_like_utf8_latin1_mojibake,
    _rule_abnormal_char_issues,
)


def _mojibake(value: str) -> str:
    return value.encode("utf-8").decode("latin-1")


def test_detects_utf8_cyrillic_decoded_as_latin1():
    broken = _mojibake("Развитие научных исследований")

    assert _looks_like_utf8_latin1_mojibake(broken)
    assert "RuleMojibake" in _rule_abnormal_char_issues(broken)
    assert _filter_llm_field_issues("title", broken, ["title:mojibake"]) == ["title:mojibake"]
    assert _issues_to_labels(["RuleMojibake", "title:mojibake"]) == ["Effectiveness.Error_Mojibake"]


def test_does_not_flag_valid_latin_or_cyrillic_text():
    assert not _looks_like_utf8_latin1_mojibake("Ð is a valid Icelandic letter")
    assert not _looks_like_utf8_latin1_mojibake("Развитие научных исследований")


def test_detects_mojibake_fragment_in_mixed_language_text():
    broken = "中文标题 | " + _mojibake("Научные исследования")

    assert _looks_like_utf8_latin1_mojibake(broken)


def test_rule_only_grade_penalizes_mojibake_fields():
    broken_title = _mojibake("Развитие научных исследований")
    broken_abstract = _mojibake(
        "В этой статье рассматриваются современные научные исследования и методы анализа данных. " * 4
    )
    grader = LLMSearchResultEffectiveness(enable_llm_quality=False)

    grade = grader.grade(
        title=broken_title,
        abstract=broken_abstract,
        keywords=["research", "analysis", "data"],
        venue="Science Journal",
    )

    assert "RuleMojibake" in grade.issues
    assert grade.title_score == 0.1
    assert grade.abstract_score == 0.1
    assert grade.score < 0.5
