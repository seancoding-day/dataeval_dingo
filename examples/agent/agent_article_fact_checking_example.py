"""
Article Fact-Checking Example using ArticleFactChecker Agent.

This example demonstrates how to use the ArticleFactChecker agent to
comprehensively verify factual claims in long-form articles.

The agent autonomously:
1. Extracts verifiable claims using ClaimsExtractor
2. Selects appropriate verification tools (arxiv_search, tavily_search)
3. Verifies institutional attributions and other claims
4. Generates a structured verification report

Output Files:
=============
Dingo standard output (always generated, saved to executor output_path):
- all_results.jsonl           : Dingo standard EvalDetail output
- summary.json               : Dingo standard summary

Intermediate artifacts (only when agent_config.output_path is set):
- article_content.md         : Original Markdown article
- claims_extracted.jsonl     : Extracted claims (one per line)
- claims_verification.jsonl  : Per-claim verification details
- verification_report.json   : Full structured report (v2.0)

Usage:
    python examples/agent/agent_article_fact_checking_example.py

Requirements:
    - OPENAI_API_KEY: For claims extraction and LLM agent
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
    article_path = "test/data/blog_article.md"
    if not os.path.exists(article_path):
        print(f"ERROR: Article file not found: {article_path}")
        return 1

    with open(article_path, 'r', encoding='utf-8') as f:
        article_content = f.read()

    # Create temporary JSONL file with complete article.
    # JSONL is needed because Executor requires input_path, and plaintext format
    # reads line-by-line (each line becomes a separate Data object), which would
    # split the article. JSONL keeps the entire article as one Data object since
    # json.dumps encodes newlines as \n within a single JSON line.
    temp_jsonl = tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False, encoding='utf-8')
    temp_jsonl.write(json.dumps({"content": article_content}, ensure_ascii=False) + '\n')
    temp_jsonl.close()

    # Where to save intermediate artifacts (claims, verification details, report).
    # Set to a directory path to enable artifact saving.
    # If set to None, only Dingo standard output (all_results.jsonl, summary.json) is generated.
    artifact_output_path = "outputs/article_factcheck/"

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
                                "timeout": 120,
                                "agent_config": {
                                    "max_iterations": 30,
                                    # output_path controls intermediate artifact saving.
                                    # When set, saves: article_content.md, claims_extracted.jsonl,
                                    # claims_verification.jsonl, verification_report.json
                                    # When omitted/None, only Dingo standard output is generated.
                                    "output_path": artifact_output_path,
                                    "tools": {
                                        "claims_extractor": {
                                            "api_key": openai_key,
                                            "model": "deepseek-chat",
                                            "base_url": "https://api.deepseek.com/v1",
                                            "max_claims": 30,  # Lower for quick demo, raise for thorough check
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
    if artifact_output_path:
        print(f"Artifact output: {artifact_output_path}")
    print("=" * 70)

    # Create input args and executor
    input_args = InputArgs(**config)
    executor = Executor.exec_map["local"](input_args)

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
                            # reason[0]: human-readable text summary (always present)
                            print(eval_detail.reason[0] if isinstance(eval_detail.reason[0], str) else str(eval_detail.reason[0]))

                            # reason[1]: structured report dict (present when output_path is set)
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

    # Show output locations
    print("\nFact-checking complete!")

    # Dingo standard output (always present)
    print(f"\nDingo standard output: {input_args.output_path}/")
    print("  |-- all_results.jsonl             (EvalDetail with dual-layer reason)")
    print("  +-- summary.json                  (aggregated statistics)")

    # Intermediate artifacts (only when output_path is configured)
    if artifact_output_path:
        print(f"\nIntermediate artifacts: {artifact_output_path}")
        print("  |-- article_content.md           (original Markdown article)")
        print("  |-- claims_extracted.jsonl        (extracted claims, one per line)")
        print("  |-- claims_verification.jsonl     (per-claim verification details)")
        print("  +-- verification_report.json      (full structured report v2.0)")
    else:
        print("\nNote: Set agent_config.output_path to save intermediate artifacts")
        print("      (claims, verification details, structured report)")

    # Cleanup temporary file
    try:
        os.unlink(temp_jsonl.name)
    except OSError:
        pass

    return 0


if __name__ == "__main__":
    exit(main())
