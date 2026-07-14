# Search Result Authority Executor Usage

This document describes the executor-based authority evaluation for meta search results.

## What Changed

`examples/retrieval/sdk_eval_authority.py` evaluates each retrieved result with `LLMSearchResultAuthority` through Dingo `LocalExecutor`.

The standalone authority script evaluates each retrieved result as one test object. The combined script `sdk_eval_search_result.py` still evaluates at query level and applies query-level bad/good thresholds.

`LLMSearchResultAuthority` is rule-based despite being registered as an LLM evaluator. It does not call an external model. The score is based on citation impact, venue/source signals, and DOI availability.

## Flow

1. Read query-level meta search JSONL.
2. Flatten each query's top-k results into result-level JSONL rows.
3. Build `InputArgs`.
4. Run `Executor.exec_map["local"]`.
5. `LLMSearchResultAuthority` returns standard `EvalDetail(metric/status/score/label/reason)`.
6. `LocalExecutor` writes timestamped output, `summary.json`, `search_result/QUALITY_GOOD.jsonl`, and `search_result/Authority/Error_*.jsonl`.

Each flattened input row contains:

| Field | Meaning |
|---|---|
| `query` | Original query text |
| `query_index` | Query order in source JSONL |
| `rank` | Result rank under the query |
| `title` | Result title or display name |
| `search_result` | Full result payload passed to evaluator |

## Test Data

The repository includes `test/data/test_search_result.jsonl` with three queries and nine results. It covers normal papers (`BiMLP`), search-highlight HTML (`海带`), and sparse ebook metadata (`pam`). Authority evaluation is rule-based, so this smoke test does not require an LLM API:

```powershell
python examples/retrieval/sdk_eval_authority.py `
  --input-jsonl test/data/test_search_result.jsonl `
  --output-dir outputs/search_result_authority_smoke `
  --top-k 3 `
  --threshold 0.15 `
  --save-good
```

## Commands

Run authority evaluation:

```powershell
python examples/retrieval/sdk_eval_authority.py `
  --input-jsonl outputs/meta_search_97_query_results.jsonl `
  --output-dir outputs/search_result_authority_97q_executor `
  --top-k 10 `
  --threshold 0.15 `
  --save-good
```

Smoke test with fewer queries:

```powershell
python examples/retrieval/sdk_eval_authority.py `
  --input-jsonl outputs/meta_search_97_query_results.jsonl `
  --output-dir outputs/search_result_authority_smoke `
  --top-k 10 `
  --max-queries 5 `
  --threshold 0.15 `
  --save-good
```

Useful parameters:

| Parameter | Default | Meaning |
|---|---:|---|
| `--top-k` | `10` | Number of results evaluated per query |
| `--max-queries` | `None` | Limit query count for smoke tests |
| `--threshold` | `0.15` | Result-level bad threshold |
| `--max-workers` | `4` | LocalExecutor worker count |
| `--batch-size` | `10` | LocalExecutor batch size |
| `--save-good` | off | Save passing samples |
| `--raw-output` | off | Merge raw data and Dingo result in output JSONL rows |

## Output

The executor creates a timestamped child directory under `--output-dir`, for example:

```text
outputs/search_result_authority_97q_executor/20260709_172501_0f73c631/
```

Main files:

| Path | Meaning |
|---|---|
| `summary.json` | Executor summary |
| `search_result/QUALITY_GOOD.jsonl` | Passing result-level samples, only with `--save-good` |
| `search_result/Authority/Error_*.jsonl` | Bad result-level samples grouped by error type |

`summary.json` uses result-level statistics:

- `total`: number of evaluated retrieved results.
- `num_good`: result count with no error labels.
- `num_bad`: result count with at least one error label.
- `score`: `num_good / total * 100`.
- `metrics_score.search_result.stats.LLMSearchResultAuthority`: result-level authority score distribution.
- `type_ratio.search_result`: label ratios. One result can have multiple error labels, so error ratios can sum to more than the bad ratio.

Error labels:

| Label path | Trigger |
|---|---|
| `search_result/Authority/Error_Authority_Low.jsonl` | Final authority score below threshold |
| `search_result/Authority/Error_Citation_Miss.jsonl` | Authority is low and citation score is zero |
| `search_result/Authority/Error_Venue_Low_Signal.jsonl` | Authority is low and venue/source has only low signal |
| `search_result/Authority/Error_DOI_Miss.jsonl` | Authority is low and no DOI signal is present |

The sub-labels are emitted only when the final authority score is below the threshold. For example, a result without DOI can still be `QUALITY_GOOD` if citation and venue signals are strong enough.

## Scoring

The metric score is:

```text
authority =
  0.45 * citation_score
+ 0.20 * influential_citation_score
+ 0.25 * venue_score
+ 0.10 * doi_score
```

Citation scores use log normalization and are clamped to `[0, 1]`:

```text
citation_score = log1p(citation_count) / log1p(500)
influential_citation_score = log1p(influential_citation_count) / log1p(50)
```

Venue is read from the first available field:

```text
publication_venue_name_unified
publication_venue_name
venue
source
```

Venue scoring:

| Condition | `venue_score` | Reason |
|---|---:|---|
| Venue name contains a high-authority hint | `0.85` | `high_authority_venue_hint` |
| `publication_venue_type` contains journal or conference | `0.65` | `journal_or_conference` |
| `publication_venue_type` contains repository, or venue contains preprint | `0.45` | `repository_or_preprint` |
| Unknown or low-signal source | `0.25` | `unknown_or_low_signal_venue` |

High-authority venue hints include:

```text
nature, science, cell, nejm, lancet, jama,
acm, ieee, springer, elsevier, wiley,
neurips, icml, iclr, cvpr, acl, emnlp, aaai, ijcai, sigir
```

DOI scoring:

```text
doi_score = 1.0
```

when the result has a `doi` field or `locations` contains `doi.org`; otherwise:

```text
doi_score = 0.0
```

Authority does not judge query relevance or content completeness. A low authority score means the result lacks academic trust signals such as citations, venue, or DOI. It does not necessarily mean the result is irrelevant or unusable.
