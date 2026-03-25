# ADR 001a: Infrastructure — Terraform + Scaleway H100

**Date:** 2026-03-25
**Status:** Proposed
**Parent:** [ADR 001](001-automated-benchmark-site.md)

---

## Context

The nightly pipeline needs H100 GPU instances to run benchmarks. Requirements:

- Provisioned on demand (no permanent infra).
- Full SSH access (for `nvidia-smi`, GPU monitoring).
- 3 backends in parallel to minimize per-model wall time.

## Options Considered

| Option | Description | Verdict |
|--------|-------------|---------|
| **A. Terraform + Scaleway, 3 parallel instances** | 1 H100 per backend, Terraform manages lifecycle | **Chosen** |
| B. Single sequential instance | Backends run one after another | Rejected: 3× slower (~45 min vs ~15 min), same total cost |
| C. Scaleway Python SDK (no Terraform) | Provision from `run.py` directly | Rejected: Terraform is declarative, handles failure cleanup better, infra is versionable |

## Decision

**Option A**: 3 parallel H100 instances via Terraform + Scaleway.

## Design

**Structure**: `infra/` contains `main.tf`, `variables.tf`, `outputs.tf` and per-backend bash setup scripts (`setup-vllm.sh`, `setup-sglang.sh`, `setup-llamacpp.sh`).

**Provisioning**: Terraform creates N `H100-1-80G` instances via `for_each` on the backends list. Each instance gets a cloud-init that installs CUDA, Python, `llm-grill`, the relevant backend, and downloads the model from HuggingFace.

**GGUF handling**: if a model has no GGUF variant on HuggingFace, `discover.py` excludes `llamacpp` → only 2 instances are created.

**Cleanup**: `terraform destroy` is always called, even on error (`try/finally` in `run.py`). Global 60 min timeout per model. Instances have no persistent volumes — fully ephemeral.

## Consequences

| | |
|---|---|
| **+** | 3× faster than sequential, full backend isolation, infra as code, guaranteed cleanup |
| **−** | 3 instances consume Scaleway quota faster; model downloaded 3× (acceptable — HF downloads are fast on Scaleway) |
| **Cost** | ~$2/model (3 machines × ~15 min × H100 spot price) = same as sequential |
