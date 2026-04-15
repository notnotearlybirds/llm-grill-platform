# ADR 001f: Aggregation Strategy — Single Source of Truth

**Date:** 2026-03-25
**Status:** Validated
**Parent:** [ADR 001](001-automated-benchmark-site.md)

---

## Context

ADR 001c and 001d both flag the same issue: aggregation logic (percentiles, success filtering, tokens/s) would be duplicated between Python (`llm_grill/metrics.py`) and JavaScript (`site/scripts/build-data.js`). This creates a divergence risk — the site and CLI could show different numbers for the same data.

## Options Considered

| Option | Description | Verdict |
|--------|-------------|---------|
| **A. Python pre-aggregation in the pipeline** | `aggregate.py` writes JSON; site just copies it | **Chosen** |
| B. Keep both, add cross-validation tests | Two implementations + test harness | Rejected: more work than one implementation, tests can drift too |
| C. Shared WASM module | Compile aggregation to WASM for both runtimes | Rejected: massive over-engineering for percentile math |

## Decision

**Option A**: Single Python aggregation step. The site consumes pre-built JSON.

## Design

### `pipeline/aggregate.py`

Runs after benchmarks are committed. Reads `results/**/*.jsonl`, reuses `llm_grill.metrics.aggregate()`, and writes:

| Output | Content |
|--------|---------|
| `results/aggregated/leaderboard.json` | Latest run per (model, backend) with mean/p95 TTFT, tokens/s, success rate |
| `results/aggregated/models/{slug}.json` | All runs for a model across all backends and dates |
| `results/aggregated/history.json` | Time series for performance evolution charts |

### Updated flow

```
run.py → benchmarks → commit JSONL
aggregate.py → commit aggregated JSON
site build: copies results/aggregated/ → static/data/ (no computation)
```

### Aggregated files are committed

Trade-off: slightly larger repo (~50 KB total), but the site build needs no JSONL parsing, and aggregated data is versioned and auditable.

## Consequences

| | |
|---|---|
| **+** | Single source of truth (`llm_grill/metrics.py`), no JS aggregation to maintain, site build is a simple copy, CLI and site always agree |
| **−** | Extra pipeline step (fast — seconds). Changing aggregation logic requires re-running on historical data (one-time migration) |
