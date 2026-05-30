import asyncio
import json

import yaml
from fastapi import HTTPException, status
from huggingface_hub import HfApi
from huggingface_hub.utils import RepositoryNotFoundError
from pydantic import BaseModel, field_validator

from src.catalog import (
    build_engines_catalog,
    build_models_catalog,
    build_scenarios_catalog,
)
from src.config import settings
from src.models import ACTIVE_RUN_STATUSES, Engine
from src.repositories.run_repository import RunRepository
from src.schemas import RunCreate
from src.services.run_service import RunService
from src.storage import (
    head_latest_meta,
    upload_engines_catalog,
    upload_models_catalog,
    upload_scenarios_catalog,
)

_hf = HfApi()


class ModelEntry(BaseModel):
    model: str
    engine: Engine
    size_b: int
    scenario: str = "scenarios/ramp.yaml"
    gguf_file: str | None = None
    # Editorial, optional. Free-form tags surfaced as frontend filters
    # (Reasoning | MoE | Dense | Quantized). When absent, catalog derivation
    # falls back to a heuristic — see catalog._categories.
    categories: list[str] | None = None

    @field_validator("gguf_file")
    @classmethod
    def gguf_required_for_llamacpp(cls, v: str | None, info) -> str | None:
        if info.data.get("engine") == Engine.llamacpp and not v:
            raise ValueError("gguf_file is required when engine is llamacpp")
        return v


def _load_models() -> list[ModelEntry]:
    with open(settings.models_file) as f:
        raw = yaml.safe_load(f)["models"]
    return [ModelEntry.model_validate(entry) for entry in raw]


def _filter_entries(
    entries: list[ModelEntry], model_filter: str | None
) -> list[ModelEntry]:
    """Restrict entries to those whose id contains `model_filter` (case-insensitive).

    Shared by `submit` and `pending_run_count` so the bench selection criteria
    can't drift between the CI preflight and the real submit path.
    """
    if not model_filter:
        return entries
    needle = model_filter.lower()
    return [e for e in entries if needle in e.model.lower()]


async def _check_hf_exists(model_id: str) -> None:
    try:
        await asyncio.to_thread(
            _hf.model_info, model_id, token=settings.hf_token or None
        )
    except RepositoryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Model not found on HuggingFace: {model_id}",
        )


async def _publish_catalogs(entries: list[ModelEntry]) -> None:
    """Publish derived models.json + scenarios.json for the static frontend.

    Derived from the full model list (ignores any `model_filter`) so the
    catalogs always describe every benchmarked model, not just the subset
    submitted this call.
    """
    await upload_models_catalog(json.dumps(build_models_catalog(entries)))
    await upload_scenarios_catalog(
        json.dumps(build_scenarios_catalog(settings.scenarios_root))
    )
    await upload_engines_catalog(json.dumps(build_engines_catalog()))


async def publish_catalogs() -> None:
    """Derive + publish models.json and scenarios.json to S3, no benchmarking.

    Entry point for the lightweight `publish-catalogs` CI job: catalogs are pure
    functions of models.yaml / scenarios/*.yaml, so they refresh without a VM.
    """
    await _publish_catalogs(_load_models())


async def pending_run_count(force: bool, model_filter: str | None) -> int:
    """How many (model, engine) entries would actually be benched.

    Mirrors `submit`'s S3 dedup without touching the DB, so CI can decide
    whether provisioning a VM is worth it. `force` counts everything.
    """
    entries = _filter_entries(_load_models(), model_filter)
    if force:
        return len(entries)
    flags = await asyncio.gather(
        *(head_latest_meta(e.model, e.engine) for e in entries)
    )
    return sum(1 for has_meta in flags if not has_meta)


async def submit(force: bool = False, model_filter: str | None = None) -> dict:
    all_entries = _load_models()
    await _publish_catalogs(all_entries)

    entries = _filter_entries(all_entries, model_filter)
    if model_filter and not entries:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No model matching '{model_filter}' in models.yaml",
        )

    submitted: list[str] = []
    skipped: list[str] = []

    for entry in entries:
        label = f"{entry.model} [{entry.engine}]"

        if not force and await head_latest_meta(entry.model, entry.engine):
            skipped.append(label)
            continue

        if await RunRepository.has_active_run(entry.model, entry.engine):
            skipped.append(f"{label} (already active)")
            continue

        await _check_hf_exists(entry.model)

        run = await RunService.create(
            RunCreate(
                model=entry.model,
                model_size_b=entry.size_b,
                engine=entry.engine,
                scenario_path=entry.scenario,
                gguf_file=entry.gguf_file,
            )
        )
        submitted.append(str(run.id))

    return {"submitted": submitted, "skipped": skipped}


async def bench_status() -> dict:
    counts = await RunRepository.count_by_status()
    active = sum(counts[s.value] for s in ACTIVE_RUN_STATUSES)
    return {"active": active, "counts": counts}
