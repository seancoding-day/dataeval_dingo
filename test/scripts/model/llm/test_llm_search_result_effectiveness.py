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


def test_nonempty_fields_are_not_penalized_for_length_or_item_count():
    grader = LLMSearchResultEffectiveness(enable_llm_quality=False)

    grade = grader.grade(
        title="D",
        abstract="短",
        keywords=["AI"],
        venue="J",
        authors=["Q"],
    )

    assert grade.title_score == 1.0
    assert grade.abstract_score == 1.0
    assert grade.keywords_score == 1.0
    assert grade.venue_score == 1.0
    assert grade.author_score == 1.0
    assert grade.score == 1.0
    assert grade.issues == []


def test_longer_content_does_not_receive_more_effectiveness_credit():
    grader = LLMSearchResultEffectiveness(enable_llm_quality=False)
    short = grader.grade(title="D", abstract="A", keywords=["K"], authors=["Q"])
    long = grader.grade(
        title="A comprehensive academic title",
        abstract="A complete and readable abstract. " * 100,
        keywords=["one", "two", "three", "four", "five"],
        authors=["Alice", "Bob"],
    )

    assert short.score == long.score == 1.0


def test_preview_navigation_text_is_not_treated_as_html():
    abstract = (
        "Preview this article: Meaning and the Structure of Language, by Wallace Chafe, "
        "Page 1 of 1 < Previous page | Next page > "
        "/docserver/preview/fulltext/ce/33/8/collegeenglish18315-1.gif"
    )

    assert "RuleSpecialCharacter" not in _rule_abnormal_char_issues(abstract)

    # LLM quality is enabled deliberately: this text should bypass the LLM
    # because it is not an abnormal-character candidate.
    grade = LLMSearchResultEffectiveness(enable_llm_quality=True).grade(
        title="Meaning and the Structure of Language, by Wallace Chafe",
        abstract=abstract,
        keywords=["Linguistics"],
        venue="College English",
        authors=["Frank Heny"],
    )

    assert grade.score == 1.0
    assert grade.issues == []


@pytest.mark.parametrize(
    "markup",
    [
        "<span class='highlight'>language</span>",
        "<i>language</i>",
        "H<sub>2</sub>O",
        "<scp>AM</scp>",
    ],
)
def test_real_academic_html_tags_remain_detectable(markup: str):
    assert "RuleSpecialCharacter" in _rule_abnormal_char_issues(markup)
    assert _filter_llm_field_issues("title", markup, ["title:html_tag"]) == [
        "title:html_tag"
    ]


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
