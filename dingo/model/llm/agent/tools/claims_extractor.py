"""
Claims Extraction Tool

This module provides LLM-based extraction of verifiable claims from long-form text.
Based on Claimify methodology and ACL 2025 best practices for atomic fact extraction.

Dependencies:
    openai>=1.0.0 (for LLM-based extraction)

Configuration:
    model: LLM model for extraction (default: "gpt-4o-mini")
    api_key: OpenAI API key
    base_url: Custom API base URL (optional, e.g., "https://api.deepseek.com/v1" for DeepSeek)
    max_claims: Maximum number of claims to extract (default: 50, range: 1-200)
    claim_types: Types of claims to extract (default: all types)
    chunk_size: Text chunk size for processing (default: 2000)
    include_context: Include surrounding context (default: True)
"""

import json
import re
from typing import Any, Dict, List, Optional

from pydantic import Field

from dingo.model.llm.agent.tools.base_tool import BaseTool, ToolConfig
from dingo.model.llm.agent.tools.tool_registry import tool_register
from dingo.utils import log


class ClaimsExtractorConfig(ToolConfig):
    """Configuration for claims extraction tool"""
    model: str = Field(default="gpt-4o-mini", description="LLM model for extraction")
    api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    base_url: Optional[str] = Field(default=None, description="Custom API base URL (e.g., for DeepSeek)")
    max_claims: int = Field(default=50, ge=1, le=200)
    claim_types: List[str] = Field(
        default=[
            # Original claim types
            "factual",       # General facts
            "statistical",   # Numbers, percentages, metrics
            "attribution",   # Who said/did/published what
            "institutional",   # Organizations, affiliations, collaborations
            # New claim types for multi-type article support
            "temporal",      # Time-related claims (dates, durations, "recently")
            "comparative",   # Comparisons between entities/products
            "monetary",      # Financial figures, costs, prices
            "technical"      # Technical specifications, capabilities
        ],
        description="Types of claims to extract (8 types)"
    )
    chunk_size: int = Field(default=2000, ge=500, le=10000, description="Text chunk size")
    include_context: bool = Field(default=True, description="Include surrounding context")
    temperature: float = Field(default=0.1, ge=0.0, le=1.0, description="LLM temperature")


@tool_register
class ClaimsExtractor(BaseTool):
    """
    Extract verifiable claims from long-form text (articles, blog posts).

    This tool uses LLM-based extraction to identify atomic, decontextualized claims
    that can be independently fact-checked. Based on Claimify (ACL 2025) methodology.

    Features:
    - Atomic claim extraction (one fact per claim)
    - Decontextualization (claims stand alone)
    - Claim type classification
    - Context preservation (optional)
    - Deduplication and merging

    Claim Types (8 types):
    - factual: General facts (e.g., "The tower is 330 meters tall")
    - statistical: Numbers, percentages (e.g., "Model has 0.9B parameters")
    - attribution: Who said/did what (e.g., "Vaswani et al. proposed Transformer")
    - institutional: Organizations, affiliations (e.g., "Released by MIT and Stanford")
    - temporal: Time-related (e.g., "Released on December 5, 2024")
    - comparative: Comparisons (e.g., "GPU improved 20% vs previous gen")
    - monetary: Financial figures (e.g., "Priced at $999")
    - technical: Technical specs (e.g., "A17 Pro chip with 3nm process")

    Usage:
        # Extract all types of claims (using default OpenAI API)
        result = ClaimsExtractor.execute(text=article_text)

        # Extract only institutional claims
        result = ClaimsExtractor.execute(
            text=article_text,
            claim_types=["institutional"]
        )

        # Use custom API (e.g., DeepSeek)
        ClaimsExtractor.config.model = "deepseek-chat"
        ClaimsExtractor.config.base_url = "https://api.deepseek.com/v1"
        result = ClaimsExtractor.execute(text=article_text)

        # Result structure:
        {
            'success': True,
            'claims': [
                {
                    'claim_id': 'claim_001',
                    'claim': 'OmniDocBench was released by Tsinghua University',
                    'claim_type': 'institutional',
                    'context': 'PaddleOCR-VL登顶的OmniDocBench V1.5...',
                    'position': {'start': 120, 'end': 180},
                    'verifiable': True,
                    'confidence': 0.95
                },
                ...
            ],
            'metadata': {
                'total_claims': 25,
                'verifiable_claims': 20,
                'claim_types_distribution': {...}
            }
        }
    """

    name = "claims_extractor"
    description = (
        "Extract verifiable claims from long-form text (articles, blog posts). "
        "Returns atomic, decontextualized claims with context and metadata. "
        "Useful for fact-checking articles, identifying checkable statements. "
        "Supports 8 claim types: factual, statistical, attribution, institutional, "
        "temporal, comparative, monetary, technical."
    )
    config: ClaimsExtractorConfig = ClaimsExtractorConfig()

    # System prompt for LLM-based extraction
    EXTRACTION_SYSTEM_PROMPT = """You are an expert fact-checker specialized in extracting verifiable claims from text.

Your task is to extract ATOMIC, VERIFIABLE claims that can be independently fact-checked.

Guidelines:
1. Atomicity: Each claim describes ONE fact, statistic, or attribution
2. Verifiability: Can be checked against authoritative sources
3. Decontextualization: Include necessary context to stand alone
4. Faithfulness: Preserve original meaning
5. Specificity: Extract specific, checkable claims (not opinions or vague statements)

Claim Types (EXPANDED from 4 to 8 for multi-type article support):
- factual: General facts (e.g., "The tower is 330 meters tall")
- statistical: Numbers, percentages, metrics (e.g., "Model has 0.9B parameters")
- attribution: Who said/did/published what (e.g., "Vaswani et al. proposed Transformer")
- institutional: Organizations, affiliations, collaborations (e.g., "Released by MIT and Stanford")
- temporal: Time-related claims - dates, durations, "recently" (e.g., "Released on Dec 5, 2024")
- comparative: Comparisons between entities/products (e.g., "GPU improved 20% vs A16")
- monetary: Financial figures, costs, prices (e.g., "128GB model priced at $999")
- technical: Technical specifications, capabilities (e.g., "A17 Pro chip with 3nm process")

Output Format (JSON):
{
    "claims": [
        {
            "claim": "具体的声明文本",
            "claim_type": "institutional",
            "context": "周围的上下文(帮助理解)",
            "verifiable": true,
            "confidence": 0.95
        }
    ]
}

Examples:

Example 1 - Academic Article:
Input: "百度刚刚发布的PaddleOCR-VL模型登顶了由清华大学、阿里达摩院等联合发布的OmniDocBench榜单。"

Output:
{
    "claims": [
        {
            "claim": "PaddleOCR-VL model was just released by Baidu",
            "claim_type": "attribution",
            "context": "百度刚刚发布的PaddleOCR-VL模型...",
            "verifiable": true,
            "confidence": 0.90
        },
        {
            "claim": "PaddleOCR-VL topped the OmniDocBench leaderboard",
            "claim_type": "factual",
            "context": "模型登顶了...OmniDocBench榜单",
            "verifiable": true,
            "confidence": 0.95
        },
        {
            "claim": "OmniDocBench was jointly released by Tsinghua University and Alibaba DAMO Academy",
            "claim_type": "institutional",
            "context": "由清华大学、阿里达摩院等联合发布的OmniDocBench榜单",
            "verifiable": true,
            "confidence": 0.95
        }
    ]
}

Example 2 - News Article:
Input: "OpenAI于2024年12月5日正式发布o1推理模型。CEO Sam Altman表示这是AGI道路上的里程碑。ChatGPT Plus月费保持20美元。"

Output:
{
    "claims": [
        {
            "claim": "OpenAI released o1 reasoning model on December 5, 2024",
            "claim_type": "temporal",
            "context": "OpenAI于2024年12月5日正式发布o1推理模型",
            "verifiable": true,
            "confidence": 0.98
        },
        {
            "claim": "Sam Altman stated o1 is a milestone on the path to AGI",
            "claim_type": "attribution",
            "context": "CEO Sam Altman表示这是AGI道路上的里程碑",
            "verifiable": true,
            "confidence": 0.90
        },
        {
            "claim": "ChatGPT Plus monthly fee remains $20",
            "claim_type": "monetary",
            "context": "ChatGPT Plus月费保持20美元",
            "verifiable": true,
            "confidence": 0.95
        }
    ]
}

Example 3 - Product Review:
Input: "iPhone 15 Pro搭载A17 Pro芯片,采用3纳米工艺。GPU性能相比A16提升20%。国行128GB版售价7999元。"

Output:
{
    "claims": [
        {
            "claim": "iPhone 15 Pro features A17 Pro chip with 3nm process",
            "claim_type": "technical",
            "context": "iPhone 15 Pro搭载A17 Pro芯片,采用3纳米工艺",
            "verifiable": true,
            "confidence": 0.98
        },
        {
            "claim": "GPU performance improved 20% compared to A16",
            "claim_type": "comparative",
            "context": "GPU性能相比A16提升20%",
            "verifiable": true,
            "confidence": 0.90
        },
        {
            "claim": "China 128GB model priced at 7999 yuan",
            "claim_type": "monetary",
            "context": "国行128GB版售价7999元",
            "verifiable": true,
            "confidence": 0.95
        }
    ]
}

Critical: Extract SPECIFIC claims with verifiable details. Ignore opinions, marketing language, or vague statements.
"""

    @classmethod
    def execute(
        cls,
        text: str,
        claim_types: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Extract verifiable claims from text.

        Args:
            text: Input text (supports Markdown)
            claim_types: Types of claims to extract (default: all types from config)
            **kwargs: Optional configuration overrides
                - max_claims: Override max_claims config
                - include_context: Override include_context config
                - chunk_size: Override chunk_size config

        Returns:
            Dict with extracted claims:
            {
                'success': bool,
                'claims': List[Dict],
                'metadata': Dict
            }

        Raises:
            ImportError: If openai library is not installed
            ValueError: If text is empty or API key is missing
            Exception: For API errors
        """
        # Validate inputs
        if not text or not text.strip():
            log.error("Claims extraction: text cannot be empty")
            return {
                'success': False,
                'error': 'Input text cannot be empty',
                'claims': []
            }

        if not cls.config.api_key:
            error_msg = (
                "OpenAI API key is required for claims extraction.\n\n"
                "Set api_key in tool configuration or environment variable OPENAI_API_KEY"
            )
            log.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'error_type': 'ConfigurationError',
                'claims': []
            }

        # Import OpenAI library (lazy import)
        try:
            from openai import OpenAI
        except ImportError:
            error_msg = (
                "openai library is not installed but required for claims extraction.\n\n"
                "Install with:\n"
                "  pip install -r requirements/agent.txt\n"
                "Or:\n"
                "  pip install openai>=1.0.0"
            )
            log.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'error_type': 'DependencyError',
                'claims': []
            }

        # Get configuration
        claim_types_filter = claim_types or cls.config.claim_types
        max_claims = kwargs.get('max_claims', cls.config.max_claims)
        include_context = kwargs.get('include_context', cls.config.include_context)
        chunk_size = kwargs.get('chunk_size', cls.config.chunk_size)

        log.info(f"Extracting claims from text ({len(text)} chars, chunk_size={chunk_size})")

        try:
            # Create OpenAI client (with optional custom base_url)
            client_kwargs = {"api_key": cls.config.api_key}
            if cls.config.base_url:
                client_kwargs["base_url"] = cls.config.base_url
                log.info(f"Using custom API base URL: {cls.config.base_url}")
            client = OpenAI(**client_kwargs)

            # Chunk text if needed
            chunks = cls._chunk_text(text, chunk_size)
            log.debug(f"Split text into {len(chunks)} chunks")

            # Extract claims from each chunk
            all_claims = []
            for i, chunk_data in enumerate(chunks):
                log.debug(f"Processing chunk {i+1}/{len(chunks)}")

                chunk_claims = cls._extract_claims_from_chunk(
                    client,
                    chunk_data['text'],
                    chunk_data['start_pos'],
                    claim_types_filter,
                    include_context
                )
                all_claims.extend(chunk_claims)

            # Deduplicate and merge similar claims
            unique_claims = cls._deduplicate_claims(all_claims)

            # Limit to max_claims
            if len(unique_claims) > max_claims:
                log.warning(f"Limiting claims from {len(unique_claims)} to {max_claims}")
                unique_claims = unique_claims[:max_claims]

            # Add claim IDs
            for i, claim in enumerate(unique_claims, 1):
                claim['claim_id'] = f"claim_{i:03d}"

            # Build metadata
            metadata = cls._build_metadata(unique_claims)

            result = {
                'success': True,
                'claims': unique_claims,
                'metadata': metadata
            }

            log.info(f"Claims extraction successful: {len(unique_claims)} claims extracted")
            return result

        except Exception as e:
            log.error(f"Claims extraction failed: {e}")

            # Sanitize error message
            error_str = str(e).lower()
            if "api key" in error_str or "authentication" in error_str:
                error_msg = "Invalid or missing API key"
            elif "rate limit" in error_str:
                error_msg = "Rate limit exceeded"
            elif "timeout" in error_str:
                error_msg = "Request timed out"
            else:
                error_msg = f"Extraction failed: {type(e).__name__}"

            return {
                'success': False,
                'error': error_msg,
                'error_type': type(e).__name__,
                'claims': []
            }

    @classmethod
    def _chunk_text(cls, text: str, chunk_size: int) -> List[Dict[str, Any]]:
        """
        Split long text into chunks for processing.

        Args:
            text: Input text
            chunk_size: Maximum chunk size in characters

        Returns:
            List of chunk dictionaries with text and position info
        """
        if len(text) <= chunk_size:
            return [{'text': text, 'start_pos': 0, 'end_pos': len(text)}]

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size

            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence ending within last 20% of chunk
                search_start = start + int((end - start) * 0.8)
                sentence_end = max(
                    text.rfind('。', search_start, end),
                    text.rfind('.', search_start, end),
                    text.rfind('\n\n', search_start, end)
                )
                if sentence_end > start:
                    end = sentence_end + 1

            chunk_text = text[start:end]
            chunks.append({
                'text': chunk_text,
                'start_pos': start,
                'end_pos': end
            })

            start = end

        return chunks

    @classmethod
    def _extract_claims_from_chunk(
        cls,
        client,
        chunk_text: str,
        start_pos: int,
        claim_types: List[str],
        include_context: bool
    ) -> List[Dict]:
        """
        Extract claims from a single text chunk using LLM.

        Args:
            client: OpenAI client
            chunk_text: Text chunk to process
            start_pos: Start position of chunk in original text
            claim_types: Types of claims to extract
            include_context: Whether to include context

        Returns:
            List of extracted claims
        """
        # Build user prompt
        user_prompt = f"""Extract verifiable claims from the following text.

Focus on these claim types: {', '.join(claim_types)}

Text:
{chunk_text}

Return JSON with claims array as specified in the system prompt.
"""

        # Call LLM
        try:
            response = client.chat.completions.create(
                model=cls.config.model,
                messages=[
                    {"role": "system", "content": cls.EXTRACTION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=cls.config.temperature,
                response_format={"type": "json_object"}  # Force JSON output
            )

            output_text = response.choices[0].message.content

            # Parse JSON
            result_json = json.loads(output_text)
            claims = result_json.get('claims', [])

            # Add position info and filter by type
            filtered_claims = []
            for claim in claims:
                claim_type = claim.get('claim_type', 'unknown')
                if claim_type in claim_types or 'all' in claim_types:
                    # Add position (approximate - based on chunk)
                    claim['position'] = {
                        'start': start_pos,
                        'end': start_pos + len(chunk_text)
                    }

                    # Remove context if not requested
                    if not include_context:
                        claim.pop('context', None)

                    filtered_claims.append(claim)

            return filtered_claims

        except json.JSONDecodeError as e:
            log.warning(f"Failed to parse LLM output as JSON: {e}")
            return []
        except Exception as e:
            log.error(f"LLM call failed: {e}")
            return []

    @classmethod
    def _deduplicate_claims(cls, claims: List[Dict]) -> List[Dict]:
        """
        Remove duplicate or highly similar claims.

        Args:
            claims: List of claims

        Returns:
            Deduplicated claims
        """
        if len(claims) <= 1:
            return claims

        unique_claims = []
        seen_texts = set()

        for claim in claims:
            claim_text = claim.get('claim', '').strip().lower()

            # Skip if empty
            if not claim_text:
                continue

            # Skip if exact duplicate
            if claim_text in seen_texts:
                continue

            # Check for very similar claims (simple substring check)
            is_duplicate = False
            for seen_text in seen_texts:
                # If one is substring of other and length difference < 20%
                if claim_text in seen_text or seen_text in claim_text:
                    len_diff = abs(len(claim_text) - len(seen_text))
                    if len_diff < 0.2 * max(len(claim_text), len(seen_text)):
                        is_duplicate = True
                        break

            if not is_duplicate:
                unique_claims.append(claim)
                seen_texts.add(claim_text)

        return unique_claims

    @classmethod
    def _build_metadata(cls, claims: List[Dict]) -> Dict[str, Any]:
        """
        Build metadata summary for extracted claims.

        Args:
            claims: List of claims

        Returns:
            Metadata dictionary
        """
        total_claims = len(claims)
        verifiable_claims = sum(1 for c in claims if c.get('verifiable', True))

        # Count by type
        type_distribution = {}
        for claim in claims:
            claim_type = claim.get('claim_type', 'unknown')
            type_distribution[claim_type] = type_distribution.get(claim_type, 0) + 1

        return {
            'total_claims': total_claims,
            'verifiable_claims': verifiable_claims,
            'claim_types_distribution': type_distribution
        }

    @classmethod
    def validate_config(cls):
        """Validate tool configuration before execution."""
        if not cls.config.api_key:
            raise ValueError(f"{cls.name}: OpenAI API key is required")
