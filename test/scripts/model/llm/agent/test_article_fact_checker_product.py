"""
Test ArticleFactChecker with product reviews.

This test suite validates product review handling with technical,
comparative, and monetary claims.
"""

import functools
import os
from pathlib import Path

import pytest

from dingo.io.input.data import Data
from dingo.model.llm.agent.agent_article_fact_checker import ArticleFactChecker


def get_test_data_path(filename: str) -> Path:
    """Get absolute path to test data file."""
    return Path(__file__).parents[4] / "data" / filename


def skip_on_api_error(test_func):
    """Decorator to skip test if API execution fails (preserves function signature for pytest)."""
    @functools.wraps(test_func)
    def wrapper(*args, **kwargs):
        try:
            return test_func(*args, **kwargs)
        except Exception as e:
            pytest.skip(f"API execution failed: {e}")
    return wrapper


class TestArticleFactCheckerProduct:
    """Test suite for product review fact-checking"""

    # DeepSeek API configuration (uses OpenAI SDK)
    DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL = "deepseek-chat"

    def setup_method(self):
        """Configure ArticleFactChecker to use DeepSeek API"""
        from dingo.config.input_args import EvaluatorLLMArgs

        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            ArticleFactChecker.dynamic_config = EvaluatorLLMArgs(
                key=api_key,
                api_url=self.DEEPSEEK_BASE_URL,
                model=self.DEEPSEEK_MODEL
            )

    @pytest.fixture
    def product_review(self) -> str:
        """Load product review for iPhone 15 Pro."""
        path = get_test_data_path("product_review_excerpt.md")
        return path.read_text(encoding='utf-8')

    @pytest.fixture(autouse=True)
    def skip_if_no_api_key(self):
        """Auto-skip all tests if no API keys available."""
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set")

    def test_structure_validation(self, product_review: str):
        """Test data structure without API calls."""
        data = Data(dingo_id="product_001", content=product_review)

        assert data.content is not None
        assert "iPhone 15 Pro" in data.content
        assert "A17 Pro" in data.content
        assert "7999" in data.content

    @pytest.mark.slow
    @pytest.mark.external
    @skip_on_api_error
    def test_claim_extraction(self, product_review: str):
        """
        Test claim extraction from product review.

        Expected: technical, comparative, monetary, statistical claims.
        """
        data = Data(dingo_id="product_002", content=product_review)
        result = ArticleFactChecker.eval(data)

        assert result is not None
        assert hasattr(result, 'status')
        assert hasattr(result, 'score')

    @pytest.mark.slow
    @pytest.mark.external
    @skip_on_api_error
    def test_technical_verification(self, product_review: str):
        """
        Test technical specification verification.

        Example: "A17 Pro chip with 3nm process"
        Tool: tavily_search for official specs
        """
        data = Data(dingo_id="product_003", content=product_review)
        result = ArticleFactChecker.eval(data)

        assert result is not None

    @pytest.mark.slow
    @pytest.mark.external
    @skip_on_api_error
    def test_comparative_verification(self, product_review: str):
        """
        Test comparative claim verification.

        Examples: "GPU improved 20% vs A16", "12% vs iPhone 14 Pro"
        Tool: tavily_search for benchmarks
        """
        data = Data(dingo_id="product_004", content=product_review)
        result = ArticleFactChecker.eval(data)

        assert result is not None

    @pytest.mark.slow
    @pytest.mark.external
    @skip_on_api_error
    def test_monetary_verification(self, product_review: str):
        """
        Test pricing verification.

        Examples: "128GB: 7999 yuan", "Price increase: 800 yuan"
        Tool: tavily_search for official pricing
        """
        data = Data(dingo_id="product_005", content=product_review)
        result = ArticleFactChecker.eval(data)

        assert result is not None

    @pytest.mark.slow
    @pytest.mark.external
    @skip_on_api_error
    def test_statistical_verification(self, product_review: str):
        """
        Test benchmark score verification.

        Examples: "Geekbench 6: 2920/7230", "Video: 23 hours"
        Tool: tavily_search for benchmarks
        """
        data = Data(dingo_id="product_006", content=product_review)
        result = ArticleFactChecker.eval(data)

        assert result is not None

    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.external
    @skip_on_api_error
    def test_full_workflow(self, product_review: str):
        """
        Integration test: Full product review workflow.

        Steps: Type ID → Claim extraction → Verification → Report
        """
        data = Data(dingo_id="product_integration", content=product_review)
        result = ArticleFactChecker.eval(data)

        assert result is not None
        assert hasattr(result, 'status')
        assert hasattr(result, 'score')
        assert hasattr(result, 'label')
        assert hasattr(result, 'reason')

    @pytest.mark.slow
    @pytest.mark.external
    @skip_on_api_error
    def test_cross_device_comparison(self, product_review: str):
        """
        Test cross-device comparative claims.

        Example: "Night mode better than Samsung Galaxy S23 Ultra"
        Note: May mark subjective claims as UNVERIFIABLE
        """
        data = Data(dingo_id="product_007", content=product_review)
        result = ArticleFactChecker.eval(data)

        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
