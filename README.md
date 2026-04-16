# llm-grill-nightly

Nightly benchmark pipeline for [llm-grill](https://github.com/llmgrill/llm-grill). Discovers trending HuggingFace models, benchmarks them on Scaleway H100s via Terraform, aggregates results into JSON consumed by a SvelteKit frontend published on GitHub Pages.

## Architecture

```
HuggingFace Hub ──► Pipeline (GH Actions) ──► Scaleway H100/L40s
                         │
                         ▼
                  results/aggregated/
                         │
                         ▼
               SvelteKit front (GH Pages)
```

The pipeline follows hexagonal architecture — services in `pipeline/application/`, adapters in `pipeline/adapters/`. Architecture decisions are documented in [`docs/adr/`](docs/adr/).

C4 diagrams (LikeC4 DSL) are in [`docs/architecture/`](docs/architecture/).

## Setup

```bash
make install        # Python deps via uv
make install-front  # Node deps (SvelteKit front)
```

## Make commands

| Command | Description |
|---|---|
| `make install` | Install Python dependencies via uv |
| `make install-front` | Install Node dependencies for the frontend |
| `make lint` | Auto-fix and format with ruff |
| `make check` | Check code quality without fixing |
| `make tests` | Run pytest with 80% coverage requirement |
| `make run-dry` | Run pipeline against fixtures (no provisioning) |
| `make run` | Run the full nightly pipeline (provisions H100s) |
| `make aggregate` | Re-aggregate raw JSONL into `results/aggregated/` |
| `make sweep` | Destroy orphan Scaleway instances older than 2h |
| `make front-dev` | Serve the frontend locally |
| `make front-build` | Build the static frontend |

## C4 diagrams

Diagrams are written in [LikeC4](https://likec4.dev) DSL and live in `docs/architecture/`.

```bash
# Install LikeC4 CLI
npm install -g @likec4/cli

# Preview diagrams in browser (live reload)
likec4 serve docs/architecture/

# Export to PNG
likec4 export png docs/architecture/ -o docs/architecture/export/

# Export to single HTML file
likec4 export html docs/architecture/ -o docs/architecture/export/index.html
```

Three views are defined:

| View | Description |
|---|---|
| `system_context` | How llm-grill-nightly fits in the wider ecosystem |
| `containers` | Deployable units: GH Actions, Pipeline, Terraform, H100s, Front, Pages |
| `components` | Pipeline internals — hexagonal architecture: services, ports, adapters |

## Data contract

Output JSON schemas are documented in [`docs/schemas.md`](docs/schemas.md). The three files under `results/aggregated/` are the frontend's only data source.

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `SWEEP_NAME_PREFIX` | `grill-` | Instance name prefix for the orphan sweep |
| `SWEEP_MAX_AGE_HOURS` | `2.0` | Max instance age before considered orphan |
| `HF_TOKEN` | — | HuggingFace token (optional, increases rate limits) |
| `SCW_*` | — | Scaleway credentials (see ADR 001g) |
