# llm-grill.fr — Static SvelteKit Site

Nightly LLM benchmark leaderboard for open-source models.

## Development

```bash
npm install
npm run dev
```

The dev server starts at `http://localhost:5173`.

Data is loaded from `static/data/`. If `results/aggregated/leaderboard.json` exists (real pipeline data), it is used. Otherwise the fixtures in `static/data/fixtures/` are copied automatically — so development works without real benchmark data.

## Build

```bash
npm run build
```

Output goes to `build/`. Served via GitHub Pages at `llm-grill.fr`.

## Fixtures

`static/data/fixtures/` contains hand-crafted JSON matching `docs/schemas.md`:
- `leaderboard.json` — 3 entries (2 models × 2 backends, Qwen without llamacpp)
- `models/meta-llama--Llama-3.1-8B-Instruct.json` — 2 dates × 2 backends
- `models/Qwen--Qwen2.5-7B-Instruct.json` — 2 dates × 1 backend
- `history.json` — time series for 3 (model, backend) pairs
