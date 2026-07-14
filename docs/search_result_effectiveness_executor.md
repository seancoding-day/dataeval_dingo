# Search Result Effectiveness Executor Usage

This document describes the executor-based effectiveness evaluation for meta search results.

## What Changed

`examples/retrieval/sdk_eval_effectiveness.py` reuses Dingo `LocalExecutor`. It no longer hand-builds chunk-style `summary.json` or bad/good folders.

The standalone effectiveness script evaluates each retrieved result as one test object. The combined script `sdk_eval_search_result.py` still evaluates at query level and applies query-level bad/good thresholds.

## Flow

1. Read query-level meta search JSONL.
2. Flatten each query's top-k results into result-level JSONL rows.
3. Build `InputArgs`.
4. Run `Executor.exec_map["local"]`.
5. `LLMSearchResultEffectiveness` returns standard `EvalDetail(metric/status/score/label/reason)`.
6. `LocalExecutor` writes timestamped output, `summary.json`, `search_result/QUALITY_GOOD.jsonl`, and `search_result/Effectiveness/Error_*.jsonl`.

Each flattened input row contains:

| Field | Meaning |
|---|---|
| `query` | Original query text |
| `query_index` | Query order in source JSONL |
| `rank` | Result rank under the query |
| `title` | Result title or display name |
| `search_result` | Full result payload passed to evaluator |

## Commands

Fast rule-only run:

```powershell
python examples/retrieval/sdk_eval_effectiveness.py `
  --input-jsonl outputs/meta_search_97_query_results.jsonl `
  --output-dir outputs/search_result_effectiveness_97q_executor `
  --top-k 10 `
  --threshold 0.15 `
  --disable-llm-quality `
  --save-good
```

Run with LLM second judgment for abnormal-character candidates:

```powershell
$env:OPENAI_API_KEY="..."
$env:OPENAI_BASE_URL="http://35.220.164.252:3888/v1/"
$env:OPENAI_MODEL="deepseek-v4-flash"
$env:OPENAI_TEMPERATURE="0.7"

python examples/retrieval/sdk_eval_effectiveness.py `
  --input-jsonl outputs/meta_search_97_query_results.jsonl `
  --output-dir outputs/search_result_effectiveness_97q_executor_llm `
  --top-k 10 `
  --threshold 0.15 `
  --llm-max-tokens 512 `
  --llm-workers 4 `
  --save-good
```

Useful parameters:

| Parameter | Default | Meaning |
|---|---:|---|
| `--top-k` | `10` | Number of results evaluated per query |
| `--max-queries` | `None` | Limit query count for smoke tests |
| `--threshold` | `0.15` | Result-level bad threshold |
| `--save-good` | off | Save passing samples |
| `--disable-llm-quality` | off | Skip LLM second judgment and use deterministic rules only |
| `--llm-max-tokens` | `512` | Max tokens for LLM second judgment |
| `--llm-workers` | `4` | LocalExecutor worker count |
| `--batch-size` | `10` | LocalExecutor batch size |
| `--raw-output` | off | Merge raw data and Dingo result in output JSONL rows |

## Output

The executor creates a timestamped child directory under `--output-dir`, for example:

```text
outputs/search_result_effectiveness_97q_executor/20260709_172501_0f73c631/
```

Main files:

| Path | Meaning |
|---|---|
| `summary.json` | Executor summary |
| `search_result/QUALITY_GOOD.jsonl` | Passing result-level samples, only with `--save-good` |
| `search_result/Effectiveness/Error_*.jsonl` | Bad result-level samples grouped by error type |

`summary.json` uses result-level statistics:

- `total`: number of evaluated retrieved results.
- `num_good`: result count with no error labels.
- `num_bad`: result count with at least one error label.
- `score`: `num_good / total * 100`.
- `metrics_score.search_result.stats.LLMSearchResultEffectiveness`: result-level effectiveness score distribution.
- `type_ratio.search_result`: label ratios. One result can have multiple error labels, so error ratios can sum to more than the bad ratio.

Error labels:

| Label path | Trigger |
|---|---|
| `search_result/Effectiveness/Error_Title_Miss.jsonl` | Missing title |
| `search_result/Effectiveness/Error_Abstract_Miss.jsonl` | Missing abstract |
| `search_result/Effectiveness/Error_Keywords_Miss.jsonl` | Missing keywords |
| `search_result/Effectiveness/Error_Venue_Miss.jsonl` | Missing publication venue/source |
| `search_result/Effectiveness/Error_HTML_Tag.jsonl` | LLM-confirmed HTML tag pollution |
| `search_result/Effectiveness/Error_Mojibake.jsonl` | LLM-confirmed mojibake |
| `search_result/Effectiveness/Error_Invisible_Char.jsonl` | LLM-confirmed invisible characters |
| `search_result/Effectiveness/Error_Unreadable_Text.jsonl` | LLM-confirmed unreadable text |
| `search_result/Effectiveness/Error_Special_Char_Noise.jsonl` | LLM-confirmed special-character noise |
| `search_result/Effectiveness/Error_Effectiveness_Low.jsonl` | Final effectiveness score below threshold |

`RuleSpecialCharacter` and `RuleInvisibleChar` are treated as candidate triggers. If LLM confirms a concrete issue, for example `title:html_tag`, the final label keeps only the concrete business label such as `Effectiveness.Error_HTML_Tag` and suppresses the intermediate rule label. The original rule issue is still retained in `EvalDetail.reason` for traceability.

## Scoring

The metric score is unchanged:

```text
Effectiveness =
  title_score * 0.25
+ abstract_score * 0.45
+ keywords_score * 0.15
+ venue_score * 0.15
```

Field scores are based on missing-field checks, length/information-density checks, and abnormal-character handling. `RuleSpecialCharacter` and `RuleInvisibleChar` are fast candidates. When LLM quality judgment is enabled, those candidates are penalized only after LLM confirmation.

