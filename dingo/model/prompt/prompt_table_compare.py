from dingo.model.model import Model
from dingo.model.prompt.base import BasePrompt


@Model.prompt_register('TableCompare', [], ['LLMTableCompare'])
class PromptTableCompare(BasePrompt):
    _metric_info = {
        'category': 'Pretrain Text Quality Assessment Metrics',
        'metric_name': 'PromptTableCompare',
        'description': 'Compares the effectiveness of two tools in extracting tables from HTML to Markdown format by evaluating recognition rate and accuracy to determine which tool performs better',
        'paper_title': '',
        'paper_url': '',
        'paper_authors': '',
        'evaluation_results': ''
    }

    # prompt v3
    content = """
你是一位专业的表格识别评估专家,擅长分析 HTML 代码和 Markdown 文本中的表格。现在我会提供三段内容：

1. **裁剪后网页的 HTML 代码**：这是原始网页经过裁剪（去除非必要标签和标签属性）的 HTML 结构。
2. **工具A提取的 Markdown 文本**：这是从 HTML 中提取的、适合大语言模型训练的 Markdown 格式文本。
3. **工具B提取的 Markdown 文本**：这是从 HTML 中提取的、适合大语言模型训练的 Markdown 格式文本。

⚠️ 注意：工具A与工具B的顺序不是固定的，请不要因为顺序而偏好某一工具，最终结论必须严格基于流程2统计的数值差异。

## 评估流程

### 1. 表格数量统计

**原始HTML表格识别：**
- `<table>` 标签
- 表格相关标签：`<thead>` `<tbody>` `<tr>` `<th>` `<td>` 等
- 特定样式表格：`<div class="table">` `<div class="data-table">` 等

**Markdown表格统计：**
- 标准 Markdown 表格格式（使用 `|` 分隔符和 `-` 对齐符）
- 表格必须包含表头分隔行（如 `| --- | --- |`）
- 复杂表格使用原始HTML段落（<table>标签包裹）


### 2. 识别率和准确率统计

统计以下内容：
- N = HTML 中实际表格数量（如果N = 0，直接跳转到 "5. 特殊情况处理"并输出指定内容，不需要进行其他的流程）
- MA, MB = 工具A、B识别的表格数量（在对应Markdown文本中）
- EA, EB = 工具A、B在转化中的错误数量（在对应Markdown文本中）

计算：
- 工具A识别率 = MA / N × 100%
- 工具B识别率 = MB / N × 100%
- 工具A准确率 = (MA − EA) / MA × 100%
- 工具B准确率 = (MB − EB) / MB × 100%

### 3. 量化评估规则

请严格按照以下规则做出决策：
- 如果识别率差异 ≥ 20%：识别率高的工具获胜。
- 如果识别率差异 < 20% 且准确率差异 ≥ 15%：准确率高的工具获胜。
- 如果两项差异都 < 阈值：判定两者相当。


### 原始网页的 HTML 代码如下：

```html
{}

### 工具A提取的 Markdown 文本如下：

```md
{}
```

### 工具B提取的 Markdown 文本如下：

```md
{}
```

### 4. 输出格式（HTML有表格情况，即 N ≠ 0）

请最终只返回一个 JSON，不要有任何额外解释说明
JSON 包含以下字段：
- `score`：如果工具A更好取值1，工具B更好取值2，效果相当取值0
- `name`：固定值 "table"
- `reason`："1）HTML共N个表格；2）工具A统计结果；3）工具B统计结果；4）判定结果。"


示例输出（HTML有表格情况，即 N ≠ 0）：
```json
{{
  "score": [0|1|2],
  "name": "table",
  "reason": "1）HTML共N个表格；2）工具A识别MA个(识别率%)，错误EA个(准确率%)；3）工具B识别MB个(识别率%)，错误EB个(准确率%)；4）最终依据规则，判定..."
}}
```

### 5. 特殊情况处理（HTML无表格情况，即 N = 0）

如果统计到 N = 0，务必直接返回，不得包含额外解释：
```json
{{
  "no_table": true
}}

### 6. 注意事项
如果 HTML 中没有任何表格，请按照特殊情况处理，返回指定内容。

如果HTML有表格，在做出结论前，必须严格完成 ①统计 ②计算 ③规则判定 这三个步骤，不得跳过。

返回结果必须是一个严格符合格式的 JSON，不得包含额外解释！
"""
