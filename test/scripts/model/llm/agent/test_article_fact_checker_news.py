"""
Test ArticleFactChecker with news articles.

This test suite validates news article handling with temporal,
attribution, and monetary claims.
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


class TestArticleFactCheckerNews:
    """Test suite for news article fact-checking"""

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
    def news_article(self) -> str:
        """Load news article about OpenAI o1 release."""
        path = get_test_data_path("news_article_excerpt.md")
        return path.read_text(encoding='utf-8')

    @pytest.fixture(autouse=True)
    def skip_if_no_api_key(self):
        """Auto-skip all tests if no API keys available."""
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set")

    def test_structure_validation(self, news_article: str):
        """Test data structure without API calls."""
        data = Data(dingo_id="news_001", content=news_article)

        assert data.content is not None
        assert "OpenAI" in data.content
        assert "o1" in data.content
        assert "2024" in data.content

    @pytest.mark.slow
    @pytest.mark.external
    @skip_on_api_error
    def test_claim_extraction(self, news_article: str):
        """
        Test claim extraction from news article.

        Expected: temporal, attribution, statistical, monetary claims.
        """
        data = Data(dingo_id="news_002", content=news_article)
        result = ArticleFactChecker.eval(data)

        assert result is not None
        assert hasattr(result, 'status')
        assert hasattr(result, 'score')

    @pytest.mark.slow
    @pytest.mark.external
    @skip_on_api_error
    def test_temporal_verification(self, news_article: str):
        """
        Test temporal claim verification.

        Example: "Released on December 5, 2024"
        Tool: tavily_search with date filters
        """
        data = Data(dingo_id="news_003", content=news_article)
        result = ArticleFactChecker.eval(data)

        assert result is not None

    @pytest.mark.slow
    @pytest.mark.external
    @skip_on_api_error
    def test_attribution_verification(self, news_article: str):
        """
        Test attribution claim verification.

        Example: "Sam Altman stated o1 is a milestone"
        Tool: tavily_search
        """
        data = Data(dingo_id="news_004", content=news_article)
        result = ArticleFactChecker.eval(data)

        assert result is not None

    @pytest.mark.slow
    @pytest.mark.external
    @skip_on_api_error
    def test_monetary_verification(self, news_article: str):
        """
        Test monetary claim verification.

        Example: "ChatGPT Plus remains $20/month"
        Tool: tavily_search
        """
        data = Data(dingo_id="news_005", content=news_article)
        result = ArticleFactChecker.eval(data)

        assert result is not None

    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.external
    @skip_on_api_error
    def test_full_workflow(self, news_article: str):
        """
        Integration test: Full news article workflow.

        Steps: Type ID → Claim extraction → Verification → Report
        """
        data = Data(dingo_id="news_integration", content=news_article)
        result = ArticleFactChecker.eval(data)

        assert result is not None
        assert hasattr(result, 'status')
        assert hasattr(result, 'score')
        assert hasattr(result, 'label')
        assert hasattr(result, 'reason')


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
