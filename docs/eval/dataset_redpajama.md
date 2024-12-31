# Dataset Redpajama

## 数据集介绍
本数据集旨在评估dingo内置提示词的准确性，因此选择开源数据集redpajama，从中抽取数据构建测试集。

| 字段名          | 介绍                        |
|--------------|---------------------------|
| data_id      | 数据id，没有特殊含义，用户可根据自身需求修改   |
| content      | 待测试数据                     |
| language     | 语言类型                      |
| error_status | 数据状态，True为负例数据，False为正例数据 |
| type_list    | 负例数据的负例类型，正例数据该字段则为空列表    |
| name_list    | 负例数据的负例名称，正例数据该字段则为空列表    |
| reason_list  | 负例数据的负例介绍，正例数据该字段则为空列表    |

链接：
https://huggingface.co/datasets/chupei/redpajama_good_model
https://huggingface.co/datasets/chupei/redpajama_bad_model

### 数据集构成
| 类型                        | 数量  |
|---------------------------|-----|
| 正例数据                      | 101 |
| 负例数据：disfluency           | 4   |
| 负例数据：dissimilarity        | 3   |
| 负例数据：disunderstandability | 2   |
| 负例数据：incompleteness       | 27  |
| 负例数据：insecurity           | 16  |
| 负例数据：irrelevance          | 49  |

## 提示词介绍
本次测试使用内置的 **PromptTextQualityV2** 作为提示词，具体包含的内容可以参考：[PromptTextQualityV2介绍](../../dingo/model/prompt/prompt_text_quality_v2.py)
内置的提示词集合可以参考：[提示词集合](../../dingo/model/prompt)

## 评测结果
### 概念介绍
正例数据与负例数据经过评测，均会生成对应的summary文件，因此需要对结果进行定义，明确概念。

| 名称  | 介绍                            |
|-----|-------------------------------|
| TP  | True Positive：正例数据中被评测为正例的数量  |
| FP  | False Positive：负例数据中被评测为正例的数量 |
| TN  | True Negative：负例数据中被评测为负例的数量  |
| FN  | False Negative：正例数据中被评测为负例的数量 |
| 准确率 | TP / (TP + FP) 被评测为正例中正例数据的比率 |
| 召回率 | TP / (TP + FN) 正例数据被评测为正例的比率  |
| F1  | (准确率 + 召回率) / 2               |

### 结果展示
| 数据集名称     | TP | FP | TN  | FN | 准确率% | 召回率% | F1 |
|-----------|----|----|-----|----|------|------|----|
| redpajama | 95 | 0  | 101 | 6  | 100  | 94   | 97 |

## 评测方式

```python
from dingo.io import InputArgs
from dingo.exec import Executor

input_data = {
    "eval_group": "v2",
    "input_path": "chupei/redpajama_good_model",
    "save_data": True,
    "save_correct": True,
    "save_raw": True,
    "max_workers": 10,
    "batch_size": 10,
    "data_format": "jsonl",
    "column_content": "content",
    "custom_config":
        {
            "prompt_list": ["PromptTextQualityV2"],
            "llm_config":
                {
                    "detect_text_quality_detail":
                        {
                            "key": "Your Key",
                            "api_url": "Your Url",
                        }
                }
        }
}
input_args = InputArgs(**input_data)
executor = Executor.exec_map["local"](input_args)
result = executor.execute()
print(result)
```
