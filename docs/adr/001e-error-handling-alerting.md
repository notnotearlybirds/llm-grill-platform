# ADR 001e: Error Handling & Alerting

**Date:** 2026-03-25
**Status:** Validated
**Parent:** [ADR 001](001-automated-benchmark-site.md)

---

## Context

The nightly pipeline provisions expensive H100 GPUs unattended. Failure modes include:

- Terraform apply fails (quota, API error, region unavailable)
- Backend crashes or hangs (OOM, model incompatibility)
- Terraform destroy fails → **orphaned instances running at ~$3/h each**
- GitHub Actions timeout (6h max)
- HuggingFace API down or rate-limited

Without handling, failures go unnoticed and leaked instances accumulate cost silently.

## Options Considered

| Option | Description | Verdict |
|--------|-------------|---------|
| **A. Structured error handling + GH Actions notifications + orphan sweep** | Multi-layered: per-model try/finally, sweep cron, notifications | **Chosen** |
| B. Full observability stack (Datadog/Grafana) | Ship logs and metrics to a platform | Rejected: overkill for a once-a-day batch job |
| C. Manual checking | Check GH Actions dashboard each morning | Rejected: silent failures are the highest-cost risk (leaked GPUs) |

## Decision

**Option A**: Structured error handling + GitHub notifications + orphan sweep.

## Design

### Error handling in `run.py`

Each model runs in a `try/finally` block ensuring `terraform destroy` always executes. Benchmarks run via `asyncio.gather(return_exceptions=True)` so one backend failure doesn't block others. Per-backend timeout (default 3600s) kills hung processes.

### Failure classification

| Status | Meaning | Action |
|--------|---------|--------|
| `success` | All backends completed | None |
| `partial` | Some backends failed | Commit successful results, log failures |
| `infra_failed` | Terraform apply failed | Skip model, alert, sweep cleans up |
| `unknown_error` | Unexpected exception | Alert, investigate logs |
| `destroy_failed` | Terraform destroy failed | **Critical**: sweep job must clean up |

### Run summary

`run.py` writes `results/summary.json` at the end with counts (success, partial, failed, destroy failures) and per-model details. Non-zero exit code on any failure.

### Orphan sweep (`sweep.yml` + `pipeline/sweep.py`)

Separate workflow that runs:
- After `Nightly Benchmark` completes (via `workflow_run`)
- Daily at 8 AM as a safety net (via `schedule`)

Lists all Scaleway instances named `grill-*` and terminates any older than 2 hours. Exits non-zero if orphans were found (triggers alert).

### Alerting

- **GitHub Actions native**: email on workflow failure (free, no setup)
- **Optional Slack webhook**: `curl` on `if: failure()` step with link to logs

## Consequences

| | |
|---|---|
| **+** | No silent failures, leaked instances caught within hours, partial results still committed, clear failure taxonomy |
| **−** | Sweep job needs Scaleway API access (same secrets as pipeline); summary file adds minor non-result data to repo |
| **Cost of not doing this** | A single leaked H100 running 24h costs ~$72 |
