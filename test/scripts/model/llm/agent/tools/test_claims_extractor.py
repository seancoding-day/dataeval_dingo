"""
Unit tests for ClaimsExtractor tool.

Tests the LLM-based claims extraction functionality including:
- Basic extraction
- Claim type filtering
- Context preservation
- Deduplication
- Edge cases

Note: Tests use DeepSeek API (via OpenAI SDK) for better availability.
Set OPENAI_API_KEY environment variable with your DeepSeek API key.
"""

import os

import pytest

from dingo.model.llm.agent.tools import ClaimsExtractor

# DeepSeek API configuration (uses OpenAI SDK)
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
DEEPSEEK_MODEL = "deepseek-chat"


class TestClaimsExtractor:
    """Test suite for ClaimsExtractor tool"""

    @pytest.fixture
    def api_key(self):
        """Get API key from environment"""
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            pytest.skip("OPENAI_API_KEY not set")
        return key

    def _configure_extractor(self, api_key: str):
        """Configure ClaimsExtractor with DeepSeek API settings."""
        config = {
            'api_key': api_key,
            'model': DEEPSEEK_MODEL,
            'base_url': DEEPSEEK_BASE_URL
        }
        ClaimsExtractor.update_config(config)

    @pytest.fixture
    def sample_text_with_institutional_claim(self):
        """Sample text with institutional affiliation claim"""
        return """
        PaddleOCR-VL登顶的OmniDocBench V1.5是目前全球衡量文档解析能力最具权威性的评测体系之一。
        它经清华大学、阿里达摩院、上海人工智能实验室等联合发布,主要面向真实场景中的PDF文档解析任务。
        """

    @pytest.fixture
    def sample_text_with_statistical_claims(self):
        """Sample text with statistical claims"""
        return """
        PaddleOCR-VL核心模型参数仅0.9B,在OmniDocBench V1.5榜单上拿下92.6分的成绩。
        该模型支持109种语言,公式识别CDM得分高达0.9453。
        """

    def test_extract_institutional_claims(
        self,
        api_key,
        sample_text_with_institutional_claim
    ):
        """Test extraction of institutional claims"""
        # Configure tool with DeepSeek API
        self._configure_extractor(api_key)

        # Extract claims
        result = ClaimsExtractor.execute(
            text=sample_text_with_institutional_claim,
            claim_types=["institutional"]
        )

        # Verify success
        assert result['success'], f"Extraction failed: {result.get('error')}"

        # Verify claims extracted
        claims = result.get('claims', [])
        assert len(claims) > 0, "No claims extracted"

        # Verify at least one institutional claim
        institutional_claims = [
            c for c in claims
            if c.get('claim_type') == 'institutional'
        ]
        assert len(institutional_claims) > 0, "No institutional claims found"

        # Verify claim about institutions
        claim_texts = [c.get('claim', '').lower() for c in institutional_claims]
        has_institution_mention = any(
            '清华' in text or 'tsinghua' in text or
            '阿里' in text or 'alibaba' in text or
            '上海' in text or 'shanghai' in text
            for text in claim_texts
        )
        assert has_institution_mention, f"No institution mentions found in claims: {claim_texts}"

    def test_extract_statistical_claims(
        self,
        api_key,
        sample_text_with_statistical_claims
    ):
        """Test extraction of statistical claims"""
        self._configure_extractor(api_key)

        result = ClaimsExtractor.execute(
            text=sample_text_with_statistical_claims,
            claim_types=["statistical"]
        )

        assert result['success']
        claims = result.get('claims', [])
        assert len(claims) > 0

        # Verify numbers in claims
        claim_texts = ' '.join(c.get('claim', '') for c in claims)
        assert '0.9B' in claim_texts or '92.6' in claim_texts, \
            f"No statistical data found in claims: {claim_texts}"

    def test_extract_all_claim_types(self, api_key, sample_text_with_institutional_claim):
        """Test extraction of all claim types"""
        self._configure_extractor(api_key)

        result = ClaimsExtractor.execute(
            text=sample_text_with_institutional_claim
            # claim_types defaults to all types
        )

        assert result['success']
        claims = result.get('claims', [])
        assert len(claims) > 0

        # Verify metadata
        metadata = result.get('metadata', {})
        assert metadata.get('total_claims', 0) > 0
        assert 'claim_types_distribution' in metadata

    def test_max_claims_limit(self, api_key, sample_text_with_statistical_claims):
        """Test max_claims configuration"""
        self._configure_extractor(api_key)

        result = ClaimsExtractor.execute(
            text=sample_text_with_statistical_claims,
            max_claims=2
        )

        assert result['success']
        claims = result.get('claims', [])
        assert len(claims) <= 2, f"Expected max 2 claims, got {len(claims)}"

    def test_include_context(self, api_key, sample_text_with_institutional_claim):
        """Test context inclusion/exclusion"""
        self._configure_extractor(api_key)

        # With context
        result_with_context = ClaimsExtractor.execute(
            text=sample_text_with_institutional_claim,
            include_context=True
        )

        assert result_with_context['success']
        claims_with = result_with_context.get('claims', [])
        if claims_with:
            assert 'context' in claims_with[0], "Context should be included"

        # Without context
        result_without_context = ClaimsExtractor.execute(
            text=sample_text_with_institutional_claim,
            include_context=False
        )

        assert result_without_context['success']
        # Context may still be present if LLM includes it - just verify no error

    def test_empty_text(self, api_key):
        """Test handling of empty text"""
        self._configure_extractor(api_key)

        result = ClaimsExtractor.execute(text="")

        assert not result['success']
        assert 'error' in result
        assert result.get('claims') == []

    def test_missing_api_key(self):
        """Test error when API key is missing"""
        # Reset config
        ClaimsExtractor.config = ClaimsExtractor.config.__class__()

        result = ClaimsExtractor.execute(text="Some text")

        assert not result['success']
        assert 'API key' in result.get('error', '')

    def test_chunking_long_text(self, api_key):
        """Test text chunking for long articles"""
        self._configure_extractor(api_key)

        # Create long text (>2000 chars)
        long_text = "PaddleOCR-VL is a model. " * 200  # ~5000 chars

        result = ClaimsExtractor.execute(
            text=long_text,
            chunk_size=1000  # Force chunking
        )

        assert result['success']
        # Should still extract claims even from chunked text - may get duplicates due to repetition

    def test_claim_id_assignment(self, api_key, sample_text_with_institutional_claim):
        """Test that claim IDs are assigned correctly"""
        self._configure_extractor(api_key)

        result = ClaimsExtractor.execute(
            text=sample_text_with_institutional_claim
        )

        assert result['success']
        claims = result.get('claims', [])

        if claims:
            # Verify all claims have IDs
            for claim in claims:
                assert 'claim_id' in claim
                assert claim['claim_id'].startswith('claim_')

            # Verify unique IDs
            claim_ids = [c['claim_id'] for c in claims]
            assert len(claim_ids) == len(set(claim_ids)), "Claim IDs should be unique"

    def test_real_article_extraction(self, api_key):
        """Test extraction from real article excerpt"""
        self._configure_extractor(api_key)

        article_text = """
        PaddleOCR-VL登顶的OmniDocBench V1.5是目前全球衡量文档解析能力最具权威性的评测体系之一。
        它经清华大学、阿里达摩院、上海人工智能实验室等联合发布,由开源社区推动发展。
        在最新一期榜单中,PaddleOCR-VL以92.6的综合得分问鼎榜首。
        PaddleOCR-VL核心模型参数仅0.9B,正面超越了Gemini-2.5 Pro、GPT-4o等巨型多模态大模型。
        """

        result = ClaimsExtractor.execute(text=article_text, max_claims=10)

        assert result['success'], f"Extraction failed: {result.get('error')}"

        claims = result.get('claims', [])
        assert len(claims) >= 3, f"Expected at least 3 claims, got {len(claims)}"

        # Verify we got different claim types
        claim_types = set(c.get('claim_type') for c in claims)
        assert len(claim_types) > 1, f"Expected multiple claim types, got {claim_types}"

        # Log for debugging
        print(f"\nExtracted {len(claims)} claims:")
        for claim in claims:
            print(f"  - [{claim.get('claim_type')}] {claim.get('claim')[:80]}...")
