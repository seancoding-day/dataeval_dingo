# Advanced Configuration

## Model Selection

| Model | Speed | Quality | Cost | Notes |
|-------|-------|---------|------|-------|
| `gpt-4o-mini` | Fast | Good | Low | Default, recommended for most articles |
| `gpt-4o` | Medium | High | Medium | Better accuracy for complex claims |
| `gpt-4` | Slow | High | High | Most thorough verification |
| Custom endpoint | Varies | Varies | Varies | Set via OPENAI_BASE_URL |

Override model: `--model gpt-4o` or `export OPENAI_MODEL=gpt-4o`

## Claim Types

ArticleFactChecker recognizes 8 claim types:

| Type | Description | Example |
|------|-------------|---------|
| `factual` | General factual statements | "Python was created in 1991" |
| `statistical` | Numbers, percentages, metrics | "GPT-4 achieves 86.4% on MMLU" |
| `attribution` | Who said/did what | "Elon Musk announced..." |
| `institutional` | Organization affiliations | "Released by Tsinghua University" |
| `temporal` | Dates and timelines | "Launched on December 5, 2024" |
| `comparative` | Comparisons between entities | "Faster than GPT-3.5" |
| `monetary` | Financial figures | "Raised $100M in Series B" |
| `technical` | Technical specs and capabilities | "Supports 128K context window" |

## Tuning Parameters

### `--max-claims N` (default: 50)

Controls how many claims are extracted from the article.

- **10-20**: Quick scan, good for short articles or demos
- **30-50**: Standard, covers most article claims
- **50+**: Thorough, may increase execution time significantly

### `--max-concurrent N` (default: 5)

Controls parallel claim verification.

- **1-3**: Conservative, avoids API rate limits
- **5**: Default balance of speed and reliability
- **10**: Fast but may hit rate limits on some APIs

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | API key for LLM calls |
| `OPENAI_BASE_URL` | No | `https://api.openai.com/v1` | Custom API endpoint |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | Default model |
| `TAVILY_API_KEY` | No | - | Enables web search verification |

## Output Artifacts

Dingo saves detailed output to `outputs/<timestamp>/`:

| File | Content |
|------|---------|
| `summary.json` | Overall evaluation statistics |
| `content/QUALITY_BAD_*.jsonl` | Per-item results grouped by error type |

ArticleFactChecker also saves intermediate artifacts:

| File | Content |
|------|---------|
| `article_content.md` | Original article text |
| `claims_extracted.jsonl` | Extracted claims (one per line) |
| `claims_verification.jsonl` | Per-claim verification details |
| `verification_report.json` | Full structured verification report |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Dingo SDK not installed" | `pip install -e .` from project root |
| "LangChain not installed" | `pip install -r requirements/agent.txt` |
| Timeout errors | Use `--model gpt-4o-mini` and `--max-claims 20` |
| Rate limit errors | Reduce `--max-concurrent` to 2-3 |
| Empty results | Check that article has verifiable factual claims |
