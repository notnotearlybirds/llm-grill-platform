# ADR 001g: Security & Secrets Management

**Date:** 2026-03-25
**Status:** Proposed
**Parent:** [ADR 001](001-automated-benchmark-site.md)

---

## Context

The pipeline requires sensitive credentials:

| Secret | Used by | Risk if leaked |
|--------|---------|---------------|
| `SCW_ACCESS_KEY` / `SCW_SECRET_KEY` | Terraform | Attacker provisions unlimited GPU instances (~$3/h each) |
| `HF_TOKEN` | `discover.py`, model downloads | API abuse under our identity |
| `GITHUB_TOKEN` | Git push, GitHub Pages deploy | Repo write access |
| `SLACK_WEBHOOK_URL` | Failure notifications | Spam the Slack channel |

Long-lived API keys stored as GitHub Actions secrets work but have risks: no expiration, no usage audit trail, broad permissions.

## Options Considered

| Option | Description | Verdict |
|--------|-------------|---------|
| **A. GH Actions secrets + scoped Scaleway IAM + OIDC** | Least-privilege keys, dedicated IAM app | **Chosen** |
| B. HashiCorp Vault | Centralized secrets with dynamic credentials | Rejected: significant infra overhead for 4 secrets |
| C. Personal API keys | Use a team member's credentials | Rejected: no separation of concerns, full account access |

## Decision

**Option A**: GitHub Actions secrets with scoped credentials and least-privilege IAM.

## Design

### Scaleway IAM

Dedicated IAM application `llm-grill-nightly` scoped to:
- A single Scaleway Project (not the whole Organization)
- Instance management permissions only (no storage, no billing)
- Project-level quota: max 5 H100 instances (prevents runaway provisioning)

### HuggingFace token

Read-only, fine-grained: `read-repos` on public models only. No write or organization access.

### GitHub token

Built-in `GITHUB_TOKEN` (auto-scoped to repo, rotated per workflow run). Permissions: `contents: write`, `pages: write`.

### Rotation

| Secret | Frequency | Method |
|--------|-----------|--------|
| Scaleway keys | 90 days | Regenerate in IAM → update GH secret |
| HF token | 90 days | Regenerate in HF settings → update GH secret |
| `GITHUB_TOKEN` | Automatic | Rotated per workflow run |
| Slack webhook | On compromise | Regenerate in Slack app settings |

### Security practices

- Never log secrets (no `echo $SECRET` or `set -x` in sensitive steps)
- Terraform state: local only, ephemeral (destroyed with runner)
- Model downloads: on ephemeral instances, destroyed after use
- Inference port 8000 exposed briefly on short-lived instances; optional security group to restrict to GH Actions IPs

### Incident response

1. Immediately revoke compromised credential at the provider
2. Run `sweep.py` (ADR 001e) to destroy unauthorized instances
3. Check Scaleway billing for unexpected charges
4. Generate new credentials, update GitHub secrets
5. Review GH Actions logs for unauthorized runs

## Consequences

| | |
|---|---|
| **+** | Least-privilege limits blast radius, quota cap prevents runaway GPU costs, no extra infra (no Vault), built-in `GITHUB_TOKEN` eliminates one long-lived secret |
| **−** | Manual rotation (acceptable at 90-day cadence), one-time Scaleway IAM setup, no dynamic/short-lived Scaleway credentials (OIDC not supported there yet) |
