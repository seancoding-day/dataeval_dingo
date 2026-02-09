#!/usr/bin/env python3
"""
Verify ArticleFactChecker setup without API calls.

Checks:
1. Component imports
2. Claim types configuration
3. Test data files
4. Blog article content
5. API keys (optional)
6. Configuration structure

Usage:
    python verify_setup.py
"""

import os
from pathlib import Path
from typing import List, Tuple


def check_imports(imports: List[Tuple[str, str]]) -> bool:
    """Verify all imports work."""
    print("1. Import Checks")
    print("-" * 40)

    all_passed = True
    for name, import_stmt in imports:
        try:
            exec(import_stmt)
            print(f"   ✓ {name}")
        except Exception as e:
            print(f"   ✗ {name}: {e}")
            all_passed = False

    print()
    return all_passed


def check_claim_types() -> bool:
    """Verify claim types are expanded to 8."""
    print("2. Claim Types Verification")
    print("-" * 40)

    try:
        from dingo.model.llm.agent.tools.claims_extractor import ClaimsExtractor

        claim_types = ClaimsExtractor.config.claim_types
        expected = [
            'factual', 'statistical', 'attribution', 'institutional',
            'temporal', 'comparative', 'monetary', 'technical'
        ]

        if len(claim_types) == 8:
            print(f"   ✓ Claim types count: {len(claim_types)}")
        else:
            print(f"   ✗ Claim types count: {len(claim_types)} (expected 8)")
            print()
            return False

        missing = set(expected) - set(claim_types)
        if missing:
            print(f"   ✗ Missing types: {missing}")
            print()
            return False

        print(f"   ✓ All expected types present")
        print()
        return True

    except Exception as e:
        print(f"   ✗ Error checking claim types: {e}")
        print()
        return False


def check_test_data_files() -> bool:
    """Verify test data files exist."""
    print("3. Test Data Files")
    print("-" * 40)

    data_files = [
        ("test/data/news_article_excerpt.md", "News article"),
        ("test/data/product_review_excerpt.md", "Product review"),
        ("test/data/blog_article_excerpt.md", "Blog excerpt"),
        ("test/data/blog_article.md", "Full blog article"),
    ]

    all_passed = True
    for filepath, desc in data_files:
        path = Path(filepath)
        if path.exists():
            size = path.stat().st_size
            print(f"   ✓ {desc}: {filepath} ({size} bytes)")
        else:
            print(f"   ✗ {desc}: {filepath} not found")
            all_passed = False

    print()
    return all_passed


def check_blog_article() -> bool:
    """Verify blog article content."""
    print("4. Blog Article Analysis")
    print("-" * 40)

    blog_path = Path("test/data/blog_article.md")
    if not blog_path.exists():
        print(f"   ✗ Blog article not found")
        print()
        return False

    content = blog_path.read_text(encoding='utf-8')

    print(f"   ✓ File loaded successfully")
    print(f"   - Total length: {len(content)} characters")
    print(f"   - Lines: {len(content.splitlines())}")

    keywords = [
        ("PaddleOCR-VL", "Model name"),
        ("OmniDocBench", "Benchmark name"),
        ("清华大学", "Institution 1"),
        ("阿里达摩院", "Institution 2"),
        ("上海人工智能实验室", "Institution 3"),
        ("92.6", "Score"),
        ("0.9B", "Model size"),
    ]

    print(f"   - Keyword checks:")
    all_found = True
    for keyword, desc in keywords:
        if keyword in content:
            print(f"     ✓ {desc}: '{keyword}'")
        else:
            print(f"     ✗ {desc}: '{keyword}' not found")
            all_found = False

    print()
    return all_found


def check_api_keys() -> None:
    """Check API keys (non-blocking)."""
    print("5. API Keys (Optional)")
    print("-" * 40)

    openai_key = os.getenv("OPENAI_API_KEY")
    tavily_key = os.getenv("TAVILY_API_KEY")

    if openai_key:
        print(f"   ✓ OPENAI_API_KEY: {'*' * 8}{openai_key[-4:]}")
    else:
        print(f"   ⚠ OPENAI_API_KEY: Not set (required for actual testing)")

    if tavily_key:
        print(f"   ✓ TAVILY_API_KEY: {'*' * 8}{tavily_key[-4:]}")
    else:
        print(f"   ⚠ TAVILY_API_KEY: Not set (optional)")

    print()


def check_configuration() -> bool:
    """Verify configuration structure."""
    print("6. Configuration Structure")
    print("-" * 40)

    try:
        from dingo.config import InputArgs

        test_config = {
            "input_path": "test/data/blog_article.md",
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
                        "key": "test-key",
                        "model": "deepseek-chat",
                        "parameters": {
                            "agent_config": {
                                "max_iterations": 15,
                                "tools": {
                                    "claims_extractor": {
                                        "api_key": "test-key",
                                        "max_claims": 50,
                                        "claim_types": [
                                            "factual", "statistical", "attribution", "institutional",
                                            "temporal", "comparative", "monetary", "technical"
                                        ]
                                    },
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

        input_args = InputArgs(**test_config)
        print(f"   ✓ InputArgs validation passed")
        print(f"   ✓ Evaluator count: {len(input_args.evaluator)}")

        if input_args.evaluator:
            print(f"   ✓ Evaluators configured successfully")

        print()
        return True

    except Exception as e:
        print(f"   ✗ Configuration validation failed: {e}")
        print()
        return False


def main() -> int:
    """Run all verification checks."""
    print("=" * 80)
    print("ArticleFactChecker Setup Verification")
    print("=" * 80)
    print()

    imports = [
        ("Data class", "from dingo.io.input.data import Data"),
        ("ArticleFactChecker", "from dingo.model.llm.agent.agent_article_fact_checker import ArticleFactChecker"),
        ("ClaimsExtractor", "from dingo.model.llm.agent.tools.claims_extractor import ClaimsExtractor"),
        ("InputArgs", "from dingo.config import InputArgs"),
        ("Executor", "from dingo.exec import Executor"),
    ]

    results = [
        check_imports(imports),
        check_claim_types(),
        check_test_data_files(),
        check_blog_article(),
        check_configuration(),
    ]

    check_api_keys()  # Non-blocking

    print("=" * 80)
    if all(results):
        print("✅ ALL CHECKS PASSED")
        print()
        print("Setup is ready for ArticleFactChecker testing!")
        print()
        print("Next steps:")
        print("  1. Set API keys if not already set:")
        print("     export OPENAI_API_KEY='your-deepseek-key'")
        print("     export TAVILY_API_KEY='your-tavily-key'")
        print()
        print("  2. Run real test:")
        print("     python test_blog_article_real.py")
        return 0
    else:
        print("⚠️ SOME CHECKS FAILED")
        print()
        print("Please fix the issues above before proceeding.")
        return 1


if __name__ == "__main__":
    exit(main())
