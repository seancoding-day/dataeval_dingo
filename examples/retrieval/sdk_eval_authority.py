"""Run search result authority evaluation through Dingo LocalExecutor."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dingo.config import InputArgs
from dingo.exec import Executor

from search_result_eval_utils import add_common_args, get_title, load_query_result_jsonl


EVALUATOR_NAME = "LLMSearchResultAuthority"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate search result authority with Dingo executor.")
    add_common_args(parser)
    parser.add_argument("--threshold", type=float, default=0.15)
    parser.add_argument("--max-workers", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument(
        "--raw-output",
        action="store_true",
        help="Write executor records with raw data merged into top-level JSONL rows.",
    )
    return parser.parse_args()


def flatten_query_results(input_path: Path, output_path: Path, *, top_k: int, max_queries: int | None) -> int:
    items = load_query_result_jsonl(input_path, max_queries)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with output_path.open("w", encoding="utf-8") as f:
        for query_index, item in enumerate(items, start=1):
            query = item["query"]
            for rank, result in enumerate(item["results"][:top_k], start=1):
                row: dict[str, Any] = {
                    "query": query,
                    "query_index": query_index,
                    "rank": rank,
                    "title": get_title(result),
                    "search_result": result,
                }
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                count += 1
    return count


def build_input_data(args: argparse.Namespace, flattened_path: Path) -> dict[str, Any]:
    return {
        "task_name": "search_result_authority",
        "input_path": str(flattened_path),
        "output_path": str(args.output_dir),
        "dataset": {"source": "local", "format": "jsonl"},
        "executor": {
            "max_workers": args.max_workers,
            "batch_size": args.batch_size,
            "result_save": {
                "bad": True,
                "good": args.save_good,
                "all_labels": True,
                "raw": args.raw_output,
            },
        },
        "evaluator": [
            {
                "fields": {"search_result": "search_result"},
                "evals": [{"name": EVALUATOR_NAME, "config": {"threshold": args.threshold}}],
            }
        ],
    }


def main() -> None:
    args = parse_args()
    os.environ.setdefault("LOCAL_DEPLOYMENT_MODE", "true")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    flattened_path = args.output_dir / "meta_search_flattened_authority_input.jsonl"
    total = flatten_query_results(
        args.input_jsonl,
        flattened_path,
        top_k=args.top_k,
        max_queries=args.max_queries,
    )
    if total == 0:
        raise ValueError("No search results found to evaluate.")

    summary = Executor.exec_map["local"](InputArgs(**build_input_data(args, flattened_path))).execute()
    print(summary)
    print(f"[Done] flattened_input={flattened_path.resolve()}")
    print(f"[Done] executor_output={summary.output_path}")


if __name__ == "__main__":
    main()
