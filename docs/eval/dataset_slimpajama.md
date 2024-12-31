# Dataset Slimpajama

## 数据集介绍
本数据集旨在评估dingo内置规则的准确性，因此选择开源数据集slimpajama，从中抽取数据构建测试集。

| 字段名          | 介绍                                       |
|--------------|------------------------------------------|
| data_id      | 数据id，没有特殊含义，用户可根据自身需求修改                  |
| content      | 待测试数据                                    |
| language     | 语言类型                                     |
| error_status | 数据状态，True为负例数据，False为正例数据                |
| type_list    | 负例数据的负例类型，正例数据该字段则为空列表                   |
| name_list    | 负例数据的负例名称，正例数据该字段则为空列表                   |
| reason_list  | 负例数据的负例介绍，正例数据该字段则为空列表                   |

链接：
https://huggingface.co/datasets/chupei/slimpajama_badcase_rule
https://huggingface.co/datasets/chupei/slimpajama_goodcase_rule

### 数据集构成
| 类型                                | 数量 |
|-----------------------------------|----|
| 正例数据                              | 82 |
| 负例数据：RuleAlphaWords               | 27 |
| 负例数据：RuleCapitalWords             | 26 |
| 负例数据：RuleCharNumber               | 5  |
| 负例数据：RuleDocRepeat                | 17 |
| 负例数据：RuleHtmlEntity               | 3  |
| 负例数据：RuleLineEndWithEllipsis      | 5  |
| 负例数据：RuleLineEndWithTerminal      | 5  |
| 负例数据：RuleLineStartWithBulletpoint | 6  |
| 负例数据：RuleLoremIpsum               | 5  |
| 负例数据：RuleMeanWordLength           | 12 |
| 负例数据：RuleNoPunc                   | 7  |
| 负例数据：RuleSentenceNumber           | 8  |
| 负例数据：RuleSpecialCharacter         | 4  |
| 负例数据：RuleStopWord                 | 24 |
| 负例数据：RuleSymbolWordRatio          | 5  |
| 负例数据：RuleUniqueWords              | 7  |
| 负例数据：RuleWordNumber               | 7  |

## 规则介绍
本次测试使用内置的 **pretrain** 作为eval_group，具体包含的规则可以参考：[集合介绍](../groups.md)
集合内部的规则可以参考：[规则介绍](../rules.md)

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
| 数据集名称      | TP | FP | TN  | FN | 准确率% | 召回率% | F1   |
|------------|----|----|-----|----|------|------|------|
| slimpajama | 78 | 5  | 103 | 4  | 94   | 95   | 94.5 |

## 评测方式

```python
from dingo.io import InputArgs
from dingo.exec import Executor

input_data = {
    "eval_group": "pretrain",
    "input_path": "chupei/slimpajama_badcase_rule",
    "save_data": True,
    "save_correct": True,
    "save_raw": True,
    "max_workers": 10,
    "batch_size": 10,
    "data_format": "jsonl",
    "column_content": "content",
}
input_args = InputArgs(**input_data)
executor = Executor.exec_map["local"](input_args)
result = executor.execute()
print(result)
```
