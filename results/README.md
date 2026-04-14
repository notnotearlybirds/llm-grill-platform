# results/

This directory is the source-of-truth store for all benchmark data (see [ADR 001c](../docs/adr/001c-data-storage-jsonl.md)).

## Layout

```
results/
├── YYYY-MM-DD/
│   ├── {org}--{name}/
│   │   ├── vllm.jsonl
│   │   ├── sglang.jsonl
│   │   └── llamacpp.jsonl
│   └── ...
├── aggregated/
│   ├── leaderboard.json
│   ├── history.json
│   └── models/
│       └── {slug}.json
└── fixtures/                  # Synthetic reference data for tests / schema validation
    └── YYYY-MM-DD/
        └── ...
```

## Conventions

### Date directory

`YYYY-MM-DD` — the calendar date on which the nightly benchmark ran.

### Model slug

The HuggingFace model ID `{org}/{name}` is encoded by replacing `/` with `--`:

| HuggingFace ID | Directory name |
|---|---|
| `meta-llama/Llama-3.1-8B-Instruct` | `meta-llama--Llama-3.1-8B-Instruct` |
| `Qwen/Qwen2.5-7B-Instruct` | `Qwen--Qwen2.5-7B-Instruct` |

### Backend file

One JSONL file per backend: `vllm.jsonl`, `sglang.jsonl`, `llamacpp.jsonl`.

Not every model has every backend — if no GGUF quantisation exists, `llamacpp.jsonl` will be absent.

## JSONL format

Each line is a JSON object representing one inference request (a `RequestMetrics` record from `llm_grill.metrics`). Required fields:

| Field | Type | Unit | Description |
|---|---|---|---|
| `scenario` | string | — | Top-level benchmark scenario name |
| `server` | string | — | Backend identifier (`vllm`, `sglang`, `llamacpp`) |
| `model` | string | — | Full HuggingFace model ID (with `/`) |
| `conversation` | string | — | Conversation template name |
| `turn` | integer | — | Turn index within the conversation (0-based) |
| `iteration` | integer | — | Repetition index for this (conversation, turn) |
| `ttft_ms` | float | ms | Time to first token |
| `tpot_ms` | float | ms | Time per output token |
| `e2e_ms` | float | ms | End-to-end latency |
| `prompt_tokens` | integer | tokens | Tokens in the prompt |
| `completion_tokens` | integer | tokens | Tokens generated |
| `tokens_per_second` | float | tok/s | Generation throughput |
| `gpu_utilization` | float | % (0–100) | GPU compute utilisation |
| `gpu_memory_mb` | float | MiB | GPU VRAM used |
| `success` | boolean | — | `false` if the request failed |
| `error` | string\|null | — | Error message when `success=false`, else `null` |
| `run_id` | string | — | `YYYY-MM-DD-{git-sha}` identifying the pipeline run |
| `timestamp` | string | ISO 8601 | UTC timestamp of the individual request |

## Deduplication

**File existence = benchmark already done.**

The pipeline checks whether `results/YYYY-MM-DD/{slug}/{backend}.jsonl` already exists before launching
a benchmark job. If it does, the job is skipped entirely — no need to inspect the file contents.

## Aggregated output

`pipeline/aggregate.py` (Vague 1) reads the raw JSONL files and writes pre-computed JSON to
`results/aggregated/`. The frontend consumes only these aggregated files; it never reads the raw JSONL.

See [`docs/schemas.md`](../docs/schemas.md) for the full schema contract.

## Direct pandas access

Raw files remain human- and pandas-readable without the site:

```python
import pandas as pd
df = pd.read_json(
    "results/fixtures/2026-04-14/meta-llama--Llama-3.1-8B-Instruct/vllm.jsonl",
    lines=True,
)
```
