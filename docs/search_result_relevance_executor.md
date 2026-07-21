# Search Result Relevance Executor Notes

`examples/retrieval/sdk_eval_relevancy.py` evaluates each query-result pair with `LLMSearchResultRelevance` through Dingo `LocalExecutor`.

## Content Issues

`Relevance.Error_Content_Issues` now uses a strict standard. It is intended for severe visible content corruption, not for ordinary search-result incompleteness.

The LLM prompt asks `content_issues=true` only when the visible title/content has severe problems such as:

- mojibake or garbled text
- raw HTML/XML tag residue
- parser residue that materially hurts readability
- invisible or control characters
- unreadable text

The evaluator also applies a deterministic evidence filter after the LLM response. Even if the LLM returns `content_issues=true`, the final executor label `Relevance.Error_Content_Issues` is emitted only when the result text contains supporting evidence.

The following should not by itself trigger `Relevance.Error_Content_Issues`:

- missing abstract
- short snippet
- truncated preview
- title-only result, if the title is still readable enough to judge relevance

In `EvalDetail.reason`, the output keeps both:

- `raw_content_issues`: the original LLM boolean
- `content_issues`: the post-filtered boolean used for final labels
- `content_issue_evidence`: the matched evidence list

This keeps the LLM signal available for analysis while preventing ordinary truncation or sparse metadata from making an otherwise relevant result bad.

## Test Data

The repository includes `test/data/test_search_result.jsonl` for local smoke tests. It contains three queries and nine results:

| Query | Covered scenario |
|---|---|
| `BiMLP` | Normal academic paper results |
| `海带` | Search-highlight HTML in result metadata |
| `pam` | Sparse ebook results |

With the OpenAI-compatible environment variables configured, run:

For full-dataset evaluation, prefer a low-latency Flash model such as `deepseek-v4-flash`. A Pro model is better reserved for reviewing a small number of ambiguous samples because pointwise relevance evaluation makes approximately `query count x top-k` LLM calls. Keep the model and prompt fixed and use temperature `0` when comparing search versions.

```powershell
$env:OPENAI_MODEL="deepseek-v4-flash"
$env:OPENAI_TEMPERATURE="0"

python examples/retrieval/sdk_eval_relevancy.py `
  --input-jsonl test/data/test_search_result.jsonl `
  --output-dir outputs/search_result_relevancy_smoke `
  --top-k 3 `
  --llm-max-tokens 1024 `
  --threshold 0.15 `
  --save-good
```
