from dingo.model.llm.llm_search_result_authority import LLMSearchResultAuthority, _has_doi_in_locations


class NonSerializableLocation:
    pass


def test_has_doi_in_location_dict_or_string():
    assert _has_doi_in_locations([{"url": "https://doi.org/10.1000/test"}])
    assert _has_doi_in_locations(["https://DOI.ORG/10.1000/test"])


def test_has_doi_in_locations_ignores_invalid_shapes():
    assert not _has_doi_in_locations(True)
    assert not _has_doi_in_locations({"url": "https://doi.org/10.1000/test"})
    assert not _has_doi_in_locations([NonSerializableLocation()])


def test_authority_grade_handles_non_serializable_location():
    grade = LLMSearchResultAuthority().grade(
        result={"doi": "", "locations": [NonSerializableLocation()]},
    )

    assert grade.doi_score == 0.0
