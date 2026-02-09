# Dingo Agent Architecture & Implementation Guide

## Overview

Dingo's Agent system extends traditional rule and LLM-based evaluation with **multi-step reasoning**, **tool usage**, and **adaptive context gathering** capabilities. This document provides a comprehensive overview of the Agent architecture, file structure, and implementation patterns.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [File Structure](#file-structure)
3. [Core Components](#core-components)
4. [Implementation Patterns](#implementation-patterns)
5. [Data Flow](#data-flow)
6. [Configuration](#configuration)
7. [Examples](#examples)

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Dingo Evaluation System                   │
├─────────────────────────────────────────────────────────────┤
│  Data Input → Executor → [Rules | LLMs | Agents] → Results  │
└─────────────────────────────────────────────────────────────┘
                              ▼
                    ┌─────────────────────┐
                    │   Agent Framework   │
                    └─────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
   ┌─────────┐         ┌──────────┐         ┌──────────┐
   │  Base   │         │  Tools   │         │ LangChain│
   │  Agent  │◄────────│ Registry │         │ Adapter  │
   └─────────┘         └──────────┘         └──────────┘
        │                     │
        ▼                     ▼
┌────────────────┐    ┌──────────────────┐
│ AgentFactCheck │    │  tavily_search   │
│AgentHallucin..│    │  arxiv_search    │
│ArticleFactChk │    │  claims_extractor│
│   (Custom)     │    │  render_tool     │
└────────────────┘    │  mineru_ocr_tool │
                      └──────────────────┘
```

### Evaluation Flow Comparison

```
Traditional Evaluation:
┌──────┐      ┌─────────┐      ┌────────────┐
│ Data │─────▶│ Rule/LLM│─────▶│ EvalDetail │
└──────┘      └─────────┘      └────────────┘

Agent-Based Evaluation:
┌──────┐      ┌───────┐      ┌──────────┐      ┌─────┐      ┌────────────┐
│ Data │─────▶│ Agent │─────▶│Tool Calls│─────▶│ LLM │─────▶│ EvalDetail │
└──────┘      └───────┘      └──────────┘      └─────┘      └────────────┘
                                    │              │
                               Web Search    Reasoning &
                               OCR Tools     Synthesis
```

---

## File Structure

### Current Implementation (Latest)

```
dingo/
├── model/
│   ├── llm/                              # LLM-based evaluators
│   │   ├── agent/                        # ✨ Agent Framework
│   │   │   ├── __init__.py               # Package exports (BaseAgent, tools)
│   │   │   ├── base_agent.py             # BaseAgent abstract class
│   │   │   ├── agent_fact_check.py       # LangChain-based agent (framework-driven)
│   │   │   ├── agent_hallucination.py    # Custom workflow agent (imperative)
│   │   │   ├── agent_article_fact_checker.py  # Agent-First article fact-checker
│   │   │   ├── agent_wrapper.py          # LangChain 1.0 integration wrapper
│   │   │   ├── langchain_adapter.py      # Dingo ↔ LangChain tool adapter
│   │   │   └── tools/                    # Agent tools
│   │   │       ├── __init__.py           # Tool registry exports
│   │   │       ├── base_tool.py          # BaseTool abstract class
│   │   │       ├── tool_registry.py      # Tool registration & discovery
│   │   │       ├── claims_extractor.py   # Claims extraction tool (LLM-based)
│   │   │       ├── arxiv_search.py       # Academic paper search tool
│   │   │       ├── tavily_search.py      # Web search tool (Tavily API)
│   │   │       ├── render_tool.py        # HTML rendering tool
│   │   │       └── mineru_ocr_tool.py    # OCR tool (MinerU integration)
│   │   ├── base_openai.py                # Base class for OpenAI-compatible LLMs
│   │   └── ...                           # Other LLM evaluators
│   ├── model.py                          # ✏️ Central registry (@Model decorator)
│   └── rule/                             # Rule-based evaluators
│
├── config/
│   └── input_args.py                     # ✏️ Configuration models (Pydantic)
│                                         #    - InputArgs
│                                         #    - EvaluatorArgs (includes agent_config)
│
├── exec/
│   ├── local.py                          # ✏️ Local executor with thread/process pools
│   │                                     #    - Agents run in ThreadPoolExecutor (I/O-bound)
│   └── spark.py                          # Distributed executor (Spark)
│
├── io/
│   ├── input/
│   │   └── data.py                       # Data class (standardized input)
│   └── output/
│       └── eval_detail.py                # EvalDetail (evaluation result)
│
└── utils/
    └── log_util/                         # Logging utilities
        └── logger.py

examples/
└── agent/                                # ✨ Agent usage examples
    ├── agent_executor_example.py         # Basic agent execution
    ├── agent_hallucination_example.py    # Hallucination detection example
    └── agent_article_fact_checking_example.py  # Article fact-checking example

test/
└── scripts/
    └── model/
        └── llm/
            └── agent/                    # ✨ Agent tests
                ├── test_agent_fact_check.py
                ├── test_agent_hallucination.py
                ├── test_article_fact_checker.py  # ArticleFactChecker tests (33 tests)
                ├── test_tool_registry.py
                └── tools/
                    ├── test_claims_extractor.py
                    ├── test_arxiv_search.py
                    ├── test_tavily_search.py
                    ├── test_render_tool.py
                    └── test_mineru_ocr_tool.py

docs/
├── agent_development_guide.md            # Comprehensive development guide
├── agent_architecture.md                 # This file
├── article_fact_checking_guide.md        # ArticleFactChecker guide
└── quick_start_article_fact_checking.md  # Quick start for article fact-checking

requirements/
└── agent.txt                             # Agent dependencies
                                          #   - langchain>=1.0.0
                                          #   - langchain-openai
                                          #   - tavily-python
                                          #   - etc.

.github/
└── env/
    └── agent_hallucination.json          # Example agent configuration
```

### Key File Changes from "Old Version"

| Old Path | New Path | Notes |
|----------|----------|-------|
| `dingo/model/agent/` | `dingo/model/llm/agent/` | Moved under LLM module hierarchy |
| N/A | `agent_wrapper.py` | Added LangChain 1.0 integration |
| N/A | `langchain_adapter.py` | Added Dingo ↔ LangChain adapters |
| `agent_fact_check_web.py` | `agent_fact_check.py` | Simplified naming |
| N/A | `agent_hallucination.py` | Added custom workflow example |
| `tools/web_search.py` | `tools/tavily_search.py` | Specific implementation naming |
| N/A | `tools/render_tool.py` | Added HTML rendering |
| N/A | `tools/mineru_ocr_tool.py` | Added OCR capabilities |

---

## Core Components

### 1. BaseAgent (base_agent.py)

**Purpose**: Abstract base class for all agent-based evaluators

**Key Features**:
- Extends `BaseOpenAI` to inherit LLM functionality
- Supports dual execution paths: Legacy (manual) and LangChain (framework-driven)
- Manages tool execution and configuration injection
- Provides agent orchestration methods

**Core Methods**:
```python
class BaseAgent(BaseOpenAI):
    # Configuration
    available_tools: List[str] = []      # Tools this agent can use
    max_iterations: int = 5              # Safety limit
    use_agent_executor: bool = False     # Enable LangChain path

    # Abstract methods (must implement)
    @abstractmethod
    def plan_execution(cls, input_data: Data) -> List[Dict[str, Any]]
    @abstractmethod
    def aggregate_results(cls, input_data: Data, results: List[Any]) -> EvalDetail

    # Main evaluation entry point
    def eval(cls, input_data: Data) -> EvalDetail

    # Tool execution
    def execute_tool(cls, tool_name: str, **kwargs) -> Dict[str, Any]
    def configure_tool(cls, tool_name: str, tool_class)

    # LangChain integration
    def _eval_with_langchain_agent(cls, input_data: Data) -> EvalDetail
    def get_langchain_tools(cls)
    def _format_agent_input(cls, input_data: Data) -> str
    def _get_system_prompt(cls, input_data: Data) -> str
```

**Execution Flow**:
```
eval()
├─ use_agent_executor == True?
│  ├─ Yes → _eval_with_langchain_agent()
│  │         ├─ get_langchain_tools()
│  │         ├─ get_langchain_llm()
│  │         ├─ AgentWrapper.create_agent()
│  │         ├─ AgentWrapper.invoke_and_format()
│  │         └─ aggregate_results()
│  │
│  └─ No  → Legacy path
│            ├─ plan_execution()
│            ├─ Loop through plan steps
│            │   ├─ execute_tool() for tool steps
│            │   └─ send_messages() for LLM steps
│            └─ aggregate_results()
```

### 2. Tool System

#### BaseTool (tools/base_tool.py)

**Purpose**: Abstract interface for all agent tools

```python
class BaseTool(ABC):
    name: str                           # Unique identifier
    description: str                    # For LLM understanding
    config: ToolConfig                  # Tool-specific config

    @abstractmethod
    def execute(cls, **kwargs) -> Dict[str, Any]
    def validate_config(cls)
    def update_config(cls, config_dict: Dict[str, Any])
```

#### ToolRegistry (tools/tool_registry.py)

**Purpose**: Central registry for tool discovery and management

**Key Features**:
- Auto-discovery via `@tool_register()` decorator
- Lazy loading (tools loaded on first use)
- Configuration injection from agent config

```python
@tool_register("tavily_search")
class TavilySearch(BaseTool):
    name = "tavily_search"
    description = "Search the web using Tavily API"

    @classmethod
    def execute(cls, query: str, **kwargs) -> Dict[str, Any]:
        # Implementation
        return {
            'success': True,
            'results': [...],
            'answer': "..."
        }
```

**Built-in Tools**:

| Tool | File | Purpose | Dependencies |
|------|------|---------|--------------|
| `claims_extractor` | `claims_extractor.py` | LLM-based claims extraction | `openai` |
| `arxiv_search` | `arxiv_search.py` | Academic paper search | `arxiv` |
| `tavily_search` | `tavily_search.py` | Web search via Tavily API | `tavily-python` |
| `render_tool` | `render_tool.py` | HTML rendering with Playwright | `playwright` |
| `mineru_ocr_tool` | `mineru_ocr_tool.py` | OCR with MinerU | `magic-pdf` |

### 3. LangChain Integration

#### AgentWrapper (agent_wrapper.py)

**Purpose**: Wrapper for LangChain 1.0 create_agent API

**Key Methods**:
```python
class AgentWrapper:
    @staticmethod
    def create_agent(llm, tools, system_prompt, **config)
        # Uses langchain.agents.create_agent (LangGraph-based)

    @staticmethod
    def invoke_and_format(agent, input_text, input_data, max_iterations)
        # Invokes agent and formats results for Dingo

    @staticmethod
    def get_openai_llm_from_dingo_config(dynamic_config)
        # Creates ChatOpenAI from Dingo config
```

**LangChain 1.0 Changes** (Nov 2025):
- Uses `create_agent()` instead of deprecated `AgentExecutor`
- Built on LangGraph for better state management
- `recursion_limit` instead of `max_iterations`
- Message-based invocation interface

#### LangChain Adapter (langchain_adapter.py)

**Purpose**: Converts Dingo tools to LangChain StructuredTool format

```python
def convert_dingo_tools(tool_names: List[str], agent_class) -> List[StructuredTool]:
    # Wraps Dingo tools for LangChain compatibility
    # Preserves Dingo's configuration injection mechanism
```

### 4. Agent Implementations

#### AgentFactCheck (agent_fact_check.py)

**Pattern**: LangChain-Based (Framework-Driven)

**Key Characteristics**:
- Sets `use_agent_executor = True`
- Overrides `_format_agent_input()` for custom input formatting
- Overrides `_get_system_prompt()` for task-specific instructions
- LangChain handles autonomous tool calling and reasoning
- Parses structured output in `aggregate_results()`

**Workflow**:
```
Input: Question + Response + Context (optional)
  ↓
LangChain Agent decides:
  - With context: MAY search for additional verification
  - Without context: MUST search to verify facts
  ↓
Agent autonomously:
  - Calls tavily_search tool as needed
  - Reasons about results
  - Returns structured output (HALLUCINATION_DETECTED: YES/NO)
  ↓
aggregate_results() parses output → EvalDetail
```

**When to Use**:
- ✅ Complex multi-step reasoning
- ✅ Benefit from LangChain's orchestration
- ✅ Prefer declarative style
- ✅ Rapid prototyping

#### AgentHallucination (agent_hallucination.py)

**Pattern**: Custom Workflow (Imperative)

**Key Characteristics**:
- Implements custom `eval()` with explicit workflow
- Manually calls `execute_tool()` for searches
- Manually calls `send_messages()` for LLM interactions
- Delegates to existing evaluator (LLMHallucination)
- Full control over execution flow

**Workflow**:
```
Input: Content + Context (optional)
  ↓
Check context availability
  ↓
├─ Has context? → Delegate to LLMHallucination
│
└─ No context? → Agent workflow:
    1. Extract factual claims (LLM call)
    2. Search web for each claim (Tavily tool)
    3. Synthesize context (combine results)
    4. Evaluate with synthesized context (LLMHallucination)
  ↓
Return EvalDetail with provenance
```

**When to Use**:
- Fine-grained control over steps
- Compose with existing evaluators
- Prefer explicit behavior
- Domain-specific workflows
- Conditional logic between steps

#### ArticleFactChecker (agent_article_fact_checker.py)

**Pattern**: Agent-First with Context Tracking (LangChain ReAct + Artifact Saving)

**Key Characteristics**:
- Sets `use_agent_executor = True` (same as AgentFactCheck)
- Overrides `eval()` to add context tracking and file saving
- Uses thread-local storage (`threading.local()`) for concurrent safety
- Extracts claims from tool_calls observation data
- Builds enriched per-claim verification records
- Saves intermediate artifacts (article, claims, verification, report)
- Produces dual-layer `EvalDetail.reason`: `[text_summary, structured_report_dict]`

**Workflow**:
```
Input: Article text (Markdown)
  |
eval() override:
  |- Save article content to output_path
  |- Set thread-local context (start_time, output_dir)
  |- Delegate to _eval_with_langchain_agent()
  |
LangChain Agent (ReAct):
  |- Extract claims (claims_extractor tool)
  |- Verify each claim (arxiv_search / tavily_search)
  |- Generate JSON report
  |
aggregate_results() override:
  |- Parse agent JSON output
  |- Extract claims from tool_calls
  |- Build per-claim verification records
  |- Build structured report (v2.0)
  |- Save artifacts (claims_extracted.jsonl, claims_verification.jsonl, report.json)
  |- Return EvalDetail with dual-layer reason
```

**When to Use**:
- Article-level comprehensive fact-checking
- Need intermediate artifacts (claims list, per-claim details, full report)
- Benefit from transparent evidence chains
- Want structured report alongside text summary

---

## Implementation Patterns

### Pattern Comparison

| Aspect | LangChain-Based | Custom Workflow | Agent-First + Context |
|--------|-----------------|-----------------|----------------------|
| **Control** | Framework-driven | Developer-driven | Framework + override |
| **Complexity** | Simple (declarative) | Moderate (imperative) | Moderate (hybrid) |
| **Flexibility** | Limited to LangChain | Unlimited | LangChain + artifacts |
| **Code Volume** | Low (~100 lines) | Medium (~200 lines) | High (~500+ lines) |
| **Tool Calling** | Automatic (ReAct) | Manual (`execute_tool()`) | Automatic (ReAct) |
| **LLM Calls** | Framework-managed | Manual (`send_messages()`) | Framework-managed |
| **Composability** | Limited | Delegate to evaluators | Artifact saving |
| **Best For** | Multi-step reasoning | Workflow composition | Article-level fact-check |
| **Example** | AgentFactCheck | AgentHallucination | ArticleFactChecker |

### Pattern 1: LangChain-Based (Framework-Driven)

**Implementation Checklist**:
- [ ] Set `use_agent_executor = True`
- [ ] Define `available_tools` list
- [ ] Override `_format_agent_input()` for input structuring
- [ ] Override `_get_system_prompt()` for task instructions
- [ ] Implement `aggregate_results()` for output parsing
- [ ] Return empty list in `plan_execution()` (not used)

**Minimal Example**:
```python
@Model.llm_register("MyAgent")
class MyAgent(BaseAgent):
    use_agent_executor = True
    available_tools = ["tavily_search"]
    max_iterations = 10

    @classmethod
    def _format_agent_input(cls, input_data: Data) -> str:
        return f"Evaluate: {input_data.content}"

    @classmethod
    def _get_system_prompt(cls, input_data: Data) -> str:
        return "You are a helpful agent. Use tools as needed."

    @classmethod
    def aggregate_results(cls, input_data: Data, results: List[Any]) -> EvalDetail:
        agent_result = results[0]
        # Parse agent output
        return EvalDetail(...)

    @classmethod
    def plan_execution(cls, input_data: Data) -> List[Dict[str, Any]]:
        return []  # Not used with LangChain
```

### Pattern 2: Custom Workflow (Imperative)

**Implementation Checklist**:
- [ ] Keep `use_agent_executor = False` (default)
- [ ] Define `available_tools` list
- [ ] Override `eval()` with custom workflow logic
- [ ] Call `execute_tool(tool_name, **kwargs)` for tools
- [ ] Call `send_messages(messages)` for LLM interactions
- [ ] Can delegate to other Dingo evaluators
- [ ] Return EvalDetail with detailed provenance

**Minimal Example**:
```python
@Model.llm_register("MyAgent")
class MyAgent(BaseAgent):
    available_tools = ["tavily_search"]

    @classmethod
    def eval(cls, input_data: Data) -> EvalDetail:
        # Step 1: Extract info with LLM
        messages = [{"role": "user", "content": f"Extract: {input_data.content}"}]
        extraction = cls.send_messages(messages)

        # Step 2: Search web
        search_result = cls.execute_tool('tavily_search', query=extraction)

        # Step 3: Evaluate
        if search_result['success']:
            # Custom logic
            return EvalDetail(...)
        else:
            return EvalDetail(status=True, label=["ERROR"])

    @classmethod
    def plan_execution(cls, input_data: Data) -> List[Dict[str, Any]]:
        return []  # Not used

    @classmethod
    def aggregate_results(cls, input_data: Data, results: List[Any]) -> EvalDetail:
        return EvalDetail(...)  # Not used
```

---

## Data Flow

### Complete Evaluation Pipeline

```
┌───────────────────────────────────────────────────────────────┐
│ 1. Configuration Loading                                       │
└───────────────────────────────────────────────────────────────┘
    JSON Config → InputArgs (Pydantic) → EvaluatorArgs
                                            ├─ name: "AgentFactCheck"
                                            ├─ config.key: API key
                                            ├─ config.model: "gpt-4"
                                            └─ config.parameters.agent_config:
                                                 ├─ max_iterations: 10
                                                 └─ tools:
                                                      └─ tavily_search:
                                                           └─ api_key: "..."

┌───────────────────────────────────────────────────────────────┐
│ 2. Data Loading & Conversion                                   │
└───────────────────────────────────────────────────────────────┘
    DataSource.load() → Generator[raw_data]
                            ↓
    Converter.convert() → Data objects
                            ├─ content: str
                            ├─ prompt: Optional[str]
                            ├─ context: Optional[List[str]]
                            └─ raw_data: Dict

┌───────────────────────────────────────────────────────────────┐
│ 3. Agent Execution (ThreadPoolExecutor)                        │
└───────────────────────────────────────────────────────────────┘
    BaseAgent.eval(Data) → EvalDetail
         │
         ├─ use_agent_executor?
         │
         ├─ YES (LangChain Path):
         │    ├─ _format_agent_input(Data) → input_text
         │    ├─ _get_system_prompt(Data) → system_prompt
         │    ├─ get_langchain_tools() → StructuredTool[]
         │    ├─ get_langchain_llm() → ChatOpenAI
         │    ├─ AgentWrapper.create_agent() → CompiledStateGraph
         │    ├─ AgentWrapper.invoke_and_format()
         │    │     ├─ Agent reasoning loop (ReAct)
         │    │     ├─ Tool calls (autonomous)
         │    │     └─ Final output
         │    └─ aggregate_results() → EvalDetail
         │
         └─ NO (Legacy Path):
              ├─ plan_execution(Data) → plan: List[step]
              ├─ Loop through steps:
              │    ├─ Tool step: execute_tool(name, **args)
              │    │               ├─ ToolRegistry.get(name)
              │    │               ├─ configure_tool()
              │    │               └─ tool.execute()
              │    └─ LLM step: send_messages(messages)
              └─ aggregate_results(results) → EvalDetail

┌───────────────────────────────────────────────────────────────┐
│ 4. Result Aggregation                                          │
└───────────────────────────────────────────────────────────────┘
    EvalDetail
      ├─ metric: str                    # "AgentFactCheck"
      ├─ status: bool                   # True = issue detected
      ├─ score: Optional[float]         # Numeric score
      ├─ label: List[str]              # ["QUALITY_BAD.HALLUCINATION"]
      └─ reason: List[Any]             # Dual-layer reason:
                                        #   reason[0]: str (human-readable text)
                                        #   reason[1]: Dict (structured report, optional)
                                        #   ArticleFactChecker uses this for
                                        #   text summary + full report dict

┌───────────────────────────────────────────────────────────────┐
│ 5. Summary Generation                                          │
└───────────────────────────────────────────────────────────────┘
    ResultInfo → SummaryModel
      ├─ total_count: int
      ├─ good_count: int
      ├─ bad_count: int
      ├─ type_ratio: Dict[field, Dict[label, count]]
      └─ metrics_score_stats: Dict[metric, stats]
```

### Tool Execution Flow

```
BaseAgent.execute_tool(tool_name, **kwargs)
    ↓
Check if tool in available_tools
    ↓
ToolRegistry.get(tool_name) → tool_class
    ↓
configure_tool(tool_name, tool_class)
    ├─ Extract config from dynamic_config.parameters.agent_config.tools.{tool_name}
    └─ tool_class.update_config(config_dict)
    ↓
tool_class.execute(**kwargs)
    ├─ Tool-specific logic (API calls, processing, etc.)
    └─ Return Dict[str, Any] with 'success' key
    ↓
Return to agent for processing
```

---

## Configuration

### Agent Configuration Structure

```json
{
  "evaluator": [
    {
      "name": "AgentFactCheck",
      "config": {
        "key": "your-openai-api-key",
        "api_url": "https://api.openai.com/v1",
        "model": "gpt-4-turbo-2024-04-09",
        "parameters": {
          "temperature": 0.3,
          "max_tokens": 2000,
          "agent_config": {
            "max_iterations": 10,
            "tools": {
              "tavily_search": {
                "api_key": "your-tavily-api-key",
                "max_results": 5,
                "search_depth": "advanced",
                "include_answer": true
              },
              "render_tool": {
                "timeout": 30000,
                "wait_until": "networkidle"
              }
            }
          }
        }
      },
      "evals": [
        {
          "eval_type": "llm",
          "name": "AgentFactCheck",
          "fields": {
            "content": "response",
            "prompt": "question",
            "context": "reference"
          }
        }
      ]
    }
  ]
}
```

### Configuration Injection Path

```
JSON Config
    ↓
InputArgs.evaluator → EvaluatorArgs[]
    ↓
Model.get_evaluator("AgentFactCheck", config) → Set dynamic_config
    ↓
BaseAgent.dynamic_config (class attribute)
    ├─ key: str
    ├─ api_url: str
    ├─ model: str
    └─ parameters: Dict
         ├─ temperature: float
         ├─ max_tokens: int
         └─ agent_config: Dict
              ├─ max_iterations: int
              └─ tools: Dict[tool_name, tool_config]
    ↓
get_tool_config(tool_name) → Dict
    ↓
tool_class.update_config(config_dict)
```

---

## Examples

### Example 1: Simple LangChain-Based Agent

```python
# File: dingo/model/llm/agent/my_simple_agent.py

from typing import Any, Dict, List
from dingo.io import Data
from dingo.io.output.eval_detail import EvalDetail, QualityLabel
from dingo.model import Model
from dingo.model.llm.agent.base_agent import BaseAgent


@Model.llm_register("MySimpleAgent")
class MySimpleAgent(BaseAgent):
    """Simple fact-checking agent using web search."""

    use_agent_executor = True
    available_tools = ["tavily_search"]
    max_iterations = 5

    @classmethod
    def _format_agent_input(cls, input_data: Data) -> str:
        return f"Verify this claim: {input_data.content}"

    @classmethod
    def _get_system_prompt(cls, input_data: Data) -> str:
        return """You are a fact-checker with web search.

Verify the claim using web search if needed.
Return your analysis in this format:

VERIFIED: [YES or NO]
EXPLANATION: [Your analysis]
"""

    @classmethod
    def aggregate_results(cls, input_data: Data, results: List[Any]) -> EvalDetail:
        agent_result = results[0]
        output = agent_result.get('output', '')

        # Parse output
        verified = 'VERIFIED: YES' in output.upper()

        result = EvalDetail(metric=cls.__name__)
        result.status = not verified  # True = problem
        result.label = [
            QualityLabel.QUALITY_GOOD if verified
            else f"{QualityLabel.QUALITY_BAD_PREFIX}UNVERIFIED"
        ]
        result.reason = [output]
        return result

    @classmethod
    def plan_execution(cls, input_data: Data) -> List[Dict[str, Any]]:
        return []  # Not used with LangChain
```

### Example 2: Custom Workflow Agent

```python
# File: dingo/model/llm/agent/my_workflow_agent.py

from typing import Any, Dict, List
from dingo.io import Data
from dingo.io.output.eval_detail import EvalDetail, QualityLabel
from dingo.model import Model
from dingo.model.llm.agent.base_agent import BaseAgent
from dingo.utils import log


@Model.llm_register("MyWorkflowAgent")
class MyWorkflowAgent(BaseAgent):
    """Custom workflow for claim verification."""

    available_tools = ["tavily_search"]

    @classmethod
    def eval(cls, input_data: Data) -> EvalDetail:
        try:
            cls.create_client()

            # Step 1: Check if claim is verifiable
            messages = [{
                "role": "user",
                "content": f"Is this a factual claim that can be verified? "
                          f"Answer YES or NO: {input_data.content}"
            }]
            is_verifiable = cls.send_messages(messages)

            if 'NO' in is_verifiable.upper():
                return EvalDetail(
                    metric=cls.__name__,
                    status=False,
                    label=[QualityLabel.QUALITY_GOOD],
                    reason=["Not a factual claim"]
                )

            # Step 2: Search web for verification
            log.info(f"{cls.__name__}: Searching web for verification")
            search_result = cls.execute_tool(
                'tavily_search',
                query=input_data.content
            )

            if not search_result.get('success'):
                return cls._error_result("Web search failed")

            # Step 3: Evaluate with search context
            messages = [{
                "role": "user",
                "content": f"Based on these search results, is the claim accurate?\n\n"
                          f"Claim: {input_data.content}\n\n"
                          f"Search Results: {search_result.get('answer', '')}\n\n"
                          f"Answer: ACCURATE or INACCURATE"
            }]
            evaluation = cls.send_messages(messages)

            is_accurate = 'ACCURATE' in evaluation and 'INACCURATE' not in evaluation

            return EvalDetail(
                metric=cls.__name__,
                status=not is_accurate,
                label=[
                    QualityLabel.QUALITY_GOOD if is_accurate
                    else f"{QualityLabel.QUALITY_BAD_PREFIX}INACCURATE"
                ],
                reason=[
                    evaluation,
                    f"\nWeb searches: {len(search_result.get('results', []))}"
                ]
            )

        except Exception as e:
            log.error(f"{cls.__name__} failed: {e}")
            return cls._error_result(str(e))

    @classmethod
    def _error_result(cls, error: str) -> EvalDetail:
        return EvalDetail(
            metric=cls.__name__,
            status=True,
            label=[f"{QualityLabel.QUALITY_BAD_PREFIX}AGENT_ERROR"],
            reason=[f"Error: {error}"]
        )

    @classmethod
    def plan_execution(cls, input_data: Data) -> List[Dict[str, Any]]:
        return []  # Not used

    @classmethod
    def aggregate_results(cls, input_data: Data, results: List[Any]) -> EvalDetail:
        return EvalDetail(metric=cls.__name__)  # Not used
```

### Example 3: Custom Tool

```python
# File: dingo/model/llm/agent/tools/my_custom_tool.py

from typing import Any, Dict
from dingo.model.llm.agent.tools import BaseTool, ToolConfig, tool_register
from dingo.utils import log


class MyToolConfig(ToolConfig):
    """Custom configuration for MyTool."""
    api_endpoint: str = "https://api.example.com"
    api_key: str = None


@tool_register("my_custom_tool")
class MyCustomTool(BaseTool):
    """Custom tool for demonstration."""

    name = "my_custom_tool"
    description = "Performs a custom operation on the input"
    config = MyToolConfig()

    @classmethod
    def execute(cls, input_text: str, **kwargs) -> Dict[str, Any]:
        """
        Execute the custom tool.

        Args:
            input_text: Text to process
            **kwargs: Additional arguments

        Returns:
            Dict with success status and results
        """
        try:
            # Validate configuration
            cls.validate_config()

            # Perform custom operation
            log.info(f"{cls.name}: Processing input")

            # Example: Call external API
            # result = requests.post(
            #     cls.config.api_endpoint,
            #     headers={"Authorization": f"Bearer {cls.config.api_key}"},
            #     json={"text": input_text}
            # )

            # Mock result for demonstration
            result_data = {
                "processed": input_text.upper(),
                "length": len(input_text)
            }

            return {
                'success': True,
                'data': result_data,
                'tool': cls.name
            }

        except Exception as e:
            log.error(f"{cls.name} failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'tool': cls.name
            }
```

### Example 4: Configuration File

```json
{
  "input_path": "data/hallucination_test.jsonl",
  "output_path": "outputs/agent_results",
  "dataset": {
    "source": "local",
    "format": "jsonl"
  },
  "executor": {
    "name": "local",
    "max_workers": 4,
    "batch_size": 100,
    "eval_group": ["agent"]
  },
  "evaluator": [
    {
      "name": "AgentFactCheck",
      "config": {
        "key": "${OPENAI_API_KEY}",
        "api_url": "https://api.openai.com/v1",
        "model": "gpt-4-turbo-2024-04-09",
        "parameters": {
          "temperature": 0.3,
          "max_tokens": 2000,
          "agent_config": {
            "max_iterations": 10,
            "tools": {
              "tavily_search": {
                "api_key": "${TAVILY_API_KEY}",
                "max_results": 5,
                "search_depth": "advanced",
                "include_answer": true,
                "include_raw_content": false
              }
            }
          }
        }
      },
      "evals": [
        {
          "eval_type": "llm",
          "name": "AgentFactCheck",
          "fields": {
            "content": "response",
            "prompt": "question",
            "context": "context"
          }
        }
      ]
    }
  ]
}
```

---

## Summary

### Key Takeaways

1. **Architecture**: Agents extend `BaseOpenAI` and are registered via `@Model.llm_register()`
2. **Location**: All agent code lives under `dingo/model/llm/agent/`
3. **Three Patterns**: LangChain-based (declarative), Custom Workflow (imperative), Agent-First + Context (hybrid)
4. **Tool System**: Centralized registry with configuration injection
5. **Execution**: Runs in ThreadPoolExecutor alongside other LLMs
6. **Configuration**: Nested under `parameters.agent_config` in evaluator config
7. **Artifact Saving**: ArticleFactChecker demonstrates intermediate artifact saving via `output_path`

### Implementation Checklist

Creating a new agent:
- [ ] Choose pattern (LangChain vs Custom)
- [ ] Create agent file under `dingo/model/llm/agent/`
- [ ] Extend `BaseAgent`
- [ ] Register with `@Model.llm_register("YourAgent")`
- [ ] Define `available_tools` list
- [ ] Implement required methods based on pattern
- [ ] Add tests under `test/scripts/model/llm/agent/`
- [ ] Update documentation
- [ ] Add example usage under `examples/agent/`

Creating a new tool:
- [ ] Create tool file under `dingo/model/llm/agent/tools/`
- [ ] Extend `BaseTool`
- [ ] Register with `@tool_register("your_tool")`
- [ ] Implement `execute()` method
- [ ] Define custom `ToolConfig` if needed
- [ ] Add tests under `test/scripts/model/llm/agent/tools/`
- [ ] Update requirements/agent.txt if dependencies needed

### Next Steps

- Read `docs/agent_development_guide.md` for detailed implementation guide
- Study `agent_fact_check.py` for LangChain pattern example
- Study `agent_hallucination.py` for custom workflow example
- Study `agent_article_fact_checker.py` for Agent-First + artifact saving pattern
- Review `examples/agent/` for usage examples
- Check `test/scripts/model/llm/agent/` for testing patterns

---

## Reference Links

- [Agent Development Guide](./agent_development_guide.md) - Comprehensive development guide
- [Article Fact-Checking Guide](./article_fact_checking_guide.md) - ArticleFactChecker usage guide
- [CLAUDE.md](../CLAUDE.md) - Project overview and common commands
- [LangChain Documentation](https://python.langchain.com/docs/concepts/agents/) - Agent concepts
- [Tavily API](https://tavily.com/) - Web search tool documentation
