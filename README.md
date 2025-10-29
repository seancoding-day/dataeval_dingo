<!-- SEO Meta Information and Structured Data -->
<div itemscope itemtype="https://schema.org/SoftwareApplication" align="center" xmlns="http://www.w3.org/1999/html">
  <meta itemprop="name" content="Dingo: A Comprehensive AI Data Quality Evaluation Tool">
  <meta itemprop="description" content="Comprehensive AI-powered data quality assessment platform for machine learning datasets, LLM training data validation, hallucination detection, and RAG system evaluation">
  <meta itemprop="applicationCategory" content="Data Quality Software">
  <meta itemprop="operatingSystem" content="Cross-platform">
  <meta itemprop="programmingLanguage" content="Python">
  <meta itemprop="url" content="https://github.com/MigoXLab/dingo">
  <meta itemprop="downloadUrl" content="https://pypi.org/project/dingo-python/">
  <meta itemprop="softwareVersion" content="latest">
  <meta itemprop="license" content="Apache-2.0">

<!-- logo -->
<p align="center">
  <img src="docs/assets/dingo-logo.png" width="300px" style="vertical-align:middle;" alt="Dingo AI Data Quality Evaluation Tool Logo">
</p>

<!-- badges -->
<p align="center">
  <a href="https://github.com/pre-commit/pre-commit"><img src="https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white" alt="pre-commit"></a>
  <a href="https://pypi.org/project/dingo-python/"><img src="https://img.shields.io/pypi/v/dingo-python.svg" alt="PyPI version"></a>
  <a href="https://pypi.org/project/dingo-python/"><img src="https://img.shields.io/pypi/pyversions/dingo-python.svg" alt="Python versions"></a>
  <a href="https://github.com/DataEval/dingo/blob/main/LICENSE"><img src="https://img.shields.io/github/license/DataEval/dingo" alt="License"></a>
  <a href="https://github.com/DataEval/dingo/stargazers"><img src="https://img.shields.io/github/stars/DataEval/dingo" alt="GitHub stars"></a>
  <a href="https://github.com/DataEval/dingo/network/members"><img src="https://img.shields.io/github/forks/DataEval/dingo" alt="GitHub forks"></a>
  <a href="https://github.com/DataEval/dingo/issues"><img src="https://img.shields.io/github/issues/DataEval/dingo" alt="GitHub issues"></a>
  <a href="https://mseep.ai/app/dataeval-dingo"><img src="https://mseep.net/pr/dataeval-dingo-badge.png" alt="MseeP.ai Security Assessment Badge" height="20"></a>
  <a href="https://deepwiki.com/MigoXLab/dingo"><img src="https://deepwiki.com/badge.svg" alt="Ask DeepWiki"></a>
  <a href="https://archestra.ai/mcp-catalog/dataeval__dingo"><img src="https://archestra.ai/mcp-catalog/api/badge/quality/DataEval/dingo" alt="Trust Score"></a>
</p>

</div>


<div align="center">

[English](README.md) · [简体中文](README_zh-CN.md) · [日本語](README_ja.md)

</div>


<!-- join us -->

<p align="center">
    👋 join us on <a href="https://discord.gg/Jhgb2eKWh8" target="_blank">Discord</a> and <a href="./docs/assets/wechat.jpg" target="_blank">WeChat</a>
</p>


<p align="center">
  If you like Dingo, please give us a ⭐ on GitHub!
  <br/>
  <a href="https://github.com/DataEval/dingo/stargazers" target="_blank">
    <img src="docs/assets/clickstar_2.gif" alt="Click Star" width="480">
  </a>
</p>


# Introduction of Dingo

Dingo is a data quality evaluation tool that helps you automatically detect data quality issues in your datasets. Dingo provides a variety of built-in rules and model evaluation methods, and also supports custom evaluation methods. Dingo supports commonly used text datasets and multimodal datasets, including pre-training datasets, fine-tuning datasets, and evaluation datasets. In addition, Dingo supports multiple usage methods, including local CLI and SDK, making it easy to integrate into various evaluation platforms, such as [OpenCompass](https://github.com/open-compass/opencompass).

## Architecture Diagram

![Architecture of dingo](./docs/assets/architeture.png)

# Quick Start

## Installation

```shell
pip install dingo-python
```

## Example Use Cases of Dingo

### 1. Evaluate LLM chat data

```python
from dingo.config.input_args import EvaluatorLLMArgs
from dingo.io.input import Data
from dingo.model.llm.llm_text_quality_model_base import LLMTextQualityModelBase
from dingo.model.rule.rule_common import RuleEnterAndSpace

data = Data(
    data_id='123',
    prompt="hello, introduce the world",
    content="Hello! The world is a vast and diverse place, full of wonders, cultures, and incredible natural beauty."
)


def llm():
    LLMTextQualityModelBase.dynamic_config = EvaluatorLLMArgs(
        key='YOUR_API_KEY',
        api_url='https://api.openai.com/v1/chat/completions',
        model='gpt-4o',
    )
    res = LLMTextQualityModelBase.eval(data)
    print(res)


def rule():
    res = RuleEnterAndSpace().eval(data)
    print(res)
```

### 2. Evaluate Dataset

```python
from dingo.config import InputArgs
from dingo.exec import Executor

# Evaluate a dataset from Hugging Face
input_data = {
    "input_path": "tatsu-lab/alpaca",  # Dataset from Hugging Face
    "dataset": {
        "source": "hugging_face",
        "format": "plaintext"  # Format: plaintext
    },
    "executor": {
        "eval_group": "sft",  # Rule set for SFT data
        "result_save": {
            "bad": True  # Save evaluation results
        }
    }
}

input_args = InputArgs(**input_data)
executor = Executor.exec_map["local"](input_args)
result = executor.execute()
print(result)
```

## Command Line Interface

### Evaluate with Rule Sets

```shell
python -m dingo.run.cli --input test/env/local_plaintext.json
```

### Evaluate with LLM (e.g., GPT-4o)

```shell
python -m dingo.run.cli --input test/env/local_json.json
```

## GUI Visualization

After evaluation (with `result_save.bad=True`), a frontend page will be automatically generated. To manually start the frontend:

```shell
python -m dingo.run.vsl --input output_directory
```

Where `output_directory` contains the evaluation results with a `summary.json` file.

![GUI output](docs/assets/dingo_gui.png)

## Online Demo
Try Dingo on our online demo: [(Hugging Face)🤗](https://huggingface.co/spaces/DataEval/dingo)

## Local Demo
Try Dingo in local:

```shell
cd app_gradio
python app.py
```

![Gradio demo](docs/assets/gradio_demo.png)


## Google Colab Demo
Experience Dingo interactively with Google Colab notebook: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/DataEval/dingo/blob/dev/examples/colab/dingo_colab_demo.ipynb)



# MCP Server

Dingo includes an experimental Model Context Protocol (MCP) server. For details on running the server and integrating it with clients like Cursor, please see the dedicated documentation:

[English](README_mcp.md) · [简体中文](README_mcp_zh-CN.md) · [日本語](README_mcp_ja.md)

## Video Demonstration

To help you get started quickly with Dingo MCP, we've created a video walkthrough:

https://github.com/user-attachments/assets/aca26f4c-3f2e-445e-9ef9-9331c4d7a37b

This video demonstrates step-by-step how to use Dingo MCP server with Cursor.


# Data Quality Metrics

Dingo provides comprehensive data quality assessment through both rule-based and prompt-based evaluation metrics. These metrics cover multiple quality dimensions including effectiveness, completeness, similarity, security, and more.

📊 **[View Complete Metrics Documentation →](docs/metrics.md)**

Our evaluation system includes:
- **Pretrain Text Quality Assessment Metrics**: Pre-training data quality evaluation using DataMan methodology and enhanced multi-dimensional assessment
- **SFT Data Assessment Metrics**: Honest, Helpful, Harmless evaluation for supervised fine-tuning data
- **Classification Metrics**: Topic categorization and content classification
- **Multimodality Assessment Metrics**: Image classification and relevance evaluation
- **Rule-Based Quality Metrics**: Automated quality checks using heuristic rules for effectiveness and similarity detection
- **Factuality Assessment Metrics**: Two-stage factuality evaluation based on GPT-5 System Card
- etc

Most metrics are backed by academic sources to ensure objectivity and scientific rigor.

### Using LLM Assessment in Evaluation

To use these assessment prompts in your evaluations, specify them in your configuration:

```python
input_data = {
    # Other parameters...
    "executor": {
        "prompt_list": ["QUALITY_BAD_SIMILARITY"],  # Specific prompt to use
    },
    "evaluator": {
        "llm_config": {
            "LLMTextQualityPromptBase": {  # LLM model to use
                "model": "gpt-4o",
                "key": "YOUR_API_KEY",
                "api_url": "https://api.openai.com/v1/chat/completions"
            }
        }
    }
}
```

You can customize these prompts to focus on specific quality dimensions or to adapt to particular domain requirements. When combined with appropriate LLM models, these prompts enable comprehensive evaluation of data quality across multiple dimensions.

### Hallucination Detection & RAG System Evaluation

For detailed guidance on using Dingo's hallucination detection capabilities, including HHEM-2.1-Open local inference and LLM-based evaluation:

📖 **[View Hallucination Detection Guide →](docs/hallucination_guide.md)**

### Factuality Assessment

For comprehensive guidance on using Dingo's two-stage factuality evaluation system:

📖 **[View Factuality Assessment Guide →](docs/factcheck_guide.md)**

# Rule Groups

Dingo provides pre-configured rule groups for different types of datasets:

| Group | Use Case | Example Rules |
|-------|----------|---------------|
| `default` | General text quality | `RuleColonEnd`, `RuleContentNull`, `RuleDocRepeat`, etc. |
| `sft` | Fine-tuning datasets | Rules from `default` plus `RuleHallucinationHHEM` for hallucination detection |
| `rag` | RAG system evaluation | `RuleHallucinationHHEM`, `PromptHallucination` for response consistency |
| `hallucination` | Hallucination detection | `PromptHallucination` with LLM-based evaluation |
| `pretrain` | Pre-training datasets | Comprehensive set of 20+ rules including `RuleAlphaWords`, `RuleCapitalWords`, etc. |

To use a specific rule group:

```python
input_data = {
    "executor": {
        "eval_group": "sft",  # Use "default", "sft", "rag", "hallucination", or "pretrain"
    }
    # other parameters...
}
```

# Feature Highlights

## Multi-source & Multi-modal Support

- **Data Sources**: Local files, Hugging Face datasets, S3 storage
- **Data Types**: Pre-training, fine-tuning, and evaluation datasets
- **Data Modalities**: Text and image

## Rule-based & Model-based Evaluation

- **Built-in Rules**: 20+ general heuristic evaluation rules
- **LLM Integration**: OpenAI, Kimi, and local models (e.g., Llama3)
- **Hallucination Detection**: HHEM-2.1-Open local model and GPT-based evaluation
- **RAG System Evaluation**: Response consistency and context alignment assessment
- **Custom Rules**: Easily extend with your own rules and models
- **Security Evaluation**: Perspective API integration

## Flexible Usage

- **Interfaces**: CLI and SDK options
- **Integration**: Easy integration with other platforms
- **Execution Engines**: Local and Spark

## Comprehensive Reporting

- **Quality Metrics**: 7-dimensional quality assessment
- **Traceability**: Detailed reports for anomaly tracking

# User Guide

## Custom Rules, Prompts, and Models

If the built-in rules don't meet your requirements, you can create custom ones:

### Custom Rule Example

```python
from dingo.model import Model
from dingo.model.rule.base import BaseRule
from dingo.config.input_args import EvaluatorRuleArgs
from dingo.io import Data
from dingo.model.modelres import ModelRes

@Model.rule_register('QUALITY_BAD_RELEVANCE', ['default'])
class MyCustomRule(BaseRule):
    """Check for custom pattern in text"""

    dynamic_config = EvaluatorRuleArgs(pattern=r'your_pattern_here')

    @classmethod
    def eval(cls, input_data: Data) -> ModelRes:
        res = ModelRes()
        # Your rule implementation here
        return res
```

### Custom LLM Integration

```python
from dingo.model import Model
from dingo.model.llm.base_openai import BaseOpenAI

@Model.llm_register('my_custom_model')
class MyCustomModel(BaseOpenAI):
    # Custom implementation here
    pass
```

See more examples in:
- [Register Rules](examples/register/sdk_register_rule.py)
- [Register Prompts](examples/register/sdk_register_prompt.py)
- [Register Models](examples/register/sdk_register_llm.py)

## Execution Engines

### Local Execution

```python
from dingo.config import InputArgs
from dingo.exec import Executor

input_args = InputArgs(**input_data)
executor = Executor.exec_map["local"](input_args)
result = executor.execute()

# Get results
summary = executor.get_summary()        # Overall evaluation summary
bad_data = executor.get_bad_info_list() # List of problematic data
good_data = executor.get_good_info_list() # List of high-quality data
```

### Spark Execution

```python
from dingo.config import InputArgs
from dingo.exec import Executor
from pyspark.sql import SparkSession

# Initialize Spark
spark = SparkSession.builder.appName("Dingo").getOrCreate()
spark_rdd = spark.sparkContext.parallelize([...])  # Your data as Data objects

input_data = {
    "executor": {
        "eval_group": "default",
        "result_save": {"bad": True}
    }
}
input_args = InputArgs(**input_data)
executor = Executor.exec_map["spark"](input_args, spark_session=spark, spark_rdd=spark_rdd)
result = executor.execute()
```

## Evaluation Reports

After evaluation, Dingo generates:

1. **Summary Report** (`summary.json`): Overall metrics and scores
2. **Detailed Reports**: Specific issues for each rule violation

Report Description:
1. **score**: `num_good` / `total`
2. **type_ratio**: The count of type / total, such as: `QUALITY_BAD_COMPLETENESS` / `total`
3. **name_ratio**: The count of name / total, such as: `QUALITY_BAD_COMPLETENESS-RuleColonEnd` / `total`

Example summary:
```json
{
    "task_id": "d6c922ec-981c-11ef-b723-7c10c9512fac",
    "task_name": "dingo",
    "eval_group": "default",
    "input_path": "test/data/test_local_jsonl.jsonl",
    "output_path": "outputs/d6c921ac-981c-11ef-b723-7c10c9512fac",
    "create_time": "20241101_144510",
    "score": 50.0,
    "num_good": 1,
    "num_bad": 1,
    "total": 2,
    "type_ratio": {
        "QUALITY_BAD_COMPLETENESS": 0.5,
        "QUALITY_BAD_RELEVANCE": 0.5
    },
    "name_ratio": {
        "QUALITY_BAD_COMPLETENESS-RuleColonEnd": 0.5,
        "QUALITY_BAD_RELEVANCE-RuleSpecialCharacter": 0.5
    }
}
```

# Future Plans

- [ ] Richer graphic and text evaluation indicators
- [ ] Audio and video data modality evaluation
- [ ] Small model evaluation (fasttext, Qurating)
- [ ] Data diversity evaluation

# Limitations

The current built-in detection rules and model methods focus on common data quality problems. For specialized evaluation needs, we recommend customizing detection rules.

# Acknowledgments

- [RedPajama-Data](https://github.com/togethercomputer/RedPajama-Data)
- [mlflow](https://github.com/mlflow/mlflow)
- [deepeval](https://github.com/confident-ai/deepeval)

# Contribution

We appreciate all the contributors for their efforts to improve and enhance `Dingo`. Please refer to the [Contribution Guide](docs/en/CONTRIBUTING.md) for guidance on contributing to the project.

# License

This project uses the [Apache 2.0 Open Source License](LICENSE).

This project uses fasttext for some functionality including language detection. fasttext is licensed under the MIT License, which is compatible with our Apache 2.0 license and provides flexibility for various usage scenarios.

# Citation

If you find this project useful, please consider citing our tool:

```
@misc{dingo,
  title={Dingo: A Comprehensive AI Data Quality Evaluation Tool for Large Models},
  author={Dingo Contributors},
  howpublished={\url{https://github.com/MigoXLab/dingo}},
  year={2024}
}
```
