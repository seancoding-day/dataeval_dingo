"""
Unit tests for ClaimsExtractor tool.

Only non-API tests are included here. Tests that require a live
DeepSeek/OpenAI API have been removed to keep the suite fast and
deterministic.
"""

from dingo.model.llm.agent.tools.claims_extractor import ClaimsExtractor


class TestClaimsExtractor:
    """Test suite for ClaimsExtractor tool."""

    def test_missing_api_key(self):
        """Test error when API key is missing."""
        # Reset config to a fresh instance (no key set)
        ClaimsExtractor.config = ClaimsExtractor.config.__class__()

        result = ClaimsExtractor.execute(text="Some text")

        assert not result['success']
        assert 'API key' in result.get('error', '')
