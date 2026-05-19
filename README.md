# llm-grill-nightly

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)

Benchmark pipeline for LLM inference servers on **Scaleway GPU**.
Provisions ephemeral GPU VMs, runs [`llm-grill`](https://github.com/fisheatfish/llm-grill) against a curated model list, publishes results to S3.

> This repo is the **orchestrator + infrastructure**. The benchmark engine itself lives in [`llm-grill`](https://github.com/fisheatfish/llm-grill).

---

## How it works

```
push orchestrator/models.yaml
  └─► .github/workflows/bench.yml
        ├─► terraform apply       (creates orchestrator VM on Scaleway)
        ├─► rsync repo + write .env on VM
        ├─► docker compose up     (postgres + migrations + orchestrator API)
        ├─► POST /bench           (queue runs for new/changed models)
        │     └─► per run: terraform apply → GPU VM → llm-grill run → upload to S3
        ├─► poll /bench/status    (wait for active=0)
        ├─► GET /leaderboard      (consolidated JSON → S3)
        └─► terraform destroy     (orchestrator VM, always — even on failure)
```

The orchestrator VM is **ephemeral**: it only exists while a bench is running. GPU VMs are also short-lived (one per model run).

Frontend consumers read `leaderboard.json` directly from S3 — no permanent API.

---

## Stack

| Component       | Tech                                |
|-----------------|-------------------------------------|
| Orchestrator    | FastAPI · Python 3.12 · uv          |
| Database        | PostgreSQL 18 · SQLAlchemy · Alembic |
| Provisioning    | Terraform · Scaleway provider       |
| Object storage  | Scaleway S3 (boto3)                 |
| Runner          | `llm-grill` CLI (vLLM / llama.cpp)  |
| CI              | GitHub Actions                      |

ADRs: [`docs/adr/`](docs/adr/) — see `001-automated-benchmark-site.md` for the full design.

---

## Repository layout

```
orchestrator/        FastAPI service (hexagonal — services/repositories/adapters)
  ├── src/           controllers, routers, services, repositories, infra
  ├── alembic/       database migrations
  ├── models.yaml    curated model list (source of truth for the bench)
  └── tests/

infra/               Terraform — orchestrator VM (single, ephemeral)
terraform/           Terraform — GPU VM template (per-run)
runner/              cloud-init payload running on GPU VMs

scenarios/           llm-grill scenario YAMLs (ramp test, etc.)
docs/adr/            architecture decision records
.github/workflows/   bench.yml (nightly pipeline) · ci.yml (lint + tests)
```

---

## Local development

Requires Docker, [uv](https://docs.astral.sh/uv/), Python 3.12+.

```bash
cp .env.example .env        # fill in API_KEY, HF_TOKEN, SCW_*
make up                     # postgres + migrations + orchestrator on :8000
make logs                   # tail orchestrator logs
make down                   # stop · make down-volumes to wipe DB
```

Run orchestrator tests:

```bash
cd orchestrator
make setup-dev
make test
```

---

## Adding a model to the bench

Edit [`orchestrator/models.yaml`](orchestrator/models.yaml) and open a PR. On merge to `main`, the `bench` workflow runs the new model automatically and republishes the leaderboard.

```yaml
- model: meta-llama/Llama-3.1-8B-Instruct
  engine: vllm           # vllm | llamacpp
  size_b: 8
  scenario: scenarios/ramp.yaml   # optional, defaults to ramp.yaml
```

To re-bench everything: trigger the `bench` workflow manually with `force=true`.

---

## Configuration

All runtime config comes from environment variables. See [`.env.example`](.env.example) for the full list. Highlights:

| Variable                | Purpose                                                  |
|-------------------------|----------------------------------------------------------|
| `API_KEY`               | Bearer token protecting mutating endpoints               |
| `HF_TOKEN`              | HuggingFace token (gated model downloads on GPU VMs)     |
| `SCW_ACCESS_KEY`/`SECRET_KEY` | Scaleway credentials (S3 + Terraform)               |
| `SCW_BUCKET`            | S3 bucket for run artefacts (JSONL + logs)               |
| `GPU_ZONE`              | Scaleway zone for GPU VMs (e.g. `fr-par-2`)              |
| `ORCHESTRATOR_URL`      | Public callback URL used by GPU VMs to report status     |
| `SSH_PUBLIC_KEYS`       | Comma-separated SSH pubkeys injected on GPU VMs (debug)  |
| `RUN_RUNNING_TIMEOUT_MINUTES` | Force-destroy a run stuck longer than this         |

---

## API

OpenAPI/Swagger UI: `http://localhost:8000/docs` once the stack is up.
Key endpoints:

| Method | Path                  | Description                                  |
|--------|-----------------------|----------------------------------------------|
| POST   | `/bench`              | Queue runs for new/changed models            |
| GET    | `/bench/status`       | Active/queued count, ETA                     |
| GET    | `/leaderboard`        | Consolidated results across all completed runs |
| GET    | `/runs/{id}`          | Run state + VM IP                            |
| GET    | `/runs/{id}/logs`     | S3-stored runner logs                        |
| GET    | `/health`             | Liveness probe                               |

All mutating endpoints require `Authorization: Bearer $API_KEY`.

---

## Security

- No long-lived API or public endpoints — orchestrator VM is created and destroyed per bench cycle.
- All secrets injected via environment, never committed (see [`.env.example`](.env.example)).
- Terraform state is local-only by default; configure a remote backend for team setups.
- GPU VMs accept SSH only from keys listed in `SSH_PUBLIC_KEYS`.
- Vulnerability reports: see [SECURITY.md](SECURITY.md).

⚠️ The CI workflow currently sets `admin_cidrs=["0.0.0.0/0"]` to allow GitHub-hosted runners to reach the orchestrator VM. Restrict this if you self-host runners.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Apache 2.0 — see [LICENSE](LICENSE).
