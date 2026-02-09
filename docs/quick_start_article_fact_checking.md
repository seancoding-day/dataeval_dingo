# Quick Start: Article Fact-Checking

快速开始使用 ArticleFactChecker 进行文章事实审查。

## 5 分钟快速开始

### 1. 安装依赖

```bash
pip install -r requirements/agent.txt
```

可选(用于学术论文验证):
```bash
pip install arxiv
```

### 2. 设置 API 密钥

```bash
export OPENAI_API_KEY='your-openai-api-key'
export TAVILY_API_KEY='your-tavily-api-key'  # 可选
```

### 3. 运行示例

```bash
python examples/agent/agent_article_fact_checking_example.py
```

### 4. 查看结果

```
Starting Article Fact-Checking
======================================================================
Article: test/data/blog_article.md (via temp JSONL)
Agent: ArticleFactChecker (Agent-First architecture)
Model: deepseek-chat
Artifact output: outputs/article_factcheck/
======================================================================

Executing agent-based fact-checking...

======================================================================
FACT-CHECKING RESULTS
======================================================================

Metric: ArticleFactChecker
Status: Issues Found
Accuracy Score: 75.00%

Detailed Report:
----------------------------------------------------------------------
Article Fact-Checking Report
======================================================================
Total Claims Analyzed: 20
Verified Claims: 15
False Claims: 5
Unverifiable Claims: 0
Overall Accuracy: 75.0%

Agent Performance:
   Tool Calls: 8
   Reasoning Steps: 10

FALSE CLAIMS DETAILED COMPARISON:
======================================================================

#1 INSTITUTIONAL_MISATTRIBUTION [Severity: high]
   Article Claimed:
      OmniDocBench was released by Tsinghua University, Alibaba DAMO...
   Actual Truth:
      OmniDocBench was released by Shanghai AI Lab, Abaka AI, 2077AI
   Evidence:
      Verified via arXiv paper 2412.07626 author list

Structured Report Summary:
  Report Version: 2.0
  Verified True:  15
  Verified False: 5
  Unverifiable:   0
  Claims Extracted: 20
  Execution Time: 45.2s
----------------------------------------------------------------------

Fact-checking complete!

Dingo standard output: outputs/YYYYMMDD_HHMMSS_uuid/
  |-- all_results.jsonl             (EvalDetail with dual-layer reason)
  +-- summary.json                  (aggregated statistics)

Intermediate artifacts: outputs/article_factcheck/
  |-- article_content.md           (original Markdown article)
  |-- claims_extracted.jsonl        (extracted claims, one per line)
  |-- claims_verification.jsonl     (per-claim verification details)
  +-- verification_report.json      (full structured report v2.0)
```

## 使用自己的文章

### 方法 1: 直接调用 (最简单)

```python
import os
from dingo.io.input import Data
from dingo.model.llm.agent import ArticleFactChecker

# 确保设置了 API keys
os.environ["OPENAI_API_KEY"] = "your-openai-api-key"
os.environ["TAVILY_API_KEY"] = "your-tavily-api-key"  # 可选

# 读取文章
with open("your_article.md", "r") as f:
    article_text = f.read()

# 执行审查
data = Data(content=article_text)
result = ArticleFactChecker.eval(data)

# 打印结果
print(f"准确率: {result.score:.1%}")

# reason[0]: 人类可读的文本摘要 (always str)
if result.reason:
    print(result.reason[0] if isinstance(result.reason[0], str) else str(result.reason[0]))

    # reason[1]: 结构化报告 dict (当 output_path 已设置时)
    if len(result.reason) > 1 and isinstance(result.reason[1], dict):
        report = result.reason[1]
        v_summary = report.get('verification_summary', {})
        print(f"Verified True: {v_summary.get('verified_true', 'N/A')}")
        print(f"Verified False: {v_summary.get('verified_false', 'N/A')}")
```

### 方法 2: 通过 InputArgs + Executor (完整配置)

> **注意**: Executor 需要 `input_path` 指向文件。`plaintext` 格式会逐行读取文件，将每行作为独立的 Data 对象，不适合文章级输入。因此需要先将文章内容转为 JSONL 格式（`json.dumps` 会将换行编码为 `\n`，保持整篇文章在一行 JSON 中）。

```python
import json
import os
import tempfile

from dingo.config import InputArgs
from dingo.exec import Executor

# 读取文章
with open("your_article.md", "r") as f:
    article_text = f.read()

# 将文章转为 JSONL（整篇文章作为一个 Data 对象）
temp_jsonl = tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False, encoding='utf-8')
temp_jsonl.write(json.dumps({"content": article_text}, ensure_ascii=False) + '\n')
temp_jsonl.close()

# 配置
config = {
    "input_path": temp_jsonl.name,
    "dataset": {"source": "local", "format": "jsonl"},
    "executor": {"max_workers": 1},
    "evaluator": [{
        "fields": {"content": "content"},
        "evals": [{
            "name": "ArticleFactChecker",
            "config": {
                "key": os.getenv("OPENAI_API_KEY"),
                "model": "deepseek-chat",
                "parameters": {
                    "agent_config": {
                        "max_iterations": 15,
                        "output_path": "outputs/article_factcheck/",  # 保存中间产物
                        "tools": {
                            "claims_extractor": {
                                "api_key": os.getenv("OPENAI_API_KEY"),
                                "max_claims": 50,
                                "claim_types": [
                                    "factual", "statistical", "attribution", "institutional",
                                    "temporal", "comparative", "monetary", "technical"
                                ]
                            },
                            "tavily_search": {
                                "api_key": os.getenv("TAVILY_API_KEY")
                            },
                            "arxiv_search": {"max_results": 5}
                        }
                    }
                }
            }
        }]
    }]
}

# 执行
input_args = InputArgs(**config)
executor = Executor.exec_map["local"](input_args)
result = executor.execute()

print(f"Total: {result.total_count}, Good: {result.good_count}, Bad: {result.bad_count}")

# 清理临时文件
os.unlink(temp_jsonl.name)
```

### 方法 3: CLI

```bash
# 1. 将文章转为 JSONL 格式
python -c "
import json
with open('your_article.md', 'r') as f:
    text = f.read()
with open('article_input.jsonl', 'w') as f:
    f.write(json.dumps({'content': text}, ensure_ascii=False) + '\n')
"

# 2. 创建配置文件
cat > my_config.json << 'EOF'
{
  "input_path": "article_input.jsonl",
  "dataset": {"source": "local", "format": "jsonl"},
  "evaluator": [{
    "fields": {"content": "content"},
    "evals": [{
      "name": "ArticleFactChecker",
      "config": {
        "key": "${OPENAI_API_KEY}",
        "model": "deepseek-chat",
        "parameters": {
          "agent_config": {
            "tools": {
              "claims_extractor": {"api_key": "${OPENAI_API_KEY}"}
            }
          }
        }
      }
    }]
  }]
}
EOF

# 3. 运行审查
python -m dingo.run.cli --input my_config.json

# 4. 查看输出
cat output_*/result_info.json
```

## 验证特定类型的声明

你可以通过配置 `claim_types` 来仅验证特定类型的声明。

> **前提**: 以下示例假设你已将文章内容转为 JSONL 文件（参见方法 2）。

### 仅验证机构归属

```python
import os
from dingo.config import InputArgs
from dingo.exec import Executor

config = {
    "input_path": "article_input.jsonl",  # 文章内容的 JSONL 文件
    "dataset": {"source": "local", "format": "jsonl"},
    "executor": {"max_workers": 1},
    "evaluator": [{
        "fields": {"content": "content"},
        "evals": [{
            "name": "ArticleFactChecker",
            "config": {
                "key": os.getenv("OPENAI_API_KEY"),
                "model": "deepseek-chat",
                "parameters": {
                    "agent_config": {
                        "tools": {
                            "claims_extractor": {
                                "api_key": os.getenv("OPENAI_API_KEY"),
                                "claim_types": ["institutional"]  # 仅提取机构声明
                            },
                            "arxiv_search": {"max_results": 5}
                        }
                    }
                }
            }
        }]
    }]
}

input_args = InputArgs(**config)
result = Executor.exec_map["local"](input_args).execute()
```

### 仅验证统计数据和价格信息

```python
config = {
    "input_path": "product_review_input.jsonl",  # 产品评测的 JSONL 文件
    "dataset": {"source": "local", "format": "jsonl"},
    "executor": {"max_workers": 1},
    "evaluator": [{
        "fields": {"content": "content"},
        "evals": [{
            "name": "ArticleFactChecker",
            "config": {
                "key": os.getenv("OPENAI_API_KEY"),
                "model": "deepseek-chat",
                "parameters": {
                    "agent_config": {
                        "tools": {
                            "claims_extractor": {
                                "api_key": os.getenv("OPENAI_API_KEY"),
                                "claim_types": ["statistical", "monetary"]  # 统计和价格
                            },
                            "tavily_search": {"api_key": os.getenv("TAVILY_API_KEY")}
                        }
                    }
                }
            }
        }]
    }]
}

input_args = InputArgs(**config)
result = Executor.exec_map["local"](input_args).execute()
```

## 常见问题

### Q: 需要哪些 API 密钥?

**必需:**
- `OPENAI_API_KEY`: 用于 LLM agent 和声明提取

**可选(但推荐):**
- `TAVILY_API_KEY`: 用于通用网络搜索验证

**可选(用于学术验证):**
- `arxiv` Python 库(无需 API 密钥)

### Q: 成本如何?

使用 `deepseek-chat` 模型:
- 短文章(<1000字): ~$0.05-0.10
- 长文章(2000-3000字): ~$0.15-0.25

主要成本来自:
1. 声明提取(每个文本块调用一次 LLM)
2. Agent 推理(每个验证步骤)

### Q: 需要多长时间?

- 短文章(<1000字): 30-60 秒
- 长文章(2000-3000字): 1-2 分钟

时间受以下因素影响:
- 文章长度
- 声明数量
- API 响应速度
- `max_iterations` 设置

### Q: 准确率如何?

Agent 的准确率取决于:
- **机构验证**: 非常高(基于 arXiv 官方数据)
- **统计数据**: 高(基于可靠网络来源)
- **主观声明**: 可能不适用(注意区分)

最佳应用场景:
- 学术机构归属
- 论文引用
- 统计数据
- 可验证的事实声明

### Q: 如何提高准确率?

1. **增加 max_iterations:**
   ```python
   'agent_config': {'max_iterations': 20}  # 默认: 10
   ```

2. **启用所有验证工具:**
   ```python
   'tools': {
       'claims_extractor': {...},
       'arxiv_search': {},
       'tavily_search': {'api_key': "..."}  # 添加此工具
   }
   ```

3. **提高声明提取质量:**
   ```python
   'claims_extractor': {
       'max_claims': 50,  # 提取更多声明
       'temperature': 0.0  # 更确定性的提取
   }
   ```

## 下一步

- 阅读[完整文档](./article_fact_checking_guide.md)
- 运行[测试](../test/scripts/model/llm/agent/test_article_fact_checker.py)
- 查看[示例代码](../examples/agent/agent_article_fact_checking_example.py)
- 阅读[Agent 架构](./agent_architecture.md)

## 支持

遇到问题? 查看:
- [故障排除](./article_fact_checking_guide.md#troubleshooting)
- [测试用例](../test/scripts/model/llm/agent/)
- [示例代码](../examples/agent/)
