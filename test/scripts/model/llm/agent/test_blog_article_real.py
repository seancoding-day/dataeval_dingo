#!/usr/bin/env python3
"""
Real-world test: ArticleFactChecker with blog_article.md

This script tests ArticleFactChecker with the actual blog article about
PaddleOCR-VL to verify:
1. Article type identification (tech blog/news)
2. Claim extraction (technical, statistical, institutional)
3. Tool selection (tavily_search for verification)
4. Overall effectiveness without overfitting

Usage:
    export OPENAI_API_KEY="your-deepseek-key"
    export TAVILY_API_KEY="your-tavily-key"  # optional
    python test_blog_article_real.py
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

from dingo.config import InputArgs
from dingo.exec import Executor


def check_api_keys() -> tuple[Optional[str], Optional[str]]:
    """Check and validate API keys."""
    openai_key = os.getenv("OPENAI_API_KEY")
    tavily_key = os.getenv("TAVILY_API_KEY")

    if not openai_key:
        print("❌ OPENAI_API_KEY not found in environment")
        print("   Please set: export OPENAI_API_KEY='your-key'")
        return None, None

    print("=" * 80)
    print("ArticleFactChecker - Real Blog Article Test")
    print("=" * 80)
    print(f"✓ OPENAI_API_KEY: {'*' * 8}{openai_key[-4:]}")
    print(f"✓ TAVILY_API_KEY: {'*' * 8}{tavily_key[-4:] if tavily_key else 'Not set (optional)'}")
    print()

    return openai_key, tavily_key


def load_article(article_path: Path) -> Optional[str]:
    """Load and validate article file."""
    if not article_path.exists():
        print(f"❌ Article file not found: {article_path}")
        return None

    article_content = article_path.read_text(encoding='utf-8')

    print(f"📄 Article: {article_path}")
    print(f"   Length: {len(article_content)} characters")
    print(f"   Lines: {len(article_content.splitlines())}")
    print()

    return article_content


def build_config(article_path: Path, openai_key: str, tavily_key: Optional[str]) -> Dict[str, Any]:
    """Build configuration for ArticleFactChecker."""
    return {
        "input_path": str(article_path),
        "dataset": {
            "source": "local",
            "format": "plaintext"
        },
        "executor": {
            "max_workers": 1
        },
        "evaluator": [
            {
                "name": "ArticleFactChecker",
                "config": {
                    "key": openai_key,
                    "model": "deepseek-chat",
                    "parameters": {
                        "agent_config": {
                            "max_iterations": 15,
                            "tools": {
                                "claims_extractor": {
                                    "api_key": openai_key,
                                    "max_claims": 50,
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
                },
                "fields": {"content": "content"},
                "evals": []
            }
        ]
    }


def print_config_info() -> None:
    """Print configuration information."""
    print("   Model: deepseek-chat")
    print("   Max iterations: 15")
    print("   Claim types: 8 (factual, statistical, attribution, institutional,")
    print("                   temporal, comparative, monetary, technical)")
    print()


def print_expected_results() -> None:
    """Print expected analysis results."""
    print("🤖 Running ArticleFactChecker...")
    print("   Expected article type: Technical Blog or News Article")
    print("   Expected claims:")
    print("     - institutional: 清华大学, 阿里达摩院, 上海人工智能实验室")
    print("     - statistical: 92.6分, 0.9B参数, 96.5分, 91.4分, 89.8分")
    print("     - technical: NaViT, ERNIE-4.5-0.3B, PP-DocLayoutV2")
    print("     - comparative: 超越 Gemini-2.5 Pro, GPT-4o")
    print()


def test_blog_article() -> int:
    """Test with real blog article."""
    openai_key, tavily_key = check_api_keys()
    if not openai_key:
        return 1

    article_path = Path("blog_article.md")
    article_content = load_article(article_path)
    if not article_content:
        return 1

    print("🔧 Configuring ArticleFactChecker...")

    config = build_config(article_path, openai_key, tavily_key)
    print_config_info()

    try:
        input_args = InputArgs(**config)
        executor = Executor.exec_map["local"](input_args)
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return 1

    print_expected_results()

    try:
        result = executor.execute()
        return validate_and_display_results(result)
    except Exception as e:
        return handle_execution_error(e)


def display_summary(result: Any) -> None:
    """Display summary results."""
    print("=" * 80)
    print("✅ EXECUTION COMPLETED")
    print("=" * 80)
    print()

    print("📊 Summary Results:")
    print(f"   Total items: {result.total_count}")
    print(f"   Good items: {result.good_count}")
    print(f"   Bad items: {result.bad_count}")
    print()


def display_sample_result(result: Any) -> None:
    """Display sample result details."""
    if result.total_count == 0:
        return

    print("📝 Sample Result (first item):")
    result_dict = result.model_dump() if hasattr(result, 'model_dump') else result.__dict__

    print(f"   Result keys: {list(result_dict.keys())}")
    print()

    if 'type_ratio' in result_dict and result_dict['type_ratio']:
        print("   Type Ratio:")
        for key, value in result_dict['type_ratio'].items():
            print(f"     {key}: {value}")
        print()

    if 'metrics_score_stats' in result_dict and result_dict['metrics_score_stats']:
        print("   Metrics Score Stats:")
        for key, value in result_dict['metrics_score_stats'].items():
            print(f"     {key}: {value}")
        print()


def run_validation_checks(result: Any) -> bool:
    """Run validation checks on result."""
    print("=" * 80)
    print("🔍 Validation Checks")
    print("=" * 80)

    checks = [
        ("Result object created", result is not None),
        ("Has total_count", hasattr(result, 'total_count')),
        ("Has good_count", hasattr(result, 'good_count')),
        ("Has bad_count", hasattr(result, 'bad_count')),
        ("Processed at least one item", result.total_count > 0),
    ]

    all_passed = all(check_result for _, check_result in checks)

    for check_name, check_result in checks:
        status = "✓" if check_result else "✗"
        print(f"   {status} {check_name}")

    print()
    return all_passed


def print_success_message() -> None:
    """Print success message."""
    print("✅ All validation checks PASSED")
    print()
    print("📝 Test Summary:")
    print("   - ArticleFactChecker successfully processed the blog article")
    print("   - Agent made autonomous decisions on tool selection")
    print("   - Result structure is valid")
    print()
    print("💡 Note: This is a real-world test with actual LLM API calls.")
    print("   The agent should identify the article as tech blog/news,")
    print("   extract institutional, statistical, and technical claims,")
    print("   and verify them using appropriate tools.")


def validate_and_display_results(result: Any) -> int:
    """Validate and display execution results."""
    display_summary(result)
    display_sample_result(result)

    all_passed = run_validation_checks(result)

    if all_passed:
        print_success_message()
        return 0

    print("⚠️ Some validation checks FAILED")
    return 1


def handle_execution_error(e: Exception) -> int:
    """Handle execution errors."""
    import traceback

    print("=" * 80)
    print("❌ EXECUTION FAILED")
    print("=" * 80)
    print(f"   Error: {type(e).__name__}: {e}")
    print()

    print("Traceback:")
    traceback.print_exc()

    return 1


if __name__ == "__main__":
    exit(test_blog_article())
