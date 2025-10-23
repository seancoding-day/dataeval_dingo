# VLMLayoutQuality Layout布局检测评估工具 使用文档

Dingo 提供了一种基于VLM的Layout布局检测质量评估，可帮助您：
- 评估Layout布局检测模型质量
- 生成模型质量报告

## 工具介绍

### VLMLayoutQuality

#### 功能说明
该工具用于评估文档解析模型效果，具体功能包括：
- 定义检测遗漏、检测不准、类别错误、阅读顺序等维度的布局检测错误类别
- 基于带Bbox框的图片作为输入，进行质量评估，并报告错误类型和原因
- 输出详细的评估报告

#### 技术细节
##### 文件结构

```
dingo/
  ├── model/
  │   ├── llm/
  │   │   └── vlm_layout_quality.py         # 评估器实现
  │   └── prompt/
  │       └── prompt_layout_quality.py      # 评估提示词
  │── examples/
  │   └── document_parser/
  │       └── vlm_layout_quality.py         # 评估示例
  └── test/
      └── data/                             # demo相关数据
         ├── layout_qualti_img/
         │     ├── page-0f1dacaa-8917-4ca9-8ca0-fed1987a43da.jpg   # 输入的图片示例
         │     └── page-18d8b4a0-f46b-4042-ba4f-b2e78e6c0844.jpg   # 输入的图片示例
         └── test_layout_quality.jsonl              # 输入的jsonl示例
```

##### 评估提示词
我们的评估效果依赖于精心设计的 Prompt。其核心思想是：

1. Layout布局检测元素列别，我们基于Mineru的输出类型，来设定提示词。
2. 分层错误标签：我们将布局检测问题分为5个大类：检测遗漏错误、检测不准错误、类别错误、阅读顺序错、其他错误。
3. 结构化输出：我们要求 VLM 模型为每张图片生成一个结构化的 JSON 报告，便于后续程序化处理。


#### 输入数据格式

```python
input_data = {
    "input_path": "../../test/data/test_layout_quality.jsonl",
    "dataset": {
        "source": "local",
        "format": "image",
        "field": {
            "id": "id",
            "content": "pred",
            "image": "image_path"
        }
    },
    "executor": {
        "prompt_list": ["PromptLayoutQuality"],
        "result_save": {
            "bad": True,
            "good": True
        }
    },
    "evaluator": {
        "llm_config": {
            "VLMLayoutQuality": {
                "model": "",
                "key": "",
                "api_url": "",
            }
        }
    }
}
```

#### 输出结果格式

```python
# result 是 ModelRes 对象，包含以下字段：
result.type          # 错误问题一级标签: prompt中定义错误类别
result.name          # 错误描述: 错误列别对应的详细错描述
result.error_status  # 错误状态: False 或 True
result.reason        # 评估原因: List[str]
```


## 使用示例

### 基础用法

```python
from dingo.config import InputArgs
from dingo.exec import Executor

if __name__ == '__main__':
    # 准备数据
    input_data = {
        "input_path": "../../test/data/test_layout_quality.jsonl",
        "dataset": {
            "source": "local",
            "format": "image",
            "field": {
                "id": "id",
                "content": "pred",
                "image": "image_path"
            }
        },
        "executor": {
            "prompt_list": ["PromptLayoutQuality"],
            "result_save": {
                "bad": True,
                "good": True
            }
        },
        "evaluator": {
            "llm_config": {
                "VLMLayoutQuality": {
                    "model": "",
                    "key": "",
                    "api_url": "",
                }
            }
        }
    }
    input_args = InputArgs(**input_data)
    executor = Executor.exec_map["local"](input_args)

    # 执行评估
    result = executor.execute()

    # 查看结果
    print(result)
```

### JSONL数据格式

```jsonl
{"id": "page-0f1dacaa-8917-4ca9-8ca0-fed1987a43da", "image_width": 4306, "image_height": 3289, "image_path": "../test/data/layout_qualti_img/page-0f1dacaa-8917-4ca9-8ca0-fed1987a43da.jpg", "original_image": "", "pred_bbox_image": "", "gt_markdown": "", "pred": [{"bbox_id": 1, "bbox": [529.638, 207.207, 1003.298, 289.43199999999996], "type": "header", "content": ""}, {"bbox_id": 2, "bbox": [3285.478, 246.67499999999998, 3763.444, 325.611], "type": "header", "content": ""}, {"bbox_id": 3, "bbox": [3772.056, 565.708, 3853.87, 2065.492], "type": "text", "content": ""}, {"bbox_id": 4, "bbox": [3673.018, 572.286, 3754.832, 1940.51], "type": "text", "content": ""}, {"bbox_id": 5, "bbox": [3578.286, 572.286, 3660.1, 1940.51], "type": "text", "content": ""}, {"bbox_id": 6, "bbox": [3474.942, 572.286, 3556.756, 2680.535], "type": "text", "content": ""}, {"bbox_id": 7, "bbox": [3375.904, 572.286, 3453.4120000000003, 2956.811], "type": "text", "content": ""}, {"bbox_id": 8, "bbox": [3268.254, 572.286, 3345.762, 2368.08], "type": "text", "content": ""}, {"bbox_id": 9, "bbox": [3100.3199999999997, 572.286, 3164.91, 920.9200000000001], "type": "text", "content": ""}, {"bbox_id": 10, "bbox": [2984.058, 572.286, 3065.872, 2825.2509999999997], "type": "text", "content": ""}, {"bbox_id": 11, "bbox": [2846.266, 684.112, 2928.0800000000004, 1243.242], "type": "title", "content": ""}, {"bbox_id": 12, "bbox": [2600.824, 565.708, 2773.064, 2486.484], "type": "text", "content": ""}, {"bbox_id": 13, "bbox": [2501.786, 565.708, 2583.6, 2121.405], "type": "text", "content": ""}, {"bbox_id": 14, "bbox": [2411.36, 565.708, 2488.868, 1897.753], "type": "text", "content": ""}, {"bbox_id": 15, "bbox": [2221.896, 565.708, 2299.404, 2055.625], "type": "text", "content": ""}, {"bbox_id": 16, "bbox": [2015.208, 542.6850000000001, 2088.41, 2154.295], "type": "text", "content": ""}, {"bbox_id": 17, "bbox": [1916.17, 539.3960000000001, 1997.9840000000002, 2032.602], "type": "text", "content": ""}, {"bbox_id": 18, "bbox": [1812.826, 539.3960000000001, 1898.946, 2029.3129999999999], "type": "text", "content": ""}, {"bbox_id": 19, "bbox": [1718.094, 539.3960000000001, 1808.52, 2029.3129999999999], "type": "text", "content": ""}, {"bbox_id": 20, "bbox": [1627.6680000000001, 539.3960000000001, 1709.482, 2029.3129999999999], "type": "text", "content": ""}, {"bbox_id": 21, "bbox": [1532.936, 536.107, 1610.444, 2104.96], "type": "text", "content": ""}, {"bbox_id": 22, "bbox": [1425.286, 536.107, 1511.406, 2279.277], "type": "text", "content": ""}, {"bbox_id": 23, "bbox": [1283.1879999999999, 654.5110000000001, 1365.002, 825.539], "type": "title", "content": ""}, {"bbox_id": 24, "bbox": [1149.702, 437.437, 1227.2099999999998, 2930.4990000000003], "type": "text", "content": ""}, {"bbox_id": 25, "bbox": [1046.358, 404.54699999999997, 1136.784, 2930.4990000000003], "type": "text", "content": ""}, {"bbox_id": 26, "bbox": [947.32, 407.836, 1033.44, 2532.53], "type": "text", "content": ""}, {"bbox_id": 27, "bbox": [861.2, 407.836, 943.014, 2930.4990000000003], "type": "text", "content": ""}, {"bbox_id": 28, "bbox": [757.856, 407.836, 839.6700000000001, 2772.627], "type": "text", "content": ""}, {"bbox_id": 29, "bbox": [632.982, 407.836, 723.408, 1055.769], "type": "text", "content": ""}, {"bbox_id": 30, "bbox": [503.802, 664.378, 589.922, 1151.1499999999999], "type": "title", "content": ""}, {"bbox_id": 31, "bbox": [348.786, 2641.067, 417.682, 2720.0029999999997], "type": "page_number", "content": ""}]}
```


## 最佳实践
### 评估模型
1. 务必使用VLM模型：
此工具的原理是将图片和文本同时输入给模型进行对比评估。因此，必须使用支持多模态输入的 VLM（视觉语言模型），否则模型将无法处理图片输入。
2. 推荐使用高性能VLM：
推荐使用Gemini 2.5 Pro 这样先进的 VLM。更强大的模型在图像理解、空间关系识别和细微错误发现方面表现更出色，能提供更准确、更可靠的评估结果。
3. 对于评估任务，我们建议将temperature调低，如0.1，保证模型能严格按照prompt设定的标准进行评价，且输出可以达到最优的指令跟随效果。

## 完整示例

### 评估示例
参考: `examples/document_parser/vlm_layout_quality.py`

### 测试数据
参考: `test/data/test_layout_quality.jsonl`


## 参考资料

1. [Dingo 文档](https://deepwiki.com/MigoXLab/dingo) - 完整的 API 文档和更多示例
