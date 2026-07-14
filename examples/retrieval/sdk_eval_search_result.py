"""Evaluate search results with relevance, effectiveness, and authority metrics.

This script uses Dingo LocalExecutor for result-level metric execution, then
aggregates executor outputs back to query-level CSV/JSON reports.
"""

from __future__ import annotations
import argparse
import json
import math
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from search_result_eval_utils import add_common_args, get_title, load_query_result_jsonl, rank_discounted_mean, summarize, write_classified_jsonl, write_csv, write_json  # noqa: E402

from dingo.config import InputArgs  # noqa: E402
from dingo.exec import Executor  # noqa: E402
from dingo.model.llm.llm_search_result_relevance import is_doi_query  # noqa: E402

WEIGHTS = {
    "relevance": 0.7,
    "effectiveness": 0.2,
    "authority": 0.1,
}

EFFECTIVENESS_LABEL_TO_ISSUE = {
    "Effectiveness.Error_Title_Miss": "missing_title",
    "Effectiveness.Error_Abstract_Miss": "missing_abstract",
    "Effectiveness.Error_Keywords_Miss": "missing_keywords",
    "Effectiveness.Error_Venue_Miss": "missing_venue",
    "Effectiveness.Error_HTML_Tag": "html_tag",
    "Effectiveness.Error_Mojibake": "mojibake",
    "Effectiveness.Error_Invisible_Char": "invisible_char",
    "Effectiveness.Error_Unreadable_Text": "unreadable_text",
    "Effectiveness.Error_Special_Char_Noise": "special_char_noise",
    "Effectiveness.Error_LLM_Quality_Parse": "llm_quality_parse_error",
    "Effectiveness.Error_Effectiveness_Low": "effectiveness_low",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate search result quality with Dingo executor.")
    add_common_args(parser)
    parser.add_argument("--openai-api-key", default=os.environ.get("OPENAI_API_KEY"))
    parser.add_argument("--openai-base-url", default=os.environ.get("OPENAI_BASE_URL"))
    parser.add_argument("--openai-model", default=os.environ.get("OPENAI_MODEL", "gpt-4o"))
    parser.add_argument("--openai-temperature", type=float, default=float(os.environ.get("OPENAI_TEMPERATURE", "0.0")))
    parser.add_argument("--prompt-mode", choices=("standard", "detailed"), default="detailed")
    parser.add_argument("--llm-max-tokens", type=int, default=1024)
    parser.add_argument("--llm-timeout", type=float, default=60.0)
    parser.add_argument("--llm-workers", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--effectiveness-llm-max-tokens", type=int, default=512)
    parser.add_argument(
        "--disable-effectiveness-llm-quality",
        action="store_true",
        help="Disable LLM readability/corruption judgment for effectiveness.",
    )
    parser.add_argument("--relevance-threshold", type=float, default=0.15)
    parser.add_argument("--effectiveness-threshold", type=float, default=0.15)
    parser.add_argument("--authority-threshold", type=float, default=0.15)
    parser.add_argument("--overall-threshold", type=float, default=0.15)
    parser.add_argument(
        "--save-detailed",
        action="store_true",
        help="Save detailed_results.json with query-level records and embedded result rows.",
    )
    return parser.parse_args()


def flatten_query_results(
    input_path: Path,
    output_path: Path,
    *,
    top_k: int,
    max_queries: int | None,
) -> tuple[int, list[str]]:
    items = load_query_result_jsonl(input_path, max_queries)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    empty_queries: list[str] = []
    with output_path.open("w", encoding="utf-8") as f:
        for query_index, item in enumerate(items, start=1):
            query = item["query"]
            if not item["results"][:top_k]:
                empty_queries.append(query)
            for rank, result in enumerate(item["results"][:top_k], start=1):
                result_payload = dict(result)
                result_payload["_eval_query"] = query
                row = {
                    "query": query,
                    "query_index": query_index,
                    "rank": rank,
                    "title": get_title(result),
                    "search_result": result_payload,
                }
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                count += 1
    return count, empty_queries


def build_executor_input(args: argparse.Namespace, flattened_path: Path) -> dict[str, Any]:
    relevance_config = {
        "model": args.openai_model,
        "key": args.openai_api_key,
        "api_url": args.openai_base_url,
        "temperature": args.openai_temperature,
        "prompt_mode": args.prompt_mode,
        "max_tokens": args.llm_max_tokens,
        "timeout": args.llm_timeout,
        "threshold": args.relevance_threshold,
    }
    effectiveness_config = {
        "model": args.openai_model,
        "key": args.openai_api_key,
        "api_url": args.openai_base_url,
        "temperature": args.openai_temperature,
        "max_tokens": args.effectiveness_llm_max_tokens,
        "timeout": args.llm_timeout,
        "threshold": args.effectiveness_threshold,
        "enable_llm_quality": not args.disable_effectiveness_llm_quality,
    }
    authority_config = {"threshold": args.authority_threshold}
    return {
        "task_name": "search_result_quality",
        "input_path": str(flattened_path),
        "output_path": str(args.output_dir),
        "dataset": {"source": "local", "format": "jsonl"},
        "executor": {
            "max_workers": args.llm_workers,
            "batch_size": args.batch_size,
            "result_save": {
                "bad": True,
                "good": True,
                "all_labels": True,
                "merge": True,
            },
        },
        "evaluator": [
            {
                "fields": {"search_result": "search_result"},
                "evals": [
                    {"name": "LLMSearchResultRelevance", "config": relevance_config},
                    {"name": "LLMSearchResultEffectiveness", "config": effectiveness_config},
                    {"name": "LLMSearchResultAuthority", "config": authority_config},
                ],
            }
        ],
    }


def load_executor_records(executor_output_path: str) -> list[dict[str, Any]]:
    all_results_path = Path(executor_output_path) / "all_results.jsonl"
    if not all_results_path.exists():
        raise FileNotFoundError(f"Executor merged result file not found: {all_results_path}")
    records = []
    with all_results_path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records


def get_metric_detail(record: dict[str, Any], metric: str) -> dict[str, Any]:
    details = record.get("eval_details", {}).get("search_result", [])
    for detail in details:
        if detail.get("metric") == metric:
            return detail
    return {}


def first_reason(detail: dict[str, Any]) -> dict[str, Any]:
    reason = detail.get("reason") or []
    if reason and isinstance(reason[0], dict):
        return reason[0]
    return {}


def filtered_effectiveness_issues(detail: dict[str, Any]) -> str:
    labels = detail.get("label") or []
    issues = []
    for label in labels:
        issue = EFFECTIVENESS_LABEL_TO_ISSUE.get(label)
        if issue and issue not in issues:
            issues.append(issue)
    return "|".join(issues)


def build_reports(
    records: list[dict[str, Any]],
    args: argparse.Namespace,
    executor_summary,
    executor_result_summary: dict[str, Any] | None = None,
    empty_queries: list[str] | None = None,
) -> tuple[dict, list[dict], list[dict], list[dict], list[dict]]:
    records = sorted(
        records,
        key=lambda r: (
            int(r.get("raw_data", {}).get("query_index") or 0),
            int(r.get("raw_data", {}).get("rank") or 0),
        ),
    )

    result_rows = []
    by_query: dict[str, list[dict[str, Any]]] = {}
    rank_relevance_error_count = 0
    rank_effectiveness_llm_quality_error_count = 0

    for record in records:
        raw = record.get("raw_data", {})
        query = raw.get("query", "")
        relevance_detail = get_metric_detail(record, "LLMSearchResultRelevance")
        effectiveness_detail = get_metric_detail(record, "LLMSearchResultEffectiveness")
        authority_detail = get_metric_detail(record, "LLMSearchResultAuthority")
        relevance_reason = first_reason(relevance_detail)
        effectiveness_reason = first_reason(effectiveness_detail)
        authority_reason = first_reason(authority_detail)

        relevance = round(float(relevance_detail.get("score") or 0.0), 5)
        effectiveness = round(float(effectiveness_detail.get("score") or 0.0), 5)
        authority = round(float(authority_detail.get("score") or 0.0), 5)
        overall = round(
            WEIGHTS["relevance"] * relevance
            + WEIGHTS["effectiveness"] * effectiveness
            + WEIGHTS["authority"] * authority,
            5,
        )

        relevance_error = str(relevance_reason.get("error") or "")
        effectiveness_error = str(effectiveness_reason.get("llm_quality_error") or "")
        if relevance_error:
            rank_relevance_error_count += 1
        if effectiveness_error:
            rank_effectiveness_llm_quality_error_count += 1

        row = {
            "query": query,
            "rank": raw.get("rank"),
            "title": raw.get("title", ""),
            "relevance": relevance,
            "query_relevance": round(float(relevance_reason.get("query_relevance") or 0.0), 5),
            "result_quality": round(float(relevance_reason.get("result_quality") or 0.0), 5),
            "relevance_content_issues": bool(relevance_reason.get("content_issues", False)),
            "relevance_content_issue_evidence": "|".join(relevance_reason.get("content_issue_evidence") or []),
            "relevance_error": relevance_error,
            "relevance_reasoning": relevance_reason.get("reasoning", ""),
            "effectiveness": effectiveness,
            "effectiveness_issues": filtered_effectiveness_issues(effectiveness_detail),
            "effectiveness_llm_quality_reason": effectiveness_reason.get("llm_quality_reason", ""),
            "effectiveness_llm_quality_error": effectiveness_error,
            "authority": authority,
            "citation_score": round(float(authority_reason.get("citation_score") or 0.0), 5),
            "influential_citation_score": round(float(authority_reason.get("influential_citation_score") or 0.0), 5),
            "venue_score": round(float(authority_reason.get("venue_score") or 0.0), 5),
            "doi_score": round(float(authority_reason.get("doi_score") or 0.0), 5),
            "authority_reason": authority_reason.get("reason", ""),
            "overall": overall,
        }
        result_rows.append(row)
        by_query.setdefault(query, []).append(row)

    query_rows = []
    detailed = []
    classified_records = []
    for query, rows in by_query.items():
        relevance_scores = [float(row["relevance"]) for row in rows]
        effectiveness_scores = [float(row["effectiveness"]) for row in rows]
        authority_scores = [float(row["authority"]) for row in rows]
        if is_doi_query(query):
            query_relevance = round(
                max(
                    (
                        float(row["relevance"])
                        / math.log2(max(1, int(row.get("rank") or index)) + 1)
                    )
                    for index, row in enumerate(rows, start=1)
                ),
                5,
            )
            relevance_aggregation = "doi_exact_match_rank_discount"
        else:
            query_relevance = round(rank_discounted_mean(relevance_scores), 5)
            relevance_aggregation = "rank_discounted_mean"
        query_effectiveness = round(rank_discounted_mean(effectiveness_scores), 5)
        query_authority = round(rank_discounted_mean(authority_scores), 5)
        query_overall = round(
            WEIGHTS["relevance"] * query_relevance
            + WEIGHTS["effectiveness"] * query_effectiveness
            + WEIGHTS["authority"] * query_authority,
            5,
        )

        labels = []
        if query_overall < args.overall_threshold:
            labels.append("QUALITY_BAD.SEARCH_RESULT_OVERALL_LOW")
        if query_relevance < args.relevance_threshold:
            labels.append("QUALITY_BAD.SEARCH_RESULT_RELEVANCE_LOW")
        relevance_errors = sum(1 for row in rows if row["relevance_error"])
        if relevance_errors:
            labels.append("QUALITY_BAD.SEARCH_RESULT_RELEVANCE_PARSE_ERROR")
        if query_effectiveness < args.effectiveness_threshold:
            labels.append("QUALITY_BAD.SEARCH_RESULT_EFFECTIVENESS_LOW")
        if query_authority < args.authority_threshold:
            labels.append("QUALITY_BAD.SEARCH_RESULT_AUTHORITY_LOW")

        eval_status = bool(labels)
        if not labels:
            labels = ["QUALITY_GOOD.SEARCH_RESULT_OVERALL_PASS"]

        query_row = {
            "query": query,
            "result_count": len(rows),
            "valid_relevance_count": len(rows) - relevance_errors,
            "relevance_error_count": relevance_errors,
            "relevance": query_relevance,
            "relevance_aggregation": relevance_aggregation,
            "effectiveness": query_effectiveness,
            "authority": query_authority,
            "overall": query_overall,
            "eval_status": eval_status,
            "label": "|".join(labels),
        }
        query_rows.append(query_row)
        detail = {**query_row, "results": rows}
        detailed.append(detail)
        classified_records.append({
            "query": query,
            "metric": "search_result_quality",
            "score": query_overall,
            "threshold": args.overall_threshold,
            "eval_status": eval_status,
            "labels": labels,
            "relevance": query_relevance,
            "relevance_aggregation": relevance_aggregation,
            "effectiveness": query_effectiveness,
            "authority": query_authority,
            "relevance_error_count": relevance_errors,
            "thresholds": {
                "relevance": args.relevance_threshold,
                "effectiveness": args.effectiveness_threshold,
                "authority": args.authority_threshold,
                "overall": args.overall_threshold,
            },
            "results": rows,
        })

    for query in empty_queries or []:
        labels = ["QUALITY_BAD.SEARCH_RESULT_EMPTY"]
        query_row = {
            "query": query,
            "result_count": 0,
            "valid_relevance_count": 0,
            "relevance_error_count": 0,
            "relevance": 0.0,
            "relevance_aggregation": (
                "doi_exact_match_rank_discount" if is_doi_query(query) else "rank_discounted_mean"
            ),
            "effectiveness": 0.0,
            "authority": 0.0,
            "overall": 0.0,
            "eval_status": True,
            "label": labels[0],
        }
        query_rows.append(query_row)
        detailed.append({**query_row, "results": []})
        classified_records.append({
            "query": query,
            "metric": "search_result_quality",
            "score": 0.0,
            "threshold": args.overall_threshold,
            "eval_status": True,
            "labels": labels,
            "relevance": 0.0,
            "relevance_aggregation": (
                "doi_exact_match_rank_discount" if is_doi_query(query) else "rank_discounted_mean"
            ),
            "effectiveness": 0.0,
            "authority": 0.0,
            "relevance_error_count": 0,
            "thresholds": {
                "relevance": args.relevance_threshold,
                "effectiveness": args.effectiveness_threshold,
                "authority": args.authority_threshold,
                "overall": args.overall_threshold,
            },
            "results": [],
        })

    summary = {
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "metric": "search_result_quality",
        "top_k": args.top_k,
        "weights": WEIGHTS,
        "thresholds": {
            "relevance": args.relevance_threshold,
            "effectiveness": args.effectiveness_threshold,
            "authority": args.authority_threshold,
            "overall": args.overall_threshold,
        },
        "llm": {
            "model": args.openai_model,
            "prompt_mode": args.prompt_mode,
            "max_tokens": args.llm_max_tokens,
            "temperature": args.openai_temperature,
            "timeout": args.llm_timeout,
            "workers": args.llm_workers,
            "effectiveness_llm_quality_enabled": not args.disable_effectiveness_llm_quality,
            "effectiveness_llm_max_tokens": args.effectiveness_llm_max_tokens,
        },
        "run_output_path": str(executor_summary.output_path),
        "metrics": {
            "relevance": summarize([float(row["relevance"]) for row in query_rows]),
            "effectiveness": summarize([float(row["effectiveness"]) for row in query_rows]),
            "authority": summarize([float(row["authority"]) for row in query_rows]),
            "overall": summarize([float(row["overall"]) for row in query_rows]),
        },
        "query_count": len(query_rows),
        "result_count": len(result_rows),
        "rank_relevance_error_count": rank_relevance_error_count,
        "rank_effectiveness_llm_quality_error_count": rank_effectiveness_llm_quality_error_count,
        "num_bad": sum(1 for row in query_rows if row["eval_status"]),
        "num_good": sum(1 for row in query_rows if not row["eval_status"]),
    }
    if executor_result_summary:
        summary["result_level"] = {
            "score": executor_result_summary.get("score"),
            "num_good": executor_result_summary.get("num_good"),
            "num_bad": executor_result_summary.get("num_bad"),
            "total": executor_result_summary.get("total"),
            "type_ratio": executor_result_summary.get("type_ratio", {}),
            "metrics_score": executor_result_summary.get("metrics_score", {}),
        }
    return summary, query_rows, result_rows, detailed, classified_records


def normalize_executor_summary(executor_output_path: str, records: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Make executor summary label ratios use record-level quality semantics.

    LocalExecutor counts every EvalDetail label. In this combined script one
    result has three metrics, so a bad result can still contain QUALITY_GOOD
    from the metrics that passed. This rewrite keeps error labels as
    per-result occurrence rates, but makes QUALITY_GOOD mutually exclusive.
    """
    total = len(records)
    if total == 0:
        return None

    field_key = "search_result"
    counts: dict[str, int] = {}
    for record in records:
        labels = set()
        for detail in record.get("eval_details", {}).get(field_key, []):
            for label in detail.get("label") or []:
                labels.add(label)

        if record.get("eval_status"):
            labels.discard("QUALITY_GOOD")
        else:
            labels = {"QUALITY_GOOD"}

        for label in labels:
            counts[label] = counts.get(label, 0) + 1

    summary_path = Path(executor_output_path) / "summary.json"
    if not summary_path.exists():
        return None

    summary = json.loads(summary_path.read_text(encoding="utf-8-sig"))
    summary.setdefault("type_ratio", {})[field_key] = {
        label: round(count / total, 6)
        for label, count in sorted(counts.items())
    }
    return summary


def build_result_classified_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Expose executor result labels for result-level directory output."""
    classified: list[dict[str, Any]] = []
    for record in records:
        labels: list[str] = []
        for details in record.get("eval_details", {}).values():
            for detail in details:
                for label in detail.get("label") or []:
                    if label != "QUALITY_GOOD" and label not in labels:
                        labels.append(label)

        eval_status = bool(labels)
        if not labels:
            labels = ["QUALITY_GOOD"]
        classified.append({**record, "eval_status": eval_status, "labels": labels})
    return classified


def main() -> None:
    args = parse_args()
    os.environ.setdefault("LOCAL_DEPLOYMENT_MODE", "true")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    flattened_path = args.output_dir / f".search_result_quality_input_{int(time.time())}_{os.getpid()}.jsonl"
    try:
        total, empty_queries = flatten_query_results(
            args.input_jsonl,
            flattened_path,
            top_k=args.top_k,
            max_queries=args.max_queries,
        )
        if total == 0:
            raise ValueError("No search results found to evaluate.")

        input_data = build_executor_input(args, flattened_path)
        executor_summary = Executor.exec_map["local"](InputArgs(**input_data)).execute()
        run_dir = Path(executor_summary.output_path)
        executor_records = load_executor_records(executor_summary.output_path)
        executor_result_summary = normalize_executor_summary(executor_summary.output_path, executor_records)
        summary, query_rows, result_rows, detailed, classified_records = build_reports(
            executor_records,
            args,
            executor_summary,
            executor_result_summary,
            empty_queries,
        )

        write_json(run_dir / "summary.json", summary)
        if args.save_detailed:
            write_json(run_dir / "detailed_results.json", {"summary": summary, "queries": detailed})
        write_csv(run_dir / "query_scores.csv", query_rows)
        write_csv(run_dir / "result_scores.csv", result_rows)
        write_classified_jsonl(
            run_dir,
            classified_records,
            save_good=args.save_good,
            level="query_level",
        )
        write_classified_jsonl(
            run_dir,
            build_result_classified_records(executor_records),
            save_good=args.save_good,
            level="result_level",
        )
        print(f"Saved to {run_dir.resolve()}")
    finally:
        if flattened_path.exists():
            flattened_path.unlink()


if __name__ == "__main__":
    main()
