"""
arXiv Search Tool

This module provides integration with arXiv API for academic paper search and verification.
arXiv is a free distribution service and open-access archive for scholarly articles in
the fields of physics, mathematics, computer science, and more.

Dependencies:
    arxiv>=2.4.0

Configuration:
    max_results: Maximum number of search results (default: 5, range: 1-50)
    sort_by: Sort order - "relevance", "lastUpdatedDate", or "submittedDate" (default: "relevance")
    sort_order: "ascending" or "descending" (default: "descending")
    rate_limit_delay: Delay between requests in seconds (default: 3.0)
    timeout: Request timeout in seconds (default: 30)
    api_key: Not required for arXiv (public API)
"""

import re
import time
from typing import Any, Dict, List, Optional

from pydantic import Field

from dingo.io.input import RequiredField
from dingo.model.llm.agent.tools.base_tool import BaseTool, ToolConfig
from dingo.model.llm.agent.tools.tool_registry import tool_register
from dingo.utils import log


class ArxivConfig(ToolConfig):
    """Configuration for arXiv search tool"""
    api_key: Optional[str] = None  # Override parent - not needed for arXiv
    max_results: int = Field(default=5, ge=1, le=50)
    sort_by: str = Field(default="relevance", pattern="^(relevance|lastUpdatedDate|submittedDate)$")
    sort_order: str = Field(default="descending", pattern="^(ascending|descending)$")
    rate_limit_delay: float = Field(default=3.0, ge=0.0)
    timeout: int = Field(default=30, ge=1)


@tool_register
class ArxivSearch(BaseTool):
    """
    arXiv search tool for academic paper verification.

    Provides search capabilities for academic papers in arXiv's open-access archive.
    Supports searching by arXiv ID, DOI, title, author, and keywords with automatic
    detection of query type.

    Features:
    - Auto-detection of arXiv IDs and DOIs
    - No API key required (public API)
    - Rate limiting to respect arXiv guidelines
    - Support for multiple search modes
    - Comprehensive paper metadata

    arXiv ID Patterns:
    - New format: 2301.12345 or 2301.12345v1 (with version)
    - Old format: hep-ph/0123456 or hep-ph/0123456v1

    DOI Pattern:
    - Standard DOI: 10.1234/example.doi

    Usage:
        # Auto-detect search type
        result = ArxivSearch.execute(query="1706.03762")

        # Explicit search by title
        result = ArxivSearch.execute(
            query="Attention is All You Need",
            search_type="title"
        )

        # Result structure:
        {
            'success': True,
            'query': '1706.03762',
            'search_type': 'arxiv_id',
            'results': [
                {
                    'arxiv_id': '1706.03762',
                    'title': 'Attention is All You Need',
                    'authors': ['Vaswani, Ashish', ...],
                    'summary': 'We propose a new...',
                    'published': '2017-06-12',
                    'updated': '2017-12-06',
                    'pdf_url': 'http://arxiv.org/pdf/1706.03762v5',
                    'doi': '10.48550/arXiv.1706.03762',
                    'categories': ['cs.CL', 'cs.LG'],
                    'journal_ref': 'NIPS 2017'
                },
                ...
            ]
        }
    """

    name = "arxiv_search"
    description = (
        "Search arXiv for academic papers by ID, DOI, title, or author. "
        "Returns comprehensive paper metadata including title, authors, abstract, "
        "publication date, PDF URL, and citations. Useful for verifying academic "
        "claims, finding research papers, and checking paper details."
    )
    config: ArxivConfig = ArxivConfig()

    _required_fields = [RequiredField.CONTENT]
    _last_request_time: float = 0.0

    @classmethod
    def execute(cls, query: str, search_type: str = "auto", **kwargs) -> Dict[str, Any]:
        """
        Execute arXiv search.

        Args:
            query: Search query string (arXiv ID, DOI, title, author, or keywords)
            search_type: Search mode - "auto", "id", "doi", "title", "author" (default: "auto")
            **kwargs: Optional overrides for configuration
                - max_results: Override max_results config
                - sort_by: Override sort_by config
                - sort_order: Override sort_order config

        Returns:
            Dict with search results:
            {
                'success': bool,
                'query': str,
                'search_type': str,
                'results': List[Dict],
                'count': int
            }

        Raises:
            ImportError: If arxiv library is not installed
            ValueError: If query is empty or search_type is invalid
            Exception: For API errors
        """
        # Validate inputs
        if not query or not query.strip():
            log.error("arXiv search query cannot be empty")
            return {
                'success': False,
                'error': 'Search query cannot be empty',
                'query': query
            }

        valid_search_types = ["auto", "id", "doi", "title", "author"]
        if search_type not in valid_search_types:
            log.error(f"Invalid search_type: {search_type}")
            return {
                'success': False,
                'error': f'Invalid search_type. Must be one of: {", ".join(valid_search_types)}',
                'query': query
            }

        # Import arxiv library (lazy import)
        try:
            import arxiv
        except ImportError:
            error_msg = (
                "arxiv library is not installed but required for arXiv search.\n\n"
                "Install with:\n"
                "  pip install -r requirements/agent.txt\n"
                "Or:\n"
                "  pip install arxiv\n"
                "Or:\n"
                "  pip install 'dingo-python[agent]'"
            )
            log.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'query': query,
                'error_type': 'DependencyError'
            }

        # Apply rate limiting
        cls._apply_rate_limiting()

        # Execute search
        try:
            log.info(f"Executing arXiv search: {query[:100]}... (type: {search_type})")

            # Build search query based on type
            detected_type, arxiv_query = cls._build_arxiv_query(query, search_type)

            # Get configuration
            max_results = kwargs.get('max_results', cls.config.max_results)
            sort_by_str = kwargs.get('sort_by', cls.config.sort_by)
            sort_order_str = kwargs.get('sort_order', cls.config.sort_order)

            # Map sort_by string to arxiv.SortCriterion
            sort_by_map = {
                'relevance': arxiv.SortCriterion.Relevance,
                'lastUpdatedDate': arxiv.SortCriterion.LastUpdatedDate,
                'submittedDate': arxiv.SortCriterion.SubmittedDate
            }
            sort_by = sort_by_map.get(sort_by_str, arxiv.SortCriterion.Relevance)

            # Map sort_order string to arxiv.SortOrder
            sort_order_map = {
                'ascending': arxiv.SortOrder.Ascending,
                'descending': arxiv.SortOrder.Descending
            }
            sort_order = sort_order_map.get(sort_order_str, arxiv.SortOrder.Descending)

            # Create search
            search = arxiv.Search(
                query=arxiv_query,
                max_results=max_results,
                sort_by=sort_by,
                sort_order=sort_order
            )

            # Execute search and collect results
            results = []
            for paper in search.results():
                results.append(cls._format_paper(paper))

            # Format response
            result = {
                'success': True,
                'query': query,
                'search_type': detected_type,
                'results': results,
                'count': len(results)
            }

            log.info(f"arXiv search successful: {len(results)} results")
            return result

        except Exception as e:
            log.error(f"arXiv search failed: {e}")

            # Sanitize error message to prevent information disclosure
            error_str = str(e).lower()
            if "timeout" in error_str:
                error_msg = "Search request timed out"
            elif "network" in error_str or "connection" in error_str:
                error_msg = "Network connection error"
            elif "rate limit" in error_str:
                error_msg = "Rate limit exceeded"
            else:
                error_msg = f"Search failed: {type(e).__name__}"

            return {
                'success': False,
                'error': error_msg,
                'query': query,
                'error_type': type(e).__name__
            }

    @classmethod
    def _build_arxiv_query(cls, query: str, search_type: str) -> tuple:
        """
        Build arXiv API query based on search type.

        Auto-detection priority:
        1. arXiv ID (e.g., "2301.12345" or "hep-ph/0123456")
        2. DOI (e.g., "10.1234/example")
        3. Title/keyword search

        Args:
            query: User query
            search_type: "auto", "id", "doi", "title", or "author"

        Returns:
            Tuple of (detected_type: str, arxiv_query: str)
        """
        query = query.strip()

        # Auto-detect or explicit type
        if search_type == "auto":
            # Check for arXiv ID
            if cls._is_arxiv_id(query):
                detected_type = "arxiv_id"
                # Clean up arXiv ID (remove "arXiv:" prefix if present)
                clean_id = query.replace("arXiv:", "").replace("arxiv:", "").strip()
                arxiv_query = f"id:{clean_id}"

            # Check for DOI
            elif cls._is_doi(query):
                detected_type = "doi"
                arxiv_query = f"doi:{query}"

            # Default to title search
            else:
                detected_type = "title"
                arxiv_query = f"ti:{query}"

        elif search_type == "id":
            detected_type = "arxiv_id"
            clean_id = query.replace("arXiv:", "").replace("arxiv:", "").strip()
            arxiv_query = f"id:{clean_id}"

        elif search_type == "doi":
            detected_type = "doi"
            arxiv_query = f"doi:{query}"

        elif search_type == "title":
            detected_type = "title"
            arxiv_query = f"ti:{query}"

        elif search_type == "author":
            detected_type = "author"
            arxiv_query = f"au:{query}"

        else:
            # Fallback
            detected_type = "title"
            arxiv_query = f"ti:{query}"

        return detected_type, arxiv_query

    @classmethod
    def _is_arxiv_id(cls, text: str) -> bool:
        """
        Check if text matches arXiv ID pattern.

        Patterns:
        - New format: YYMM.NNNNN or YYMM.NNNNNvN (e.g., 2301.12345, 2301.12345v1)
        - Old format: archive/NNNNNNN or archive/NNNNNNNvN (e.g., hep-ph/0123456)

        Args:
            text: Text to check

        Returns:
            True if text matches arXiv ID pattern
        """
        text = text.strip().replace("arXiv:", "").replace("arxiv:", "")

        # New format: YYMM.NNNNN(vN)?
        new_pattern = r'^\d{4}\.\d{4,5}(v\d+)?$'
        if re.match(new_pattern, text):
            return True

        # Old format: archive/NNNNNNN(vN)?
        old_pattern = r'^[a-z\-]+/\d{7}(v\d+)?$'
        if re.match(old_pattern, text):
            return True

        return False

    @classmethod
    def _is_doi(cls, text: str) -> bool:
        """
        Check if text matches DOI pattern.

        Pattern: 10.NNNN/... (standard DOI format)

        Args:
            text: Text to check

        Returns:
            True if text matches DOI pattern
        """
        text = text.strip()
        # DOI pattern: 10.NNNN/...
        doi_pattern = r'^10\.\d{4,9}/[-._;()/:A-Z0-9]+$'
        return bool(re.match(doi_pattern, text, re.IGNORECASE))

    @classmethod
    def _format_paper(cls, paper) -> Dict[str, Any]:
        """
        Format arxiv.Result to standard dictionary.

        Args:
            paper: arxiv.Result object

        Returns:
            Formatted paper dictionary
        """
        return {
            'arxiv_id': paper.entry_id.split('/')[-1],  # Extract ID from full URL
            'title': paper.title,
            'authors': [author.name for author in paper.authors],
            'summary': paper.summary,
            'published': paper.published.strftime('%Y-%m-%d') if paper.published else None,
            'updated': paper.updated.strftime('%Y-%m-%d') if paper.updated else None,
            'pdf_url': paper.pdf_url,
            'doi': paper.doi,
            'categories': paper.categories,
            'primary_category': paper.primary_category,
            'journal_ref': paper.journal_ref,
            'comment': paper.comment
        }

    @classmethod
    def _apply_rate_limiting(cls):
        """
        Apply rate limiting to respect arXiv guidelines.

        arXiv recommends at least 3 seconds between requests.
        This method enforces the configured rate_limit_delay.
        """
        current_time = time.time()
        time_since_last_request = current_time - cls._last_request_time

        if time_since_last_request < cls.config.rate_limit_delay:
            sleep_time = cls.config.rate_limit_delay - time_since_last_request
            log.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)

        cls._last_request_time = time.time()

    @classmethod
    def detect_paper_references(cls, text: str) -> Dict[str, List[str]]:
        """
        Utility: Detect paper references in text.

        Searches for arXiv IDs and DOIs in text and returns them.
        Useful for preprocessing text to find papers to look up.

        Args:
            text: Text to search for paper references

        Returns:
            Dict with 'arxiv_ids' and 'dois' keys containing found references

        Example:
            text = "See arXiv:1706.03762 and DOI 10.1234/example"
            refs = ArxivSearch.detect_paper_references(text)
            # refs = {
            #     'arxiv_ids': ['1706.03762'],
            #     'dois': ['10.1234/example']
            # }
        """
        # Find arXiv IDs
        arxiv_ids = []

        # New format: YYMM.NNNNN(vN)? - use non-capturing group to avoid tuple returns
        new_pattern = r'\b\d{4}\.\d{4,5}(?:v\d+)?\b'
        arxiv_ids.extend(re.findall(new_pattern, text))

        # Old format: archive/NNNNNNN(vN)? - use non-capturing group
        old_pattern = r'\b[a-z\-]+/\d{7}(?:v\d+)?\b'
        arxiv_ids.extend(re.findall(old_pattern, text))

        # Also look for explicit "arXiv:..." mentions
        arxiv_prefix_pattern = r'arXiv:\s*(\d{4}\.\d{4,5}(?:v\d+)?|[a-z\-]+/\d{7}(?:v\d+)?)'
        arxiv_ids.extend(re.findall(arxiv_prefix_pattern, text, re.IGNORECASE))

        # Find DOIs
        doi_pattern = r'\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b'
        dois = re.findall(doi_pattern, text, re.IGNORECASE)

        # Deduplicate
        arxiv_ids = list(set(arxiv_ids))
        dois = list(set(dois))

        return {
            'arxiv_ids': arxiv_ids,
            'dois': dois
        }

    @classmethod
    def verify_institutions(
        cls,
        paper_id: str,
        claimed_institutions: List[str],
        fuzzy_match: bool = True
    ) -> Dict[str, Any]:
        """
        DEPRECATED: This method is deprecated and will be removed in v0.4.0.

        Deprecation Reason:
        -------------------
        This method is over-specialized for academic papers and contains hardcoded
        test data. The arXiv API does not provide structured institutional affiliations,
        making this approach fragile and limited to academic scenarios.

        Recommended Alternative:
        -----------------------
        Use a combination of arxiv_search and tavily_search for more general and
        reliable entity verification:

        1. Use arxiv_search to find paper details (title, authors, abstract)
        2. Use tavily_search to verify institutional affiliations via web search

        This approach works for:
        - Academic institutions (universities, research labs)
        - Companies and corporations
        - Government organizations
        - Any entity mentioned in articles

        Example Migration:
        ------------------
        Instead of:
            result = ArxivSearch.verify_institutions(
                paper_id="2412.07626",
                claimed_institutions=["Tsinghua University", "Alibaba DAMO"]
            )

        Use:
            # Step 1: Get paper metadata
            paper = ArxivSearch.execute(query="2412.07626")
            paper_title = paper['results'][0]['title']

            # Step 2: Verify institutions via web search
            verification = TavilySearch.execute(
                query=f"verify institutions for paper {paper_title}",
                max_results=5
            )

        Original Docstring (preserved for reference):
        ---------------------------------------------
        Verify paper's institutional affiliations.

        This method fetches a paper's author list and validates whether the
        claimed institutions are accurately represented in the actual author
        affiliations. Useful for fact-checking institutional attribution claims.

        Args:
            paper_id: arXiv ID or DOI (e.g., "2412.07626" or "10.48550/arXiv.2412.07626")
            claimed_institutions: List of institution names claimed in text
            fuzzy_match: Enable fuzzy matching for different languages/abbreviations

        Returns:
            Dict with verification results:
            {
                'success': bool,
                'paper_id': str,
                'paper_title': str,
                'actual_institutions': List[str],  # Unique institutions from authors
                'claimed_institutions': List[str],
                'verification_results': {
                    '清华大学': {
                        'verified': False,
                        'match': None,
                        'reason': 'Not found in author affiliations'
                    },
                    '上海人工智能实验室': {
                        'verified': True,
                        'match': 'Shanghai AI Laboratory',
                        'confidence': 0.95
                    }
                },
                'authors_count': int,
                'institutions_count': int
            }

        Example:
            result = ArxivSearch.verify_institutions(
                paper_id="2412.07626",
                claimed_institutions=["清华大学", "阿里达摩院", "上海人工智能实验室"]
            )

            # Check results
            for institution, result in result['verification_results'].items():
                if not result['verified']:
                    print(f"❌ {institution}: {result['reason']}")
        """
        # DEPRECATION WARNING
        import warnings
        warnings.warn(
            "verify_institutions() is deprecated and will be removed in v0.4.0. "
            "The arXiv API does not provide structured institutional affiliations. "
            "Use arxiv_search + tavily_search for general entity verification instead. "
            "See docstring for migration guide.",
            DeprecationWarning,
            stacklevel=2
        )

        # Validate inputs
        if not paper_id or not paper_id.strip():
            return {
                'success': False,
                'error': 'Paper ID cannot be empty'
            }

        if not claimed_institutions:
            return {
                'success': False,
                'error': 'Claimed institutions list cannot be empty'
            }

        log.info(f"[DEPRECATED] Verifying institutions for paper: {paper_id}")

        try:
            # Fetch paper using existing execute() method
            search_result = cls.execute(query=paper_id, search_type="id")

            if not search_result.get('success'):
                return {
                    'success': False,
                    'error': f"Failed to fetch paper: {search_result.get('error', 'Unknown error')}"
                }

            results = search_result.get('results', [])
            if not results:
                return {
                    'success': False,
                    'error': f"Paper not found: {paper_id}"
                }

            paper = results[0]

            # Extract actual institutions from paper
            actual_institutions = cls._extract_institutions_from_paper(paper)

            log.debug(f"Found {len(actual_institutions)} unique institutions in paper")

            # Verify each claimed institution
            verification_results = {}
            for claimed in claimed_institutions:
                match_result = cls._fuzzy_match_institution(
                    claimed,
                    actual_institutions,
                    fuzzy_match
                )
                verification_results[claimed] = match_result

            # Build response
            result = {
                'success': True,
                'paper_id': paper.get('arxiv_id', paper_id),
                'paper_title': paper.get('title', 'Unknown'),
                'actual_institutions': actual_institutions,
                'claimed_institutions': claimed_institutions,
                'verification_results': verification_results,
                'authors_count': len(paper.get('authors', [])),
                'institutions_count': len(actual_institutions)
            }

            # Log summary
            verified_count = sum(1 for v in verification_results.values() if v.get('verified'))
            log.info(
                f"Institution verification complete: "
                f"{verified_count}/{len(claimed_institutions)} verified"
            )

            return result

        except Exception as e:
            log.error(f"Institution verification failed: {e}")
            return {
                'success': False,
                'error': f"Verification failed: {type(e).__name__}",
                'error_details': str(e)
            }

    @classmethod
    def _extract_institutions_from_paper(cls, paper: Dict) -> List[str]:
        """
        Extract unique institution names from paper's author list.

        Note: arXiv API's author field typically only contains author names,
        not their affiliations. This is a limitation of the arXiv API.
        For papers with arXiv IDs, we attempt to parse affiliations from
        the summary/comment fields if available.

        Args:
            paper: Paper dictionary from execute() results

        Returns:
            List of unique institution names

        Known Limitations:
        - arXiv API does not provide structured affiliation data
        - This method uses heuristics to extract institutions from text
        - For accurate verification, consider using Semantic Scholar API
          or parsing the PDF directly
        """
        institutions = set()

        # Try to extract from comment field (sometimes contains affiliations)
        comment = paper.get('comment', '')
        if comment:
            # Look for common institution patterns
            # Pattern: organization names with keywords like University, Laboratory, etc.
            patterns = [
                r'([A-Z][a-zA-Z\s]+(?:University|Laboratory|Lab|Institute|Academy|AI))',
                r'([一-龥]+(?:大学|实验室|研究院|学院))',  # Chinese institutions
            ]

            for pattern in patterns:
                matches = re.findall(pattern, comment)
                institutions.update(match.strip() for match in matches)

        # Try to extract from summary (abstract)
        summary = paper.get('summary', '')
        if summary and not institutions:  # Only if we didn't find any yet
            # Look in first 500 chars (affiliations often mentioned at start)
            summary_start = summary[:500]

            # Common affiliation phrases
            affiliation_markers = [
                r'from\s+([A-Z][a-zA-Z\s]+(?:University|Laboratory|Lab|Institute))',
                r'at\s+([A-Z][a-zA-Z\s]+(?:University|Laboratory|Lab|Institute))',
            ]

            for pattern in affiliation_markers:
                matches = re.findall(pattern, summary_start)
                institutions.update(match.strip() for match in matches)

        return list(institutions)

    @classmethod
    def _fuzzy_match_institution(
        cls,
        claimed: str,
        actual_list: List[str],
        fuzzy: bool
    ) -> Dict[str, Any]:
        """
        Match claimed institution against actual institutions.

        Handles:
        - Different languages (清华大学 <-> Tsinghua University)
        - Abbreviations (MIT <-> Massachusetts Institute of Technology)
        - Alternative names (Shanghai AI Lab <-> 上海人工智能实验室)

        Args:
            claimed: Claimed institution name
            actual_list: List of actual institution names from paper
            fuzzy: Enable fuzzy matching

        Returns:
            Dict with verification result:
            {
                'verified': bool,
                'match': str or None,  # Matched institution name
                'confidence': float,   # 0.0-1.0
                'reason': str          # Explanation if not verified
            }
        """
        claimed_lower = claimed.strip().lower()

        # Exact match (case-insensitive)
        for actual in actual_list:
            if actual.lower() == claimed_lower:
                return {
                    'verified': True,
                    'match': actual,
                    'confidence': 1.0
                }

        if not fuzzy:
            return {
                'verified': False,
                'match': None,
                'reason': 'Exact match not found (fuzzy matching disabled)'
            }

        # Fuzzy matching using known institution aliases
        alias_map = cls._get_institution_aliases()

        # Check if claimed institution has known aliases
        for canonical_name, aliases in alias_map.items():
            if claimed_lower in [a.lower() for a in aliases]:
                # Check if canonical name or any alias matches actual institutions
                for actual in actual_list:
                    actual_lower = actual.lower()
                    if actual_lower == canonical_name.lower():
                        return {
                            'verified': True,
                            'match': actual,
                            'confidence': 0.95
                        }
                    if actual_lower in [a.lower() for a in aliases]:
                        return {
                            'verified': True,
                            'match': actual,
                            'confidence': 0.90
                        }

        # Substring matching (last resort)
        for actual in actual_list:
            actual_lower = actual.lower()

            # If claimed is substantial substring of actual (or vice versa)
            if len(claimed_lower) >= 5:  # Minimum length to avoid false positives
                if claimed_lower in actual_lower or actual_lower in claimed_lower:
                    # Check that it's a significant match (>50% of shorter string)
                    overlap_ratio = (min(len(claimed_lower), len(actual_lower)) /
                                     max(len(claimed_lower), len(actual_lower)))
                    if overlap_ratio > 0.5:
                        return {
                            'verified': True,
                            'match': actual,
                            'confidence': 0.80
                        }

        return {
            'verified': False,
            'match': None,
            'reason': 'Not found in author affiliations'
        }

    @classmethod
    def _get_institution_aliases(cls) -> Dict[str, List[str]]:
        """
        Get known institution aliases for fuzzy matching.

        Returns:
            Dict mapping canonical names to lists of aliases

        Note: This is a minimal set for demonstration. In production,
        consider using a comprehensive institution name database or
        external API like ROR (Research Organization Registry).
        """
        return {
            "Shanghai AI Laboratory": [
                "Shanghai AI Laboratory",
                "Shanghai Artificial Intelligence Laboratory",
                "上海人工智能实验室",
                "上海AI实验室",
                "Shanghai AI Lab",
                "SHAI Lab"
            ],
            "Tsinghua University": [
                "Tsinghua University",
                "清华大学",
                "THU",
                "Tsinghua"
            ],
            "Alibaba DAMO Academy": [
                "Alibaba DAMO Academy",
                "Alibaba Damo Academy",
                "阿里达摩院",
                "阿里巴巴达摩院",
                "Alibaba Damo",
                "DAMO Academy",
                "达摩院"
            ],
            "Peking University": [
                "Peking University",
                "北京大学",
                "PKU",
                "Peking"
            ],
            "MIT": [
                "Massachusetts Institute of Technology",
                "MIT"
            ],
            "Stanford University": [
                "Stanford University",
                "Stanford"
            ]
        }

    @classmethod
    def validate_config(cls):
        """
        Validate tool configuration.

        arXiv doesn't require an API key, so we override the parent's
        api_key validation.
        """
        # arXiv is a public API - no API key required
        # Just validate that config exists
        if not hasattr(cls, 'config'):
            raise ValueError(f"{cls.name}: Missing configuration")
