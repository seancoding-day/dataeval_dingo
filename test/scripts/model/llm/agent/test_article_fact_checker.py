"""
Integration tests for ArticleFactChecker agent.

Tests the end-to-end article fact-checking workflow including:
- Agent initialization and configuration
- Tool registration and availability
- Result structure validation
- Claims extraction from tool calls
- Per-claim verification merging
- Structured report generation
- File saving methods
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from dingo.io.input import Data
from dingo.model import Model
from dingo.model.llm.agent import ArticleFactChecker


class TestArticleFactCheckerBasic:
    """Basic tests for ArticleFactChecker agent structure"""

    def test_agent_registered(self):
        """Test that ArticleFactChecker is registered in Model registry"""
        Model.load_model()
        assert "ArticleFactChecker" in Model.llm_name_map
        assert Model.llm_name_map["ArticleFactChecker"] == ArticleFactChecker

    def test_agent_configuration(self):
        """Test agent configuration attributes"""
        assert ArticleFactChecker.use_agent_executor is True
        assert 'claims_extractor' in ArticleFactChecker.available_tools
        assert 'arxiv_search' in ArticleFactChecker.available_tools
        assert 'tavily_search' in ArticleFactChecker.available_tools
        assert ArticleFactChecker.max_iterations == 10

    def test_format_agent_input(self):
        """Test _format_agent_input method"""
        article_text = "Test article content"
        data = Data(content=article_text)

        result = ArticleFactChecker._format_agent_input(data)

        assert "ARTICLE START" in result
        assert "ARTICLE END" in result
        assert article_text in result
        assert "analyze the article type" in result
        assert "Extract ALL verifiable claims" in result

    def test_get_system_prompt(self):
        """Test system prompt generation"""
        data = Data(content="test")
        prompt = ArticleFactChecker._get_system_prompt(data)

        # Check core prompt content
        assert "expert article fact-checker" in prompt
        assert "claims_extractor" in prompt
        assert "arxiv_search" in prompt
        assert "tavily_search" in prompt
        # Check for all 8 claim types
        assert "temporal" in prompt
        assert "comparative" in prompt
        assert "monetary" in prompt
        assert "technical" in prompt
        # Check for article type analysis step (modular prompts)
        assert "article type" in prompt.lower()
        assert "Analyze Article Type" in prompt

    def test_get_system_prompt_with_article_type(self):
        """Test system prompt generation with specific article type"""
        from dingo.model.llm.agent.agent_article_fact_checker import PromptTemplates

        # Test default prompt
        default_prompt = PromptTemplates.build()
        assert "expert article fact-checker" in default_prompt
        assert len(default_prompt) > 3000  # Substantial prompt

        # Test academic article type prompt
        academic_prompt = PromptTemplates.build(article_type="academic")
        assert "arxiv_search" in academic_prompt
        assert len(academic_prompt) > len(default_prompt)  # Has additional guidance

        # Test news article type prompt
        news_prompt = PromptTemplates.build(article_type="news")
        assert "tavily_search" in news_prompt

        # Test all article types are available
        article_types = PromptTemplates.get_article_types()
        assert "academic" in article_types
        assert "news" in article_types
        assert "product" in article_types
        assert "blog" in article_types
        assert len(article_types) == 6

    def test_output_format_prompt_contains_new_fields(self):
        """Test that OUTPUT_FORMAT prompt requires verification_method, search_queries_used, reasoning"""
        from dingo.model.llm.agent.agent_article_fact_checker import PromptTemplates

        output_fmt = PromptTemplates.OUTPUT_FORMAT
        assert "verification_method" in output_fmt
        assert "search_queries_used" in output_fmt
        assert "reasoning" in output_fmt


class TestArticleFactCheckerResultStructure:
    """Test result structure and parsing"""

    def test_parse_verification_output_json(self):
        """Test parsing valid JSON output"""
        json_output = """{
            "article_verification_summary": {
                "article_type": "academic",
                "total_claims": 5,
                "verified_claims": 4,
                "false_claims": 1,
                "unverifiable_claims": 0,
                "accuracy_score": 0.8
            }
        }"""

        result = ArticleFactChecker._parse_verification_output(json_output)

        assert result is not None
        assert "article_verification_summary" in result
        assert result["article_verification_summary"]["total_claims"] == 5
        assert result["article_verification_summary"]["false_claims"] == 1

    def test_parse_verification_output_with_code_block(self):
        """Test parsing JSON in code block"""
        output_with_block = """Here is the result:
```json
{
    "article_verification_summary": {
        "total_claims": 3,
        "verified_claims": 3,
        "false_claims": 0,
        "accuracy_score": 1.0
    }
}
```
"""

        result = ArticleFactChecker._parse_verification_output(output_with_block)

        assert result is not None
        assert result["article_verification_summary"]["total_claims"] == 3
        assert result["article_verification_summary"]["false_claims"] == 0

    def test_parse_verification_output_fallback(self):
        """Test fallback parsing for non-JSON output"""
        text_output = """
        Total claims: 5
        False claims: 2
        Verified claims: 3
        """

        result = ArticleFactChecker._parse_verification_output(text_output)

        assert result is not None
        assert "article_verification_summary" in result
        assert result["article_verification_summary"]["total_claims"] == 5
        assert result["article_verification_summary"]["false_claims"] == 2

    def test_build_eval_detail_from_verification_without_report(self):
        """Test building EvalDetail from verification data (no report)"""
        verification_data = {
            "article_verification_summary": {
                "total_claims": 10,
                "verified_claims": 8,
                "false_claims": 2,
                "unverifiable_claims": 0,
                "accuracy_score": 0.8
            },
            "detailed_findings": [
                {"claim_id": "claim_001", "verification_result": "TRUE"},
                {"claim_id": "claim_002", "verification_result": "FALSE"}
            ]
        }

        result = ArticleFactChecker._build_eval_detail_from_verification(
            verification_data, tool_calls=[], reasoning_steps=5
        )

        assert result is not None
        assert result.metric == "ArticleFactChecker"
        assert result.status is True  # Has false claims
        assert result.score == 0.8
        assert len(result.reason) >= 1
        # reason[0] should be a string summary
        assert isinstance(result.reason[0], str)
        assert "Total Claims" in result.reason[0]

    def test_build_eval_detail_from_verification_with_report(self):
        """Test building EvalDetail with dual-layer reason (text + report)"""
        verification_data = {
            "article_verification_summary": {
                "total_claims": 5,
                "verified_claims": 4,
                "false_claims": 1,
                "unverifiable_claims": 0,
                "accuracy_score": 0.8
            },
            "detailed_findings": []
        }
        report = {"report_version": "2.0", "verification_summary": {"accuracy_score": 0.8}}

        result = ArticleFactChecker._build_eval_detail_from_verification(
            verification_data, tool_calls=[], reasoning_steps=3, report=report
        )

        assert len(result.reason) == 2
        assert isinstance(result.reason[0], str)
        assert isinstance(result.reason[1], dict)
        assert result.reason[1]["report_version"] == "2.0"

    def test_create_error_result(self):
        """Test error result creation"""
        error_msg = "Test error message"

        result = ArticleFactChecker._create_error_result(error_msg)

        assert result is not None
        assert result.metric == "ArticleFactChecker"
        assert result.status is True  # Error = issue
        assert any("ERROR" in label for label in result.label)
        assert any(error_msg in str(line) for line in result.reason)


class TestClaimsExtractionFromToolCalls:
    """Test _extract_claims_from_tool_calls method"""

    def test_extract_claims_from_valid_tool_calls(self):
        """Test extracting claims from claims_extractor observation"""
        tool_calls = [
            {
                "tool": "claims_extractor",
                "args": {"text": "article text..."},
                "observation": json.dumps({
                    "success": True,
                    "data": {
                        "claims": [
                            {"claim_id": "claim_001", "claim": "Claim A", "claim_type": "factual", "confidence": 0.9},
                            {"claim_id": "claim_002", "claim": "Claim B", "claim_type": "institutional", "confidence": 0.85}
                        ]
                    }
                })
            },
            {
                "tool": "tavily_search",
                "args": {"query": "Claim A"},
                "observation": "{\"success\": true, \"data\": {\"results\": []}}"
            }
        ]

        claims = ArticleFactChecker._extract_claims_from_tool_calls(tool_calls)

        assert len(claims) == 2
        assert claims[0]["claim_id"] == "claim_001"
        assert claims[1]["claim_type"] == "institutional"

    def test_extract_claims_from_empty_tool_calls(self):
        """Test with no tool calls"""
        claims = ArticleFactChecker._extract_claims_from_tool_calls([])
        assert claims == []

    def test_extract_claims_when_no_claims_extractor_called(self):
        """Test when only search tools were called"""
        tool_calls = [
            {"tool": "tavily_search", "args": {"query": "test"}, "observation": "{}"}
        ]
        claims = ArticleFactChecker._extract_claims_from_tool_calls(tool_calls)
        assert claims == []

    def test_extract_claims_with_failed_observation(self):
        """Test when claims_extractor returned failure"""
        tool_calls = [
            {
                "tool": "claims_extractor",
                "args": {"text": "article"},
                "observation": json.dumps({"success": False, "error": "API error"})
            }
        ]
        claims = ArticleFactChecker._extract_claims_from_tool_calls(tool_calls)
        assert claims == []

    def test_extract_claims_with_malformed_observation(self):
        """Test when observation is not valid JSON"""
        tool_calls = [
            {"tool": "claims_extractor", "args": {}, "observation": "not json"}
        ]
        claims = ArticleFactChecker._extract_claims_from_tool_calls(tool_calls)
        assert claims == []


class TestPerClaimVerification:
    """Test _build_per_claim_verification method"""

    def test_merge_with_complete_data(self):
        """Test merging when all three data sources have matching data"""
        verification_data = {
            "detailed_findings": [
                {
                    "claim_id": "claim_001",
                    "original_claim": "Test claim",
                    "claim_type": "factual",
                    "verification_result": "TRUE",
                    "evidence": "Found evidence",
                    "sources": ["https://example.com"],
                    "verification_method": "tavily_search",
                    "search_queries_used": ["test query"],
                    "reasoning": "Step-by-step..."
                }
            ],
            "false_claims_comparison": []
        }
        extracted_claims = [
            {"claim_id": "claim_001", "claim": "Test claim", "claim_type": "factual", "confidence": 0.95}
        ]
        tool_calls = [
            {"tool": "tavily_search", "args": {"query": "test query"}, "observation": "{}"}
        ]

        enriched = ArticleFactChecker._build_per_claim_verification(
            verification_data, extracted_claims, tool_calls
        )

        assert len(enriched) == 1
        assert enriched[0]["claim_id"] == "claim_001"
        assert enriched[0]["confidence"] == 0.95
        assert enriched[0]["verification_result"] == "TRUE"
        assert enriched[0]["verification_method"] == "tavily_search"

    def test_merge_with_false_claims_matching(self):
        """Test that FALSE claims get error_type and severity from comparison"""
        verification_data = {
            "detailed_findings": [
                {
                    "claim_id": "claim_001",
                    "original_claim": "OpenAI released o1 in November 2024",
                    "verification_result": "FALSE",
                    "evidence": "Released Dec 5"
                }
            ],
            "false_claims_comparison": [
                {
                    "article_claimed": "OpenAI released o1 in November 2024",
                    "actual_truth": "Released December 5",
                    "error_type": "temporal_error",
                    "severity": "medium"
                }
            ]
        }

        enriched = ArticleFactChecker._build_per_claim_verification(
            verification_data, [], []
        )

        assert len(enriched) == 1
        assert enriched[0]["error_type"] == "temporal_error"
        assert enriched[0]["severity"] == "medium"

    def test_fallback_when_no_detailed_findings(self):
        """Test placeholder records when agent has no detailed_findings"""
        verification_data = {"detailed_findings": []}
        extracted_claims = [
            {"claim_id": "claim_001", "claim": "Some claim", "claim_type": "factual", "confidence": 0.9}
        ]

        enriched = ArticleFactChecker._build_per_claim_verification(
            verification_data, extracted_claims, []
        )

        assert len(enriched) == 1
        assert enriched[0]["verification_result"] == "UNVERIFIABLE"
        assert enriched[0]["original_claim"] == "Some claim"

    def test_empty_all_sources(self):
        """Test with no data at all"""
        enriched = ArticleFactChecker._build_per_claim_verification({}, [], [])
        assert enriched == []


class TestStructuredReport:
    """Test _build_structured_report method"""

    def setup_method(self):
        """Set up dynamic_config mock for model name access"""
        from dingo.config.input_args import EvaluatorLLMArgs
        self._original_dynamic_config = getattr(ArticleFactChecker, 'dynamic_config', None)
        ArticleFactChecker.dynamic_config = EvaluatorLLMArgs(
            key="test-key", api_url="https://api.example.com", model="test-model"
        )

    def teardown_method(self):
        """Restore original dynamic_config to avoid test pollution"""
        if self._original_dynamic_config is not None:
            ArticleFactChecker.dynamic_config = self._original_dynamic_config

    def test_report_structure(self):
        """Test that report has all required top-level keys"""
        verification_data = {
            "article_verification_summary": {
                "total_claims": 3,
                "verified_claims": 2,
                "false_claims": 1,
                "unverifiable_claims": 0,
                "accuracy_score": 0.67
            },
            "false_claims_comparison": []
        }
        extracted_claims = [
            {"claim_id": "claim_001", "claim_type": "factual", "verifiable": True},
            {"claim_id": "claim_002", "claim_type": "institutional", "verifiable": True},
            {"claim_id": "claim_003", "claim_type": "factual", "verifiable": False}
        ]

        report = ArticleFactChecker._build_structured_report(
            verification_data=verification_data,
            extracted_claims=extracted_claims,
            enriched_claims=[],
            tool_calls=[{"tool": "tavily_search"}],
            reasoning_steps=5,
            content_length=1000,
            execution_time=30.5
        )

        assert report["report_version"] == "2.0"
        assert "generated_at" in report
        assert report["article_info"]["content_length"] == 1000
        assert report["claims_extraction"]["total_extracted"] == 3
        assert report["claims_extraction"]["verifiable"] == 2
        assert report["claims_extraction"]["claim_types_distribution"]["factual"] == 2
        assert report["verification_summary"]["accuracy_score"] == 0.67
        assert report["agent_metadata"]["tool_calls_count"] == 1
        assert report["agent_metadata"]["execution_time_seconds"] == 30.5
        assert report["agent_metadata"]["model"] == "test-model"


class TestFileSaving:
    """Test file saving methods"""

    def setup_method(self):
        """Save original dynamic_config before tests that modify it"""
        self._original_dynamic_config = getattr(ArticleFactChecker, 'dynamic_config', None)

    def teardown_method(self):
        """Restore original dynamic_config to avoid test pollution"""
        if self._original_dynamic_config is not None:
            ArticleFactChecker.dynamic_config = self._original_dynamic_config

    def test_save_article_content(self, tmp_path):
        """Test saving article content to markdown file"""
        content = "# Test Article\n\nThis is test content."

        result_path = ArticleFactChecker._save_article_content(str(tmp_path), content)

        assert os.path.exists(result_path)
        with open(result_path, 'r', encoding='utf-8') as f:
            assert f.read() == content

    def test_save_claims(self, tmp_path):
        """Test saving claims to JSONL file"""
        claims = [
            {"claim_id": "claim_001", "claim": "First claim"},
            {"claim_id": "claim_002", "claim": "Second claim"}
        ]

        result_path = ArticleFactChecker._save_claims(str(tmp_path), claims)

        assert os.path.exists(result_path)
        with open(result_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        assert len(lines) == 2
        assert json.loads(lines[0])["claim_id"] == "claim_001"

    def test_save_verification_details(self, tmp_path):
        """Test saving verification details to JSONL file"""
        enriched = [
            {"claim_id": "claim_001", "verification_result": "TRUE"},
            {"claim_id": "claim_002", "verification_result": "FALSE"}
        ]

        result_path = ArticleFactChecker._save_verification_details(str(tmp_path), enriched)

        assert os.path.exists(result_path)
        with open(result_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        assert len(lines) == 2
        assert json.loads(lines[1])["verification_result"] == "FALSE"

    def test_save_full_report(self, tmp_path):
        """Test saving full report to JSON file"""
        report = {
            "report_version": "2.0",
            "verification_summary": {"accuracy_score": 0.8}
        }

        result_path = ArticleFactChecker._save_full_report(str(tmp_path), report)

        assert os.path.exists(result_path)
        with open(result_path, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        assert loaded["report_version"] == "2.0"

    def test_get_output_dir_returns_none_when_not_configured(self):
        """Test _get_output_dir returns None when no output_path in config"""
        from dingo.config.input_args import EvaluatorLLMArgs
        ArticleFactChecker.dynamic_config = EvaluatorLLMArgs(
            key="test", api_url="https://api.example.com", model="test"
        )
        result = ArticleFactChecker._get_output_dir()
        assert result is None

    def test_get_output_dir_creates_directory(self, tmp_path):
        """Test _get_output_dir creates directory when configured"""
        from dingo.config.input_args import EvaluatorLLMArgs

        output_dir = str(tmp_path / "new_output_dir")
        ArticleFactChecker.dynamic_config = EvaluatorLLMArgs(
            key="test", api_url="https://api.example.com", model="test",
            parameters={"agent_config": {"output_path": output_dir}}
        )

        result = ArticleFactChecker._get_output_dir()

        assert result == output_dir
        assert os.path.isdir(output_dir)


class TestAggregateResultsErrorPaths:
    """Test aggregate_results error handling paths"""

    def setup_method(self):
        """Set up dynamic_config and thread-local context"""
        from dingo.config.input_args import EvaluatorLLMArgs
        self._original_dynamic_config = getattr(ArticleFactChecker, 'dynamic_config', None)
        ArticleFactChecker.dynamic_config = EvaluatorLLMArgs(
            key="test-key", api_url="https://api.example.com", model="test-model"
        )
        # Set thread-local context to avoid KeyError
        ArticleFactChecker._thread_local.context = {
            'start_time': 0,
            'output_dir': None,
            'content_length': 100,
        }

    def teardown_method(self):
        """Restore original dynamic_config"""
        if self._original_dynamic_config is not None:
            ArticleFactChecker.dynamic_config = self._original_dynamic_config

    def test_aggregate_results_with_empty_results(self):
        """Test aggregate_results when results list is empty"""
        data = Data(content="test")
        result = ArticleFactChecker.aggregate_results(data, [])

        assert result.status is True
        assert any("AGENT_ERROR" in label for label in result.label)

    def test_aggregate_results_with_recursion_limit_error(self):
        """Test aggregate_results handles recursion limit error"""
        data = Data(content="test")
        agent_result = {
            'success': False,
            'error': 'Recursion limit of 25 reached without finishing.'
        }

        result = ArticleFactChecker.aggregate_results(data, [agent_result])

        assert result.status is True
        assert any("RECURSION_LIMIT" in label for label in result.label)
        assert any("25" in str(line) for line in result.reason)

    def test_aggregate_results_with_timeout_error(self):
        """Test aggregate_results handles timeout error"""
        data = Data(content="test")
        agent_result = {
            'success': False,
            'error': 'Request timed out after 120 seconds'
        }

        result = ArticleFactChecker.aggregate_results(data, [agent_result])

        assert result.status is True
        assert any("TIMEOUT" in label for label in result.label)

    def test_aggregate_results_with_empty_output(self):
        """Test aggregate_results when agent returns empty output"""
        data = Data(content="test")
        agent_result = {
            'success': True,
            'output': '',
            'tool_calls': [],
            'reasoning_steps': 0
        }

        result = ArticleFactChecker.aggregate_results(data, [agent_result])

        assert result.status is True
        assert any("AGENT_ERROR" in label for label in result.label)

    def test_aggregate_results_with_valid_json_output(self):
        """Test aggregate_results with valid JSON agent output"""
        data = Data(content="test article")
        agent_output = json.dumps({
            "article_verification_summary": {
                "article_type": "blog",
                "total_claims": 3,
                "verified_claims": 3,
                "false_claims": 0,
                "unverifiable_claims": 0,
                "accuracy_score": 1.0
            },
            "detailed_findings": [],
            "false_claims_comparison": []
        })
        agent_result = {
            'success': True,
            'output': agent_output,
            'tool_calls': [],
            'reasoning_steps': 5
        }

        result = ArticleFactChecker.aggregate_results(data, [agent_result])

        assert result.status is False  # No false claims
        assert result.score == 1.0
        assert isinstance(result.reason[0], str)


class TestArticleFactCheckerIntegration:
    """Integration tests requiring API keys (marked as slow)"""

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
    def api_keys(self):
        """Get API keys from environment"""
        openai_key = os.getenv("OPENAI_API_KEY")
        tavily_key = os.getenv("TAVILY_API_KEY")

        if not openai_key:
            pytest.skip("OPENAI_API_KEY not set")

        return {
            'openai': openai_key,
            'tavily': tavily_key
        }

    @pytest.fixture
    def blog_article_path(self):
        """Get path to blog article test data"""
        test_file = Path(__file__)
        article_path = test_file.parents[4] / "data" / "blog_article.md"

        if not article_path.exists():
            pytest.skip(f"Blog article not found: {article_path}")

        return article_path

    @pytest.mark.slow
    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="Requires OPENAI_API_KEY for real API test"
    )
    def test_eval_with_real_article(self, api_keys, blog_article_path):
        """
        Integration test with real article and API calls.

        NOTE: This test uses real LLM and search APIs, so it:
        - Requires valid API keys
        - Consumes API quota
        - Results may vary based on external data
        """
        with open(blog_article_path, 'r', encoding='utf-8') as f:
            article_content = f.read()

        data = Data(content=article_content)

        result = ArticleFactChecker.eval(data)

        # Verify result structure
        assert result is not None
        assert result.metric == "ArticleFactChecker"
        assert isinstance(result.status, bool)
        assert result.reason is not None
        assert len(result.reason) >= 1
        # reason[0] should be human-readable text
        assert isinstance(result.reason[0], str)
        assert len(result.reason[0]) > 100

    @pytest.mark.slow
    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="Requires OPENAI_API_KEY"
    )
    def test_eval_with_empty_article(self, api_keys):
        """Test handling of empty article"""
        data = Data(content="")

        result = ArticleFactChecker.eval(data)

        assert result is not None
        assert result.metric == "ArticleFactChecker"
        assert isinstance(result.status, bool)
        assert result.score == 0.0 or result.score is None

    @pytest.mark.slow
    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="Requires OPENAI_API_KEY"
    )
    def test_eval_with_short_article(self, api_keys):
        """Test with very short article"""
        short_article = """
# Short Test Article

PaddleOCR-VL is an OCR model. It scored 92.6 on OmniDocBench.
"""

        data = Data(content=short_article)

        result = ArticleFactChecker.eval(data)

        assert result is not None
        assert result.metric == "ArticleFactChecker"
        assert isinstance(result.status, bool)
        assert result.reason is not None
