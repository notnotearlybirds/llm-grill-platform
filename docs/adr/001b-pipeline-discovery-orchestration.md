# ADR 001b: Pipeline — Model Discovery and Orchestration

**Date:** 2026-03-25
**Status:** Validated
**Parent:** [ADR 001](001-automated-benchmark-site.md)

---

## Context

The pipeline must nightly:
1. Discover new models on HuggingFace.
2. Filter out already-benchmarked models.
3. Orchestrate infra provisioning → benchmark → results commit.

Discovery filters must be configurable (YAML, not hardcoded) to adapt over time.

## Options Considered

| Option | Description | Verdict |
|--------|-------------|---------|
| **A. Python scripts + YAML config + GitHub Actions cron** | `run.py` orchestrator driven by `config.yaml` | **Chosen** |
| B. Airflow / Prefect | DAG manager | Rejected: overkill for a linear pipeline, extra infra to maintain |

## Decision

**Option A**: Python scripts + YAML config + GitHub Actions.

## Design

### Structure

```
pipeline/
├── config.yaml              # Discovery filters, backends, load params
├── conversations.yaml       # Standard benchmark conversations
├── discover.py              # HuggingFace Hub API → eligible models
├── check_existing.py        # Scan results/ → skip already done
├── generate_scenario.py     # Generate YAML scenarios for llm-grill
└── run.py                   # Main orchestrator
```

### Discovery (`discover.py`)

Queries the HuggingFace Hub API with configurable filters from `config.yaml`:
- **Task**: `text-generation`
- **Sort**: `trending` or `lastModified`
- **Max size**: safetensors weight < threshold (e.g. 75 GB for H100 80GB minus KV cache margin)
- **Name patterns**: wildcards (`*instruct*`, `*chat*`)
- **Tags**: include/exclude lists
- **Explicit exclusions**: specific models to skip

GGUF detection: looks for `{model_id}-GGUF` repo or `.gguf` files. If absent, `llamacpp` backend is excluded for that model.

### Deduplication (`check_existing.py`)

Existing JSONL file in `results/` = benchmark already done. Check is per (model, backend) pair. A model is fully covered when all expected backends have a file.

### Conversations (`conversations.yaml`)

4 standard conversations testing different aspects:
- **short-qa**: single-turn, short answer (baseline TTFT)
- **coding**: single-turn code generation (throughput)
- **multi-turn**: 3-turn conversation (KV cache effectiveness)
- **long-context**: ~2K token prompt (stress test)

### Orchestrator (`run.py`)

For each eligible, non-benchmarked model:
1. Determine available backends (exclude `llamacpp` if no GGUF)
2. `terraform apply` → provision machines
3. Run benchmarks in parallel (`asyncio`)
4. `terraform destroy` (always, via `finally`)
5. Commit and push results

### GitHub Actions (`nightly.yml`)

- Cron `0 2 * * *` + `workflow_dispatch` for manual trigger
- Timeout: 180 min
- Secrets: `SCW_ACCESS_KEY`, `SCW_SECRET_KEY`, `HF_TOKEN`

## Consequences

| | |
|---|---|
| **+** | Configurable filters via YAML, simple dedup (file existence), idempotent pipeline, manual trigger for testing |
| **−** | GitHub Actions 6h max timeout limits models per night; runner needs Scaleway + HF secrets |
| **Risks** | HF API rate limits (mitigation: `limit: 50` + caching); model crashes a backend (mitigation: per-benchmark timeout + skip with logging) |
