# ADR 001e: Error Handling & Alerting

**Date:** 2026-03-25
**Status:** Revised 2026-05-12
**Parent:** [ADR 001](001-automated-benchmark-site.md)

---

## Context

The pipeline provisions expensive GPU nodes unattended. Failure modes include:

- Terraform apply fails (quota, API error, region unavailable)
- Backend crashes or hangs (OOM, model incompatibility)
- Terraform destroy fails → **orphaned instances running at ~$3/h each**
- GitHub Actions timeout (180 min)

Without handling, failures go unnoticed and leaked instances accumulate cost silently.

## Decision

**Structured error handling + GitHub notifications + orphan sweep.**

## Design

### Error handling in the orchestrator

Each run executes in a `try/finally` block ensuring `terraform destroy` always runs, even on crash. The orchestrator marks runs as `failed` with an error message — visible via `GET /runs?status=failed`.

The CI step `Fail if any run failed` checks `GET /bench/status` and exits non-zero if `counts.failed > 0`, triggering GitHub Actions email notification.

### Failure taxonomy

| Run status | Meaning | Action |
|------------|---------|--------|
| `done` | Benchmark completed | Results committed |
| `failed` | Any error during provision or benchmark | Logged, CI fails, node destroyed |

### Orphan sweep

A separate workflow (`sweep.yml`) runs:
- After `bench` workflow completes (via `workflow_run`)
- Daily at 8 AM as a safety net

Lists all Scaleway instances named `grill-*` and terminates any older than 2 hours. Exits non-zero if orphans were found.

### Alerting

- **GitHub Actions native**: email on workflow failure (free, zero setup)
- **Optional Slack webhook**: `curl` on `if: failure()` step with link to logs

## Consequences

| | |
|---|---|
| **+** | No silent failures, leaked instances caught within hours, clear failure taxonomy via orchestrator DB |
| **−** | Sweep job needs Scaleway API access (same secrets as pipeline) |
| **Cost of not doing this** | A single leaked H100 running 24h costs ~$72 |
