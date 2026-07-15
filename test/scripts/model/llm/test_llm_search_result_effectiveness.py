import pytest

from dingo.model.llm.llm_search_result_effectiveness import (  # isort: skip
    LLMSearchResultEffectiveness,
    _filter_llm_field_issues,
    _issues_to_labels,
    _looks_like_utf8_latin1_mojibake,
    _rule_abnormal_char_issues,
    extract_authors,
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


def test_extract_authors_supports_common_response_shapes():
    assert extract_authors({"author": [{"name": "Alice"}, {"display_name": "张三"}]}) == ["Alice", "张三"]
    assert extract_authors({"authors": "Alice | Bob"}) == ["Alice", "Bob"]
    assert extract_authors({"author": {"author_name": "Carol"}}) == ["Carol"]


def test_author_is_scored_without_rewarding_author_count():
    grader = LLMSearchResultEffectiveness(enable_llm_quality=False)
    common = {
        "title": "A comprehensive evaluation of academic search result metadata",
        "abstract": "academic search metadata provides useful information for readers " * 15,
        "keywords": ["search", "metadata", "quality", "evaluation", "academic"],
        "venue": "International Journal of Search Quality Research",
    }

    single_author = grader.grade(**common, authors=["Alice"])
    multiple_authors = grader.grade(**common, authors=["Alice", "Bob", "Carol"])
    missing_author = grader.grade(**common)

    assert single_author.author_score == 1.0
    assert multiple_authors.author_score == 1.0
    assert single_author.score == multiple_authors.score
    assert missing_author.author_score == 0.0
    assert missing_author.score == pytest.approx(single_author.score - 0.1)
    assert "missing_author" in missing_author.issues
    assert _issues_to_labels(missing_author.issues) == ["Effectiveness.Error_Author_Miss"]


def test_missing_venue_is_diagnostic_only_and_does_not_reduce_score():
    grader = LLMSearchResultEffectiveness(enable_llm_quality=False)
    common = {
        "title": "A comprehensive evaluation of academic search result metadata",
        "abstract": "academic search metadata provides useful information for readers " * 15,
        "keywords": ["search", "metadata", "quality", "evaluation", "academic"],
        "authors": ["Alice"],
    }

    with_venue = grader.grade(**common, venue="International Journal of Search Quality Research")
    without_venue = grader.grade(**common, venue="")

    assert with_venue.score == without_venue.score
    assert without_venue.venue_score == 0.0
    assert "missing_venue" not in without_venue.issues
    assert "Effectiveness.Error_Venue_Miss" not in _issues_to_labels(without_venue.issues)


def _complete_result() -> dict:
    return {
        "title": "A comprehensive evaluation of academic search result metadata",
        "abstract": "academic search metadata provides useful information for readers " * 15,
        "keywords": ["search", "metadata", "quality", "evaluation", "academic"],
        "publication_venue_name_unified": "International Journal of Search Quality Research",
        "author": [{"name": "Alice"}],
    }


@pytest.mark.parametrize("field", ["title", "abstract", "keywords", "venue", "author"])
def test_all_effectiveness_fields_scan_html_residue(field: str):
    result = _complete_result()
    contaminated = "clean text <span class='highlight'>leaked markup</span>"
    if field == "keywords":
        result["keywords"] = [contaminated]
    elif field == "venue":
        result["publication_venue_name_unified"] = contaminated
    elif field == "author":
        result["author"] = [{"name": contaminated}]
    elif field == "abstract":
        result["abstract"] = "readable abstract text " * 100 + contaminated
    else:
        result[field] = contaminated

    grade = LLMSearchResultEffectiveness(enable_llm_quality=False).grade(result=result)

    assert "RuleSpecialCharacter" in grade.issues
    assert getattr(grade, f"{field}_score") <= 0.1


@pytest.mark.parametrize("field", ["title", "abstract", "keywords", "venue", "author"])
def test_all_effectiveness_fields_scan_replacement_character(field: str):
    result = _complete_result()
    contaminated = "metadata contains \ufffd broken text"
    if field == "keywords":
        result["keywords"] = [contaminated]
    elif field == "venue":
        result["publication_venue_name_unified"] = contaminated
    elif field == "author":
        result["author"] = [{"name": contaminated}]
    else:
        result[field] = contaminated

    grade = LLMSearchResultEffectiveness(enable_llm_quality=False).grade(result=result)

    assert "RuleMojibake" in grade.issues
    assert getattr(grade, f"{field}_score") <= 0.1
