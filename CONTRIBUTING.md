# Contributing to llm-grill-platform

Architecture, stack, env vars, conventions, test layout: see [CLAUDE.md](CLAUDE.md).

## Setup

```bash
git clone https://github.com/llmgrill/llm-grill-platform.git
cd llm-grill-platform
cp .env.example .env             # fill in secrets
make up                          # postgres + orchestrator (Docker)
cd orchestrator && make setup-dev
```

## Workflow

1. Branch from `main` using a descriptive name:
   - `feat/add-tgi-backend` — new feature
   - `fix/sse-timeout` — bug fix
   - `docs/scenario-examples` — documentation
   - `refactor/client-factory` — refactoring
2. Write code + tests
3. `make lint && make test` in `orchestrator/`.
4. Open a PR against `main` — never push directly to `main`

## Code conventions

- **Hexagonal architecture** — strict naming: `Service` / `Adapter` / `Repository` / `Port`.
- `from __future__ import annotations` in all modules.
- Async everywhere in HTTP I/O (FastAPI + SQLAlchemy async).
- Input validation via Pydantic — no defensive validation inside the core.
- Short classes, single responsibility.
- Logging via `loguru` — no direct `print`.

## Tests

- pytest + pytest-asyncio + pytest-mock + httpx.
- Use **Given / When / Then** structure in docstrings.
- Use `pytest-mock` (`mocker` fixture), not `unittest.mock`.
- Integration tests use `aiosqlite` for an in-memory DB.

## Database migrations

```bash
cd orchestrator
uv run alembic revision --autogenerate -m "describe change"
uv run alembic upgrade head
```

Migrations run automatically via the `migration` service when starting the stack.

## Adding a benchmarked model

Edit `orchestrator/models.yaml` and open a PR. On merge, the `bench` workflow runs it automatically.

## Commits

Use [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`, `ci:`.
