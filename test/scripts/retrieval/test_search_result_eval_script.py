"""Tests for the end-to-end search result evaluation example."""

import json
import os
import sys
from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace

EXAMPLE_DIR = Path(__file__).resolve().parents[3] / "examples" / "retrieval"
if str(EXAMPLE_DIR) not in sys.path:
    sys.path.insert(0, str(EXAMPLE_DIR))

import sdk_eval_search_result  # noqa: E402
from sdk_eval_search_result import build_reports, clear_executor_classification_dirs, load_env_file, normalize_search_result, retrieve_queries  # noqa: E402,E501
from search_result_eval_utils import load_queries, write_classified_jsonl  # noqa: E402

from dingo.retrieval.search_client import PaperResult, SearchResponse  # noqa: E402


def _record(
    query: str,
    rank: int,
    relevance: float,
    effectiveness: float,
    authority: float,
) -> dict:
    return {
        "raw_data": {
            "query": query,
            "query_index": 1,
            "rank": rank,
            "title": f"Result {rank}",
            "search_result": {
                "title": f"Result {rank}",
                "abstract": f"Abstract {rank}",
                "_eval_query": query,
            },
        },
        "eval_details": {
            "search_result": [
                {"metric": "LLMSearchResultRelevance", "score": relevance},
                {"metric": "LLMSearchResultEffectiveness", "score": effectiveness},
                {"metric": "LLMSearchResultAuthority", "score": authority},
            ]
        }
    }


def _args() -> Namespace:
    return Namespace(
        top_k=10,
        threshold=0.15,
        openai_model="test-model",
        prompt_mode="detailed",
        llm_max_tokens=1024,
        openai_temperature=0.0,
        llm_timeout=60.0,
        llm_workers=1,
        disable_effectiveness_llm_quality=False,
        effectiveness_llm_max_tokens=512,
    )


def test_load_queries_supports_query_only_jsonl(tmp_path):
    path = tmp_path / "queries.jsonl"
    path.write_text(
        '\n'.join((json.dumps({"query": "first"}), json.dumps({"query_text": "second"}))),
        encoding="utf-8",
    )

    assert load_queries(path) == ["first", "second"]


def test_load_queries_deduplicates_queries(tmp_path):
    path = tmp_path / "queries.jsonl"
    path.write_text(
        "\n".join((json.dumps({"query": "same"}), json.dumps({"query": "same"}))),
        encoding="utf-8",
    )

    assert load_queries(path) == ["same"]


def test_load_env_file_does_not_override_process_environment(tmp_path, monkeypatch):
    path = tmp_path / ".env"
    path.write_text("EXISTING=value-from-file\nNEW_VALUE=loaded\n", encoding="utf-8")
    monkeypatch.setenv("EXISTING", "value-from-process")
    monkeypatch.delenv("NEW_VALUE", raising=False)

    load_env_file(path)

    assert os.environ["EXISTING"] == "value-from-process"
    assert os.environ["NEW_VALUE"] == "loaded"


def test_retrieve_queries_writes_reusable_results_and_request_log(tmp_path, monkeypatch):
    input_path = tmp_path / "queries.jsonl"
    result_path = tmp_path / "retrieval_results.jsonl"
    log_path = tmp_path / "request_log.jsonl"
    input_path.write_text(json.dumps({"query": "test query"}), encoding="utf-8")

    class FakeClient:
        def search(self, query, limit=10):
            return SearchResponse(
                query=query,
                results=[PaperResult(paper_id="p1", title="Test result", raw={"title": "Test result"})],
                response_time_ms=12.5,
                status_code=200,
            )

    monkeypatch.setattr(sdk_eval_search_result, "_build_search_client", lambda args: FakeClient())
    args = Namespace(
        input_jsonl=input_path,
        max_queries=None,
        top_k=10,
        search_workers=1,
        retrieval_backend="meta_search",
    )

    summary = retrieve_queries(args, result_path, log_path)
    saved = json.loads(result_path.read_text(encoding="utf-8"))
    log = json.loads(log_path.read_text(encoding="utf-8"))

    assert saved["query"] == "test query"
    assert saved["results"][0]["title"] == "Test result"
    assert log["result_count"] == 1
    assert summary["success_count"] == 1


def test_normalize_openalex_result_maps_metric_fields():
    raw = {
        "id": "https://openalex.org/W1",
        "doi": "https://doi.org/10.1/example",
        "cited_by_count": 12,
        "publication_year": 2025,
        "type": "article",
        "language": "en",
        "keywords": [{"display_name": "Search"}],
        "authorships": [
            {"author": {"display_name": "A. Author", "orcid": "https://orcid.org/1"}}
        ],
        "primary_location": {
            "source": {
                "display_name": "Journal of Testing",
                "type": "journal",
                "issn": ["1234-5678"],
                "host_organization_name": "Test Publisher",
            }
        },
    }
    paper = PaperResult(
        paper_id=raw["id"],
        title="A result",
        abstract="An abstract",
        score=9.5,
        year=2025,
        raw=raw,
    )

    result = normalize_search_result(paper, "openalex")

    assert result["citation_count"] == 12
    assert result["keywords"] == ["Search"]
    assert result["author"][0]["name"] == "A. Author"
    assert result["publication_venue_name_unified"] == "Journal of Testing"
    assert result["publication_venue_type"] == "journal"
    assert result["publication_publisher"] == ["Test Publisher"]


def test_meta_search_accepts_full_endpoint():
    from dingo.retrieval.backends.agentic import MetaSearchClient

    client = MetaSearchClient(api_url="https://api.sciverse.space/meta-search")

    assert client.base_url == "https://api.sciverse.space"


def test_query_report_uses_rank_weighted_means_and_embeds_full_results():
    records = [
        _record("query", 1, relevance=0.0, effectiveness=0.1, authority=0.3),
        _record("query", 2, relevance=0.2, effectiveness=0.2, authority=0.5),
    ]

    summary, query_rows, _, _, classified = build_reports(
        records,
        _args(),
        SimpleNamespace(output_path="output/test"),
    )

    assert summary["query_aggregation"] == "rank_discounted_mean"
    assert query_rows[0]["relevance"] == 0.07737
    assert query_rows[0]["effectiveness"] == 0.13869
    assert query_rows[0]["authority"] == 0.37737
    assert query_rows[0]["relevance_aggregation"] == "rank_discounted_mean"
    assert classified[0]["labels"] == [
        "QUALITY_BAD.SEARCH_RESULT_RELEVANCE_LOW",
        "QUALITY_BAD.SEARCH_RESULT_EFFECTIVENESS_LOW",
    ]
    assert classified[0]["results"][0]["abstract"] == "Abstract 1"
    assert classified[0]["results"][0]["_evaluation"] == {
        "rank": 1,
        "relevance": 0.0,
        "effectiveness": 0.1,
        "authority": 0.3,
    }
    assert "_eval_query" not in classified[0]["results"][0]


def test_query_report_has_no_overall_and_empty_query_uses_three_low_labels():
    summary, query_rows, result_rows, _, classified = build_reports(
        [],
        _args(),
        SimpleNamespace(output_path="output/test"),
        empty_queries=["empty query"],
    )

    assert "weights" not in summary
    assert "overall" not in summary["metrics"]
    assert "overall" not in query_rows[0]
    assert result_rows == []
    assert classified[0]["labels"] == [
        "QUALITY_BAD.SEARCH_RESULT_RELEVANCE_LOW",
        "QUALITY_BAD.SEARCH_RESULT_EFFECTIVENESS_LOW",
        "QUALITY_BAD.SEARCH_RESULT_AUTHORITY_LOW",
    ]


def test_result_level_executor_summary_is_not_exposed():
    summary, *_ = build_reports(
        [],
        _args(),
        SimpleNamespace(output_path="output/test"),
    )

    assert "result_level" not in summary


def test_clear_executor_classification_dirs(tmp_path):
    (tmp_path / "bad" / "result_level").mkdir(parents=True)
    (tmp_path / "good").mkdir()

    clear_executor_classification_dirs(tmp_path)

    assert not (tmp_path / "bad").exists()
    assert not (tmp_path / "good").exists()


def test_classified_output_contains_query_records_only(tmp_path):
    records = [
        {
            "query": "first",
            "eval_status": True,
            "labels": ["QUALITY_BAD.SEARCH_RESULT_RELEVANCE_LOW"],
            "results": [{"title": "First result"}],
        },
        {
            "query": "second",
            "eval_status": True,
            "labels": ["QUALITY_BAD.SEARCH_RESULT_RELEVANCE_LOW"],
            "results": [{"title": "Second result"}],
        },
    ]

    write_classified_jsonl(tmp_path, records)

    output = tmp_path / "bad" / "QUALITY_BAD" / "SEARCH_RESULT_RELEVANCE_LOW.jsonl"
    lines = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert [line["query"] for line in lines] == ["first", "second"]
    assert all(line["results"] for line in lines)
    assert not (tmp_path / "bad" / "query_level").exists()
    assert not (tmp_path / "bad" / "result_level").exists()
