"""
Article Fact-Checking Example using ArticleFactChecker Agent.

Usage:
    python examples/agent/agent_article_fact_checking_example.py

Requirements:
    - OPENAI_API_KEY: For LLM agent and claims extraction
    - TAVILY_API_KEY: (Optional) For web search verification
"""

import json
import os
import tempfile

from dingo.config import InputArgs
from dingo.exec import Executor


def main() -> int:
    """Run article fact-checking example."""

    # Verify API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("ERROR: OPENAI_API_KEY environment variable not set")
        print("\nSet it with:")
        print("  export OPENAI_API_KEY='your-api-key'")
        return 1

    tavily_key = os.getenv("TAVILY_API_KEY")
    if not tavily_key:
        print("WARNING: TAVILY_API_KEY not set - web search verification will be limited")
        print("   Set it with: export TAVILY_API_KEY='your-api-key'")

    # Read the complete article (Markdown input)
    article_path = "test/data/blog_article_full.md"
    if not os.path.exists(article_path):
        print(f"ERROR: Article file not found: {article_path}")
        return 1

    with open(article_path, 'r', encoding='utf-8') as f:
        article_content = f.read()

    # Wrap article in JSONL so Executor treats it as a single Data object.
    temp_jsonl = tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False, encoding='utf-8')
    temp_jsonl.write(json.dumps({"content": article_content}, ensure_ascii=False) + '\n')
    temp_jsonl.close()

    # Configuration for ArticleFactChecker
    config = {
        "input_path": temp_jsonl.name,
        "dataset": {
            "source": "local",
            "format": "jsonl"
        },
        "executor": {
            "max_workers": 1
        },
        "evaluator": [
            {
                "fields": {
                    "content": "content"
                },
                "evals": [
                    {
                        "name": "ArticleFactChecker",
                        "config": {
                            "key": openai_key,
                            "api_url": "https://api.deepseek.com/v1",
                            "model": "deepseek-chat",
                            "parameters": {
                                "timeout": 600,
                                "temperature": 0,  # deterministic output
                                "agent_config": {
                                    "max_iterations": 100,
                                    # Artifacts auto-saved to outputs/article_factcheck_<timestamp>/
                                    # Override with: "output_path": "your/custom/path"
                                    "tools": {
                                        "claims_extractor": {
                                            "api_key": openai_key,
                                            "model": "deepseek-chat",
                                            "base_url": "https://api.deepseek.com/v1",
                                            "max_claims": 100,
                                            "claim_types": [
                                                "factual", "statistical", "attribution", "institutional",
                                                "temporal", "comparative", "monetary", "technical"
                                            ]
                                        },
                                        "tavily_search": {
                                            "api_key": tavily_key
                                        } if tavily_key else {},
                                        "arxiv_search": {
                                            "max_results": 5
                                        }
                                    }
                                }
                            }
                        }
                    }
                ]
            }
        ]
    }

    print("Starting Article Fact-Checking")
    print("=" * 70)
    print(f"Article: {article_path} (via temp JSONL)")
    print("Agent: ArticleFactChecker (Agent-First architecture)")
    print(f"Model: {config['evaluator'][0]['evals'][0]['config']['model']}")
    print("Artifact output: outputs/article_factcheck_<timestamp>/ (auto-generated)")
    print("=" * 70)

    # Create input args and executor
    input_args = InputArgs(**config)
    executor = Executor.exec_map["local"](input_args)

    try:
        # Execute fact-checking
        print("\nExecuting agent-based fact-checking...\n")

        result = executor.execute()

        # Display results
        print("\n" + "=" * 70)
        print("FACT-CHECKING RESULTS")
        print("=" * 70)

        if result and hasattr(result, 'eval_details'):
            for item_id, details_by_field in result.eval_details.items():
                for field_key, eval_details in details_by_field.items():
                    for eval_detail in eval_details:
                        if eval_detail.metric == "ArticleFactChecker":
                            print(f"\nMetric: {eval_detail.metric}")
                            print(f"Status: {'Issues Found' if eval_detail.status else 'All Good'}")
                            if eval_detail.score is not None:
                                print(f"Accuracy Score: {eval_detail.score:.2%}")
                            print("\nDetailed Report:")
                            print("-" * 70)
                            if eval_detail.reason:
                                print(eval_detail.reason[0] if isinstance(eval_detail.reason[0], str) else str(eval_detail.reason[0]))

                                if len(eval_detail.reason) > 1 and isinstance(eval_detail.reason[1], dict):
                                    report = eval_detail.reason[1]
                                    print("\nStructured Report Summary:")
                                    print(f"  Report Version: {report.get('report_version', 'N/A')}")
                                    v_summary = report.get('verification_summary', {})
                                    print(f"  Verified True:  {v_summary.get('verified_true', 'N/A')}")
                                    print(f"  Verified False: {v_summary.get('verified_false', 'N/A')}")
                                    print(f"  Unverifiable:   {v_summary.get('unverifiable', 'N/A')}")
                                    c_extraction = report.get('claims_extraction', {})
                                    print(f"  Claims Extracted: {c_extraction.get('total_extracted', 'N/A')}")
                                    meta = report.get('agent_metadata', {})
                                    print(f"  Execution Time: {meta.get('execution_time_seconds', 'N/A')}s")
                            print("-" * 70)

        print("\nFact-checking complete!")
        print(f"\nDingo standard output: {input_args.output_path}/")
        print("  |-- summary.json                  (aggregated statistics)")
        print("  +-- content/<LABEL>.jsonl          (results grouped by quality label)")

        print("\nIntermediate artifacts: outputs/article_factcheck_<timestamp>_<uuid>/")
        print("  |-- article_content.md           (original Markdown article)")
        print("  |-- claims_extracted.jsonl        (extracted claims, one per line)")
        print("  |-- claims_verification.jsonl     (per-claim verification details)")
        print("  +-- verification_report.json      (full structured report)")
        print("\nNote: Override artifact path with agent_config.output_path in config")

    finally:
        try:
            os.unlink(temp_jsonl.name)
        except OSError:
            pass

    return 0


if __name__ == "__main__":
    exit(main())
