# Search Result Quality 三指标评测说明

本文档说明 meta search 检索结果的三类评测指标：相关性、内容有效性、权威性，以及对应的单项评测脚本和综合评测脚本。该方案面向无人工 GT 的检索结果质量检查，输入为 query 及其 top-k 检索结果，输出 query 级和 result 级分数，并按阈值生成 Dingo 风格的 good/bad 分类目录。

## 1. 适用场景

该评测用于回答三个业务问题：

| 指标 | 业务问题 | 评测方式 |
|---|---|---|
| 相关性 `relevance` | 检索结果是否回答了用户 query 的真实检索意图 | LLM 逐条判断 query-result 匹配程度 |
| 内容有效性 `effectiveness` | 结果记录本身是否完整、可读、可用于判断论文价值 | 规则检查字段缺失/信息量，RuleSpecialCharacter/RuleInvisibleChar 初筛异常候选，LLM 二次确认 |
| 权威性 `authority` | 结果是否具备学术可信度和来源影响力信号 | 规则检查 citation、influential citation、venue、DOI |

三个指标关注点不同：

- 相关性判断“是不是用户要找的内容”。
- 内容有效性判断“这条结果记录是否有足够信息可读可用”。
- 权威性判断“这条结果是否有论文影响力、来源、DOI 等可信信号”。

例如，用户搜索 `Wallace Chafe`，rank1 返回标题也是 `Wallace Chafe`，相关性可能较好；但如果该结果没有 abstract、keywords、publication venue，则内容有效性会较低。

## 2. 输入格式

输入文件为 JSONL，每行一个 query 及其检索结果。

```json
{"query": "PBPK Review", "results": [{"title": "...", "abstract": "..."}]}
```

脚本支持的 query 字段名：

- `query`
- `query_text`
- `q`

脚本支持的结果列表字段名：

- `results`
- `top_results`
- `top_api_results`
- `search_results`

常用输入路径示例：

```bash
outputs/meta_search_97_query_results.jsonl
```

## 3. 输出文件

综合评测脚本 `sdk_eval_search_result.py` 会在 `--output-dir` 下生成一个时间戳子目录，核心结果都放在该子目录中，例如：

```text
outputs/search_result_eval_97q/20260710_162652_1ac3f3be/
```

默认核心文件如下：

| 文件 | 粒度 | 说明 |
|---|---|---|
| `summary.json` | 全局 | 指标均值、中位数、最小值、最大值、bad/good 数量、阈值、LLM 配置等 |
| `query_scores.csv` | query 级 | 每个 query 的 rank-discount 汇总分、label、eval_status |
| `result_scores.csv` | result 级 | 每个 query 的每条 top-k 结果分数和诊断信息 |
| `all_results.jsonl` | result 级原始明细 | executor 输出的逐条评测结果，保留三个指标的完整 `eval_details` |
| `bad/` | query 级分类 | 低于阈值或运行异常的 query 记录 |
| `good/` | query 级分类 | 使用 `--save-good` 时保存通过的 query 记录 |

`detailed_results.json` 默认不生成；需要完整嵌套诊断时加 `--save-detailed`。

单独运行 `sdk_eval_effectiveness.py`、`sdk_eval_relevancy.py`、`sdk_eval_authority.py` 时，会保留 Dingo executor 的单指标 result 级分类目录，例如 `search_result/Effectiveness/Error_*.jsonl`。

分类 label 示例：

```text
QUALITY_BAD.SEARCH_RESULT_RELEVANCE_LOW
QUALITY_BAD.SEARCH_RESULT_RELEVANCE_PARSE_ERROR
QUALITY_BAD.SEARCH_RESULT_EFFECTIVENESS_LOW
QUALITY_BAD.SEARCH_RESULT_AUTHORITY_LOW
QUALITY_BAD.SEARCH_RESULT_OVERALL_LOW
QUALITY_GOOD.SEARCH_RESULT_RELEVANCE_PASS
QUALITY_GOOD.SEARCH_RESULT_EFFECTIVENESS_PASS
QUALITY_GOOD.SEARCH_RESULT_AUTHORITY_PASS
QUALITY_GOOD.SEARCH_RESULT_OVERALL_PASS
```

单独运行 `sdk_eval_effectiveness.py` 时，`summary.json` 采用类似 `sdk_chunk_eval.py` 的 result 级结构：每个 query 的每条 top-k 检索文献都是一个测试对象，`total`、`num_good`、`num_bad` 和 `score` 都按 result 级计算。`type_ratio.search_result` 中会统计 `Effectiveness.Error_*` 和 `QUALITY_GOOD` 的比例，`metrics_score.search_result` 中会统计 `LLMSearchResultEffectiveness` 的 result 级分数分布。

内容有效性还会额外输出 result 级错误类型文件，例如：

```text
Effectiveness/Error_Title_Miss.jsonl
Effectiveness/Error_Abstract_Miss.jsonl
Effectiveness/Error_Keywords_Miss.jsonl
Effectiveness/Error_Venue_Miss.jsonl
Effectiveness/Error_HTML_Tag.jsonl
Effectiveness/Error_Mojibake.jsonl
Effectiveness/Error_Invisible_Char.jsonl
Effectiveness/Error_Unreadable_Text.jsonl
Effectiveness/Error_Special_Char_Noise.jsonl
Effectiveness/Error_LLM_Quality_Parse.jsonl
QUALITY_GOOD.jsonl
```

只有实际出现的错误类型会生成对应文件。

## 4. Query 级汇总逻辑

三个指标都先对 top-k 中每条 result 打分，然后用 rank-discounted mean 汇总到 query 级。

第 `rank` 条结果的权重为：

```text
weight(rank) = 1 / log2(rank + 1)
```

query 级分数为：

```text
query_score = sum(result_score_i * weight_i) / sum(weight_i)
```

业务含义：

- rank1 的影响最大。
- rank 越靠后，对 query 总分影响越小。
- 适合评估搜索排序质量，因为用户更关注前几条结果。

## 5. 相关性 Relevance

### 5.1 业务逻辑

相关性判断每条检索结果与 query 是否匹配，重点看：

- result 是否直接回答或覆盖 query 意图。
- 标题和摘要是否围绕 query 主题。
- 对短词、人名、论文题名、中文长 query 等非 DOI query，LLM 根据语义进行判断。
- DOI query 使用结构化精确匹配：规范化 query DOI 与结果 `doi`、`unique_id` 或 location DOI，完全一致才算命中。
- DOI 前缀相似、同出版社或主题相似但 DOI 不一致时，result 相关性为 0，不允许 LLM 猜测。

### 5.2 输入字段

| 输入 | 来源 |
|---|---|
| `query` | query 字段 |
| `title` | result 的 `title` 或 `display_name` |
| `abstract` | result 的 `abstract`、`summary` 或 `content` |
| `doi` | DOI query 的精确标识符匹配 |
| `unique_id`、`locations` | result 缺少顶层 DOI 时的标识符补充来源 |

### 5.3 Result 级输出

| 字段 | 说明 |
|---|---|
| `relevance` | result 总相关性分数 |
| `query_relevance` | query 与 result 的语义匹配程度 |
| `result_quality` | result 内容质量辅助判断 |
| `content_issues` | LLM 判断是否存在内容问题 |
| `confidence` | LLM 对评分的置信度 |
| `error` | LLM 输出解析失败等错误 |
| `reasoning` | 简短原因 |

DOI query 不调用 LLM。Result 级完全匹配为 `1.0`，否则为 `0.0`；reason 中记录 expected DOI 和 result DOI。

DOI 的 query 级得分按精确命中的排名折扣：

```text
doi_relevance = max(exact_match / log2(rank + 1))
```

因此 rank1 命中为 `1.0`，rank2 命中为 `0.63093`，没有精确命中为 `0.0`。普通 query 继续使用 top-k rank-discount mean。

### 5.4 Query 级异常

如果某个 query 的任意 rank 出现 LLM JSON 解析失败，会增加：

```text
QUALITY_BAD.SEARCH_RESULT_RELEVANCE_PARSE_ERROR
```

这类 label 表示运行/解析质量告警，不一定代表业务相关性低。分析低相关时建议区分：

- `SEARCH_RESULT_RELEVANCE_LOW`：业务低相关。
- `SEARCH_RESULT_RELEVANCE_PARSE_ERROR`：LLM 输出格式或解析异常。

### 5.5 可调参数

| 参数 | 默认值 | 说明 |
|---|---:|---|
| `--top-k` | 10 | 每个 query 评测前 k 条结果 |
| `--threshold` | 0.15 | query 级 hard bad 阈值 |
| `--llm-max-tokens` | 1024 | LLM 输出最大 token 数 |
| `--llm-workers` | 4 | 并发 LLM 调用数 |
| `--llm-timeout` | 60 | 单次 LLM 请求超时秒数 |
| `--prompt-mode` | `detailed` | prompt 模式 |
| `OPENAI_MODEL` | `gpt-4o` | LLM 模型名，可通过环境变量覆盖 |
| `OPENAI_BASE_URL` | 空 | OpenAI compatible endpoint |
| `OPENAI_TEMPERATURE` | 0.0 | LLM temperature |

## 6. 内容有效性 Effectiveness

### 6.1 业务逻辑

内容有效性判断的是一条检索结果记录是否“可读、完整、可用于用户判断”，不判断它是否与 query 相关。

当前不按 `metadata_type` 做差异化处理。也就是说，`paper`、`ebook`、未来新增类型都用同一套字段完整性标准。这有利于持续观察数据库元数据补全质量：如果 ebook 未来补全 abstract、keywords、venue，有效性分数会自然提升。

### 6.2 字段权重

单条 result 的分数为：

```text
Effectiveness =
  title_score * 0.25
+ abstract_score * 0.45
+ keywords_score * 0.15
+ venue_score * 0.15
```

| 子项 | 权重 | 业务含义 |
|---|---:|---|
| `title_score` | 0.25 | 标题是否存在、长度是否合理、是否可读 |
| `abstract_score` | 0.45 | 摘要是否存在、信息量是否充足、是否可读 |
| `keywords_score` | 0.15 | 关键词是否存在、是否提供主题信息 |
| `venue_score` | 0.15 | 期刊/会议/来源名称是否存在、是否可读 |

字段为空时，该字段直接得 0 分。

示例：如果 result 只有标题，其他字段为空，且 `title_score=0.32948`：

```text
0.32948 * 0.25 + 0 + 0 + 0 = 0.08237
```

### 6.3 字段评分逻辑

每个字段先做基础质量判断：

- 为空：0 分。
- 字段内容异常先由规则筛选，再由 LLM 判断：如果存在 HTML 泄漏、乱码、不可见字符、严重特殊字符噪声等，会按 LLM 字段质量分降低该字段分数。乱码筛选包括 UTF-8 被误按 Latin-1 解码产生的 `Ð...`、`Ñ...` 序列及 C1 控制字符。
- 长度太短：低分。
- 长度和信息量达到要求：接近或等于 1 分。

`keywords` 会把列表中的每个 keyword 视为一个主题信号；空列表计为缺失。

`venue` 读取优先级：

```text
publication_venue_name_unified
publication_venue_name
venue
source
```

### 6.4 Issues 类型

| issue | 含义 |
|---|---|
| `missing_title` | 标题为空 |
| `missing_abstract` | 摘要为空 |
| `missing_keywords` | 关键词为空 |
| `missing_venue` | 期刊/会议/来源名为空 |
| `title:html_tag` / `abstract:html_tag` / `venue:html_tag` | LLM 判断字段中有 HTML/XML 标签泄漏 |
| `*:mojibake` | LLM 判断字段存在乱码或编码错误 |
| `*:invisible_char` | LLM 判断字段存在不可见/控制字符 |
| `*:unreadable_text` | LLM 判断字段整体不可读 |
| `*:special_char_noise` | LLM 判断字段中特殊字符噪声已经影响阅读 |
| `llm_quality_parse_error` | LLM 字段质量判断调用或解析失败 |

注意：

- `RuleSpecialCharacter` 和 `RuleInvisibleChar` 只用于快速召回疑似异常字段，不直接作为最终扣分依据。
- LaTeX、化学符号、单位、希腊字母、`|` 分隔符等正常学术表达不应被 LLM 判为问题。
- HTML 高亮标签、明显 mojibake、不可见字符、严重乱码会由 LLM 输出字段级 issue，并降低对应字段分数。
- 分析 bad 样本时建议结合原始 title、abstract、venue 和 `llm_quality_reason` 进行人工抽查。

### 6.5 可调参数

| 参数 | 默认值 | 说明 |
|---|---:|---|
| `--top-k` | 10 | 每个 query 评测前 k 条结果 |
| `--threshold` | 0.15 | query 级 hard bad 阈值 |
| `--llm-max-tokens` | 1024 | 内容有效性 LLM 字段质量判断的最大 token 数 |
| `--llm-workers` | 4 | 内容有效性 LLM 二次复核并发数 |
| `--llm-timeout` | 60 | LLM 请求超时秒数 |
| `--disable-llm-quality` | false | 关闭 LLM 字段质量判断，仅保留字段缺失/长度规则 |

阈值建议：

- `0.15` 适合作 hard bad，只筛严重不可用结果。
- 如果要发现 metadata 缺失、摘要不足等一般质量问题，可额外关注 `< 0.45` 的 warning 区间。

## 7. 权威性 Authority

### 7.1 业务逻辑

权威性判断检索结果是否具备学术可信度和影响力信号，主要来自：

- 引用数。
- 高影响引用数。
- 期刊/会议/来源类型。
- DOI。

该指标不判断 query 相关性，也不判断内容字段是否完整。它适合作为 overall 的辅助指标，不建议单独用于硬判“结果错误”。

### 7.2 字段权重

单条 result 的权威性分数为：

```text
authority =
  0.45 * citation_score
+ 0.20 * influential_citation_score
+ 0.25 * venue_score
+ 0.10 * doi_score
```

| 子项 | 权重 | 业务含义 |
|---|---:|---|
| `citation_score` | 0.45 | 普通引用影响力 |
| `influential_citation_score` | 0.20 | 高影响引用 |
| `venue_score` | 0.25 | 来源/期刊/会议可信度 |
| `doi_score` | 0.10 | 是否具备 DOI 标识 |

### 7.3 Citation 归一化

引用数使用 log 归一化，避免高引用老论文过度碾压。

```text
citation_score = log(1 + citation_count) / log(1 + 500)

influential_citation_score =
  log(1 + influential_citation_count) / log(1 + 50)
```

分数会被限制在 `[0, 1]`。

### 7.4 Venue 评分

`venue` 读取优先级：

```text
publication_venue_name_unified
publication_venue_name
venue
source
```

当前规则：

| 条件 | `venue_score` | reason |
|---|---:|---|
| venue 名称包含高权威来源提示词 | 0.85 | `high_authority_venue_hint` |
| `publication_venue_type` 是 journal 或 conference | 0.65 | `journal_or_conference` |
| repository 或 preprint | 0.45 | `repository_or_preprint` |
| 未知或低信号来源 | 0.25 | `unknown_or_low_signal_venue` |

高权威来源提示词包括：

```text
nature, science, cell, nejm, lancet, jama,
acm, ieee, springer, elsevier, wiley,
neurips, icml, iclr, cvpr, acl, emnlp, aaai, ijcai, sigir
```

### 7.5 DOI 评分

```text
doi_score = 1.0
```

条件：

- result 有 `doi` 字段；或
- `locations` 中包含 `doi.org`。

否则：

```text
doi_score = 0.0
```

### 7.6 使用注意

权威性对以下 query 类型可能偏保守：

- 人名，例如 `Michael Pecht`、`张文宏`。
- 泛词，例如 `Jerry`、`pam`。
- 书籍、访谈、百科式结果。
- 缺少 citation、DOI、venue 元数据但实际有用的结果。

因此，权威性低不一定表示检索结果不相关，只表示该结果缺少学术权威信号。

## 8. 综合评分 Overall

综合脚本将三个 query 级指标加权：

```text
overall =
  0.7 * relevance
+ 0.2 * effectiveness
+ 0.1 * authority
```

默认权重：

| 指标 | 权重 |
|---|---:|
| `relevance` | 0.7 |
| `effectiveness` | 0.2 |
| `authority` | 0.1 |

业务含义：

- 相关性是核心，因此权重最高。
- 内容有效性次之，保证结果有足够元数据可读。
- 权威性作为辅助，不让 citation/DOI 过度主导搜索体验。

综合评估会同时检查：

- `overall` 是否低于 overall 阈值。
- `relevance` 是否低于相关性阈值。
- 是否存在 LLM 解析错误。
- `effectiveness` 是否低于有效性阈值。
- `authority` 是否低于权威性阈值。

## 9. 使用命令

以下命令均在项目根目录执行。

综合脚本按评测对象拆分分类目录：

```text
<run_dir>/
├── bad/
│   ├── query_level/
│   │   └── QUALITY_BAD/
│   │       ├── SEARCH_RESULT_RELEVANCE_LOW.jsonl
│   │       ├── SEARCH_RESULT_EFFECTIVENESS_LOW.jsonl
│   │       └── SEARCH_RESULT_AUTHORITY_LOW.jsonl
│   └── result_level/
│       ├── Relevance/
│       │   └── Error_Relevance_Low.jsonl
│       ├── Effectiveness/
│       │   ├── Error_Effectiveness_Low.jsonl
│       │   └── Error_HTML_Tag.jsonl
│       └── Authority/
│           ├── Error_Authority_Low.jsonl
│           ├── Error_Citation_Miss.jsonl
│           └── Error_DOI_Miss.jsonl
└── good/                         # 仅使用 --save-good 时生成
    ├── query_level/
    └── result_level/
```

- `query_level`：一个 query 的 top-k 聚合得分及其全部结果。
- `result_level`：每一篇检索文献的原始数据和三个指标明细。
- 同一 result 可以写入多个原因 label 文件；例如 Authority Low 可能同时进入 Citation Miss 和 DOI Miss。

### 9.1 单独跑相关性

```bash
export OPENAI_API_KEY="<your_api_key>"
export OPENAI_BASE_URL="<your_openai_compatible_base_url>"
export OPENAI_MODEL="deepseek-v4-flash"
export OPENAI_TEMPERATURE="0.7"

python examples/retrieval/sdk_eval_relevancy.py \
  --input-jsonl outputs/meta_search_97_query_results.jsonl \
  --output-dir outputs/search_result_relevancy_97q \
  --top-k 10 \
  --threshold 0.15 \
  --llm-max-tokens 1024 \
  --llm-workers 3 \
  --llm-timeout 60 \
  --save-good
```

Windows PowerShell 示例：

```powershell
$env:OPENAI_API_KEY="<your_api_key>"
$env:OPENAI_BASE_URL="<your_openai_compatible_base_url>"
$env:OPENAI_MODEL="deepseek-v4-flash"
$env:OPENAI_TEMPERATURE="0.7"

python examples/retrieval/sdk_eval_relevancy.py `
  --input-jsonl outputs/meta_search_97_query_results.jsonl `
  --output-dir outputs/search_result_relevancy_97q `
  --top-k 10 `
  --threshold 0.15 `
  --llm-max-tokens 1024 `
  --llm-workers 3 `
  --llm-timeout 60 `
  --save-good
```

### 9.2 单独跑内容有效性

```bash
export OPENAI_API_KEY="<your_api_key>"
export OPENAI_BASE_URL="<your_openai_compatible_base_url>"
export OPENAI_MODEL="deepseek-v4-flash"
export OPENAI_TEMPERATURE="0.7"

python examples/retrieval/sdk_eval_effectiveness.py \
  --input-jsonl outputs/meta_search_97_query_results.jsonl \
  --output-dir outputs/search_result_effectiveness_97q \
  --top-k 10 \
  --threshold 0.15 \
  --llm-max-tokens 1024 \
  --llm-workers 8 \
  --llm-timeout 60 \
  --save-good
```

### 9.3 单独跑权威性

```bash
python examples/retrieval/sdk_eval_authority.py \
  --input-jsonl outputs/meta_search_97_query_results.jsonl \
  --output-dir outputs/search_result_authority_97q \
  --top-k 10 \
  --threshold 0.15 \
  --save-good
```

### 9.4 跑综合评分

```bash
export OPENAI_API_KEY="<your_api_key>"
export OPENAI_BASE_URL="<your_openai_compatible_base_url>"
export OPENAI_MODEL="deepseek-v4-flash"

python examples/retrieval/sdk_eval_search_result.py \
  --input-jsonl outputs/meta_search_97_query_results.jsonl \
  --output-dir outputs/search_result_quality_97q \
  --top-k 10 \
  --relevance-threshold 0.15 \
  --effectiveness-threshold 0.15 \
  --authority-threshold 0.15 \
  --overall-threshold 0.15 \
  --llm-max-tokens 1024 \
  --effectiveness-llm-max-tokens 512 \
  --llm-timeout 60 \
  --save-good
```

## 10. 阈值解释

当前默认统一阈值为：

```text
0.15
```

该阈值的含义是 hard bad，即只标记严重问题：

- 相关性几乎不匹配。
- 内容字段严重缺失或不可读。
- 权威信号极弱。

分析建议：

| 分数段 | 建议解释 |
|---|---|
| `< 0.15` | hard bad，优先人工排查 |
| `0.15 - 0.30` | 低分边缘，适合抽样检查 |
| `0.30 - 0.45` | 一般质量问题，尤其适合看 metadata 缺失 |
| `>= 0.45` | 通常可接受，但仍需结合业务 query 类型 |

不同指标的阈值敏感性不同：

- 相关性 `0.15` 适合筛严重错召回；如果要分析一般低相关，可关注 `< 0.30`。
- 内容有效性 `0.15` 很宽松；如果要推动元数据补全，可关注 `< 0.45`。
- 权威性 `0.15` 不宜轻易提高太多，因为很多人名、书籍、访谈、非标准论文结果天然 citation/DOI/venue 信号弱。

## 11. 常见分析方法

### 11.1 查看 query 级低分

```powershell
Import-Csv outputs/search_result_relevancy_97q/query_scores.csv |
  Sort-Object {[double]$_.relevance} |
  Select-Object -First 20 query,relevance,error_count,label
```

### 11.2 查看 result 级有效性 issues

```powershell
Import-Csv outputs/search_result_effectiveness_97q/result_scores.csv |
  Where-Object {$_.issues -ne ""} |
  Select-Object query,rank,title,Effectiveness,issues
```

### 11.3 查看权威性低分原因

```powershell
Import-Csv outputs/search_result_authority_97q/result_scores.csv |
  Sort-Object {[double]$_.authority} |
  Select-Object -First 20 query,rank,title,authority,citation_score,influential_citation_score,venue_score,doi_score,reason
```

### 11.4 区分相关性低分和解析错误

```powershell
Import-Csv outputs/search_result_relevancy_97q/query_scores.csv |
  Where-Object {[double]$_.relevance -lt 0.15} |
  Select-Object query,relevance,error_count,label
```

```powershell
Import-Csv outputs/search_result_relevancy_97q/query_scores.csv |
  Where-Object {[int]$_.error_count -gt 0} |
  Select-Object query,relevance,error_count,label
```

## 12. 相关代码位置

评测器：

- `dingo/model/llm/llm_search_result_relevance.py`
- `dingo/model/llm/llm_search_result_effectiveness.py`
- `dingo/model/llm/llm_search_result_authority.py`

脚本：

- `examples/retrieval/sdk_eval_relevancy.py`
- `examples/retrieval/sdk_eval_effectiveness.py`
- `examples/retrieval/sdk_eval_authority.py`
- `examples/retrieval/sdk_eval_search_result.py`
- `examples/retrieval/search_result_eval_utils.py`

## 13. 已知注意事项

1. 相关性使用 LLM，temperature 大于 0 时，同一批数据重跑可能有轻微分数波动。
2. LLM 相关性结果可能出现 JSON 解析失败，脚本会记录 `SEARCH_RESULT_RELEVANCE_PARSE_ERROR`。
3. 内容有效性当前不按 `metadata_type` 放宽字段要求，因此 ebook 缺少 abstract、keywords、venue 时会低分。
4. 内容有效性使用 `RuleSpecialCharacter` / `RuleInvisibleChar` / `RuleMojibake` 做快速初筛，再用 LLM 二次确认 HTML 泄漏、乱码、不可见字符和严重特殊字符噪声；正常公式、LaTeX、单位符号不应被扣分。
5. 权威性低不一定表示结果不相关，可能只是 citation、DOI、venue 元数据不足。
