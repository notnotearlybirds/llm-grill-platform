# Aggregated JSON Schema Contract

This document is the **single source of truth** for the three aggregated JSON files that the frontend
consumes. It is self-sufficient — you do not need to read the raw JSONL files to build the UI.

The files are written by `pipeline/aggregate.py` (Vague 1) and live under `results/aggregated/`.
The frontend build copies them to `static/data/` with no further computation.

---

## Conventions

- All metrics are computed **only over rows where `success = true`** unless stated otherwise.
- Percentile notation: `p95` = 95th percentile.
- Units are listed per field; all latencies are **milliseconds (ms)**.
- `slug` = HuggingFace model ID with `/` replaced by `--`
  (e.g. `meta-llama/Llama-3.1-8B-Instruct` → `meta-llama--Llama-3.1-8B-Instruct`).
- `date` is always `YYYY-MM-DD` (the date directory of the raw JSONL files).

---

## 1. `results/aggregated/leaderboard.json`

One entry per `(model, backend, date)` representing the **latest completed run** for that combination.
Used for the main comparison table.

### Shape

```ts
type Leaderboard = LeaderboardEntry[];
```

### `LeaderboardEntry`

| Field | TypeScript type | Unit | Computation |
|---|---|---|---|
| `model` | `string` | — | HuggingFace model ID (with `/`) |
| `backend` | `string` | — | One of `"vllm"`, `"sglang"`, `"llamacpp"` |
| `date` | `string` | YYYY-MM-DD | Date of the run directory |
| `ttft_mean` | `number` | ms | Arithmetic mean of `ttft_ms` (success only) |
| `ttft_p95` | `number` | ms | 95th percentile of `ttft_ms` (success only) |
| `tpot_mean` | `number` | ms | Arithmetic mean of `tpot_ms` (success only) |
| `e2e_mean` | `number` | ms | Arithmetic mean of `e2e_ms` (success only) |
| `tokens_per_sec` | `number` | tok/s | Arithmetic mean of `tokens_per_second` (success only) |
| `success_rate` | `number` | ratio 0–1 | `count(success=true) / count(all rows)` |
| `n_requests` | `number` | — | Total rows in the JSONL file (success + failures) |

### Example

```json
[
  {
    "model": "meta-llama/Llama-3.1-8B-Instruct",
    "backend": "vllm",
    "date": "2026-04-14",
    "ttft_mean": 87.4,
    "ttft_p95": 112.3,
    "tpot_mean": 15.2,
    "e2e_mean": 312.8,
    "tokens_per_sec": 85.7,
    "success_rate": 1.0,
    "n_requests": 30
  }
]
```

---

## 2. `results/aggregated/models/{slug}.json`

One file per model. Contains the full history of all runs across all backends and dates, broken down
by conversation. Used for the per-model detail page.

### Shape

```ts
type ModelDetail = {
  model: string;
  runs: RunEntry[];
};
```

### `RunEntry`

| Field | TypeScript type | Unit | Computation |
|---|---|---|---|
| `date` | `string` | YYYY-MM-DD | Date of the run directory |
| `backend` | `string` | — | One of `"vllm"`, `"sglang"`, `"llamacpp"` |
| `metrics` | `RunMetrics` | — | Aggregate over **all** conversations in this run |
| `conversations` | `ConversationEntry[]` | — | Per-conversation breakdown |

### `RunMetrics`

| Field | TypeScript type | Unit | Computation |
|---|---|---|---|
| `ttft_mean` | `number` | ms | Mean of `ttft_ms` (success only) |
| `ttft_p95` | `number` | ms | 95th percentile of `ttft_ms` (success only) |
| `tpot_mean` | `number` | ms | Mean of `tpot_ms` (success only) |
| `e2e_mean` | `number` | ms | Mean of `e2e_ms` (success only) |
| `tokens_per_sec` | `number` | tok/s | Mean of `tokens_per_second` (success only) |
| `success_rate` | `number` | ratio 0–1 | `count(success=true) / count(all)` |
| `n_requests` | `number` | — | Total rows |

### `ConversationEntry`

| Field | TypeScript type | Unit | Computation |
|---|---|---|---|
| `name` | `string` | — | Conversation name (`short-qa`, `coding`, `multi-turn`, `long-context`) |
| `metrics` | `RunMetrics` | — | Same fields as `RunMetrics`, filtered to this conversation only |

### Example

```json
{
  "model": "meta-llama/Llama-3.1-8B-Instruct",
  "runs": [
    {
      "date": "2026-04-14",
      "backend": "vllm",
      "metrics": {
        "ttft_mean": 87.4,
        "ttft_p95": 112.3,
        "tpot_mean": 15.2,
        "e2e_mean": 312.8,
        "tokens_per_sec": 85.7,
        "success_rate": 1.0,
        "n_requests": 30
      },
      "conversations": [
        {
          "name": "short-qa",
          "metrics": {
            "ttft_mean": 80.1,
            "ttft_p95": 95.4,
            "tpot_mean": 14.8,
            "e2e_mean": 198.3,
            "tokens_per_sec": 87.2,
            "success_rate": 1.0,
            "n_requests": 5
          }
        },
        {
          "name": "coding",
          "metrics": { "ttft_mean": 91.2, "ttft_p95": 108.0, "tpot_mean": 15.5, "e2e_mean": 378.0, "tokens_per_sec": 84.1, "success_rate": 1.0, "n_requests": 5 }
        },
        {
          "name": "multi-turn",
          "metrics": { "ttft_mean": 88.7, "ttft_p95": 114.2, "tpot_mean": 15.0, "e2e_mean": 290.4, "tokens_per_sec": 86.0, "success_rate": 1.0, "n_requests": 15 }
        },
        {
          "name": "long-context",
          "metrics": { "ttft_mean": 102.3, "ttft_p95": 130.1, "tpot_mean": 16.0, "e2e_mean": 420.0, "tokens_per_sec": 83.5, "success_rate": 1.0, "n_requests": 5 }
        }
      ]
    }
  ]
}
```

---

## 3. `results/aggregated/history.json`

Time series of key metrics for all `(model, backend)` combinations. Used for trend/evolution charts.

### Shape

```ts
type History = {
  series: SeriesEntry[];
};
```

### `SeriesEntry`

| Field | TypeScript type | Unit | Computation |
|---|---|---|---|
| `model` | `string` | — | HuggingFace model ID (with `/`) |
| `backend` | `string` | — | One of `"vllm"`, `"sglang"`, `"llamacpp"` |
| `points` | `HistoryPoint[]` | — | One point per run date, sorted ascending by `date` |

### `HistoryPoint`

| Field | TypeScript type | Unit | Computation |
|---|---|---|---|
| `date` | `string` | YYYY-MM-DD | Date of the run directory |
| `ttft_mean` | `number` | ms | Mean of `ttft_ms` (success only) |
| `tokens_per_sec` | `number` | tok/s | Mean of `tokens_per_second` (success only) |

### Example

```json
{
  "series": [
    {
      "model": "meta-llama/Llama-3.1-8B-Instruct",
      "backend": "vllm",
      "points": [
        { "date": "2026-04-14", "ttft_mean": 87.4, "tokens_per_sec": 85.7 },
        { "date": "2026-04-15", "ttft_mean": 84.1, "tokens_per_sec": 87.0 }
      ]
    },
    {
      "model": "meta-llama/Llama-3.1-8B-Instruct",
      "backend": "sglang",
      "points": [
        { "date": "2026-04-14", "ttft_mean": 75.2, "tokens_per_sec": 91.3 }
      ]
    }
  ]
}
```

---

## Partial backend coverage

Not every model has every backend (e.g. a model without a GGUF quantisation will have no `llamacpp`
entry). The frontend must handle a model being absent from one or more backends gracefully — no
entry in `leaderboard.json`, no corresponding `runs` entry in `models/{slug}.json`, no series in
`history.json`.

---

## Null / missing metrics

If a metric cannot be computed for a run (e.g. all rows are failures), the field value is `null`
rather than omitted. Frontend components should render `null` as `"—"` or similar.
