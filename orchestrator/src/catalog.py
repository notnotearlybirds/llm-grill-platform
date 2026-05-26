"""Derive the public model + scenario catalogs published alongside the leaderboard.

The static frontend reads only public JSON from S3; it cannot read models.yaml
or scenarios/*.yaml from the repo. So we derive `models.json` and
`scenarios.json` from those files at bench time and publish them.

Almost everything is derived: `brand` from the HF org, `params_b` from
`size_b`, `quantization` parsed from the GGUF filename, `display_name` cleaned
from the HF id. The one optional editorial field is `categories` — when a
models.yaml entry omits it, we fall back to a heuristic (see `_categories`).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

import yaml
from loguru import logger

if TYPE_CHECKING:
    from src.services.bench_service import ModelEntry

# GGUF quant tag, e.g. Q4_K_M, Q5_K_S, Q8_0, IQ4_XS, BF16, F16 in a filename
# like "Qwen2.5-14B-Instruct-Q4_K_M.gguf".
_QUANT_RE = re.compile(r"(IQ\d+[\w]*|Q\d+(?:_[A-Z0-9]+)*|BF16|F16|F32)", re.IGNORECASE)


def _quantization(gguf_file: str | None) -> str | None:
    if not gguf_file:
        return None
    match = _QUANT_RE.search(Path(gguf_file).stem)
    return match.group(0).upper() if match else None


# Instruct/chat/format suffixes stripped when deriving a human display name.
_NAME_NOISE_RE = re.compile(
    r"-(?:instruct|it|chat|hf|gguf|preview|base|v\d+(?:\.\d+)*)$", re.IGNORECASE
)
_MOE_RE = re.compile(r"mixtral|\bmoe\b|a\d+b|\d+x\d+b", re.IGNORECASE)
_REASONING_RE = re.compile(
    r"qwq|deepseek-?r\d|[-/]r\d\b|\bo\d\b|reasoning", re.IGNORECASE
)


def _display_name(model: str) -> str:
    """Best-effort human name from an HF id: strip org + instruct/format suffixes.

    e.g. "Qwen/Qwen2.5-14B-Instruct" -> "Qwen2.5 14B". Deterministic, not
    hand-curated; an editorial name could override this later if needed.
    """
    name = model.split("/")[-1]
    prev = None
    while prev != name:
        prev = name
        name = _NAME_NOISE_RE.sub("", name)
    return name.replace("-", " ").replace("_", " ").strip()


def _categories(entry: ModelEntry) -> list[str]:
    """Editorial categories if provided, else a heuristic from the model id.

    Architecture tag (Dense default, MoE/Reasoning when matched) plus a
    `Quantized` tag for GGUF/quantized runs. Surfaced as frontend filters.
    """
    if entry.categories is not None:
        return entry.categories
    tags: list[str] = []
    if _MOE_RE.search(entry.model):
        tags.append("MoE")
    if _REASONING_RE.search(entry.model):
        tags.append("Reasoning")
    if not tags:
        tags.append("Dense")
    if _quantization(entry.gguf_file) is not None:
        tags.append("Quantized")
    return tags


def build_models_catalog(entries: list[ModelEntry]) -> list[dict]:
    """One derived metadata row per (model, engine), keyed by the front on `model`."""
    return [
        {
            "model": e.model,
            "engine": e.engine,
            "display_name": _display_name(e.model),
            "brand": e.model.split("/")[0],
            "params_b": e.size_b,
            "quantization": _quantization(e.gguf_file),
            "categories": _categories(e),
            "scenario": e.scenario,
        }
        for e in entries
    ]


def build_scenarios_catalog(root: Path) -> list[dict]:
    """Expose every scenario's load shape (concurrency levels, prompt…).

    Discovers all `scenarios/*.yaml` under `root` so future scenarios surface
    without touching this code, independent of which models reference them.
    The leaderboard's per-model `scenario` path keys back into this catalog.
    """
    scenarios_dir = root / "scenarios"
    if not scenarios_dir.is_dir():
        return []
    catalog: list[dict] = []
    for path in sorted(scenarios_dir.glob("*.yaml")):
        doc = yaml.safe_load(path.read_text())
        if not isinstance(doc, dict):
            # A malformed scenario (top-level list/str/empty) must not break the
            # whole bench submission — skip it and keep publishing the rest.
            logger.warning("Skipping malformed scenario file: {}", path.name)
            continue
        catalog.append(_scenario_summary(f"scenarios/{path.name}", doc))
    return catalog


def _scenario_summary(scenario_path: str, doc: dict) -> dict:
    load = doc.get("load") or {}
    models = doc.get("models") or []
    conversations = doc.get("conversations") or []
    return {
        "path": scenario_path,
        "name": doc.get("name", Path(scenario_path).stem),
        "description": (doc.get("description") or "").strip(),
        "concurrency_levels": load.get("ramp_levels", []),
        "iterations": load.get("iterations"),
        "max_tokens": _first_max_tokens(models),
        "prompt": _first_user_prompt(conversations),
    }


def _first_max_tokens(models: list) -> int | None:
    for model in models:
        if isinstance(model, dict) and "max_tokens" in model:
            return model["max_tokens"]
    return None


def _first_user_prompt(conversations: list[dict]) -> str | None:
    for conv in conversations:
        for turn in conv.get("turns", []):
            if turn.get("role") == "user":
                return turn.get("content")
    return None
