from dingo.model.llm.llm_search_result_relevance import (
    _extract_result_dois,
    _grade_doi_result,
    _normalize_doi,
    is_doi_query,
)


def test_normalize_doi_variants():
    assert _normalize_doi("10.1016/j.ijbiomac.2025.143529") == "10.1016/j.ijbiomac.2025.143529"
    assert _normalize_doi("https://doi.org/10.1038/NCOMMS7112") == "10.1038/ncomms7112"
    assert _normalize_doi(":10.1111/jipb.70096") == "10.1111/jipb.70096"
    assert _normalize_doi("PBPK review") == ""
    assert is_doi_query("10.1016/j.ijbiomac.2025.143529")
    assert not is_doi_query("PBPK review")


def test_extract_result_dois_from_supported_fields():
    result = {
        "doi": "https://doi.org/10.1000/ABC",
        "unique_id": "paper:10.2000/xyz",
        "locations": [{"url": "https://doi.org/10.3000/location"}],
    }
    assert _extract_result_dois(result) == [
        "10.1000/abc",
        "10.2000/xyz",
        "10.3000/location",
    ]


def test_doi_query_uses_exact_match():
    matched = _grade_doi_result(
        "10.1016/j.ijbiomac.2025.143529",
        {"doi": "https://doi.org/10.1016/j.ijbiomac.2025.143529"},
    )
    mismatched = _grade_doi_result(
        "10.1016/j.ijbiomac.2025.143529",
        {"doi": "https://doi.org/10.3390/plants14152362"},
    )

    assert matched is not None and matched.score == 1.0
    assert mismatched is not None and mismatched.score == 0.0
    assert "DOI mismatch" in mismatched.reasoning


def test_non_doi_query_falls_back_to_llm():
    assert _grade_doi_result("PBPK相关综述", {"doi": "10.1000/test"}) is None
