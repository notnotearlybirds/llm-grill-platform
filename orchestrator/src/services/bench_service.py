from typing import Literal

import yaml
from fastapi import HTTPException, status
from huggingface_hub import HfApi
from huggingface_hub.utils import RepositoryNotFoundError
from pydantic import BaseModel, field_validator
from sqlalchemy import exists, select

import src.db as _db
from src.config import settings
from src.models import Engine, Run, RunStatus
from src.schemas import RunCreate
from src.services.run_service import RunService

_ACTIVE_STATUSES = {RunStatus.queued, RunStatus.provisioning, RunStatus.running}

_hf = HfApi()


class ModelEntry(BaseModel):
    model: str
    engine: Literal["vllm", "llamacpp"]
    size_b: int
    scenario: str = "scenarios/basic_8b.yaml"
    gguf_file: str | None = None

    @field_validator("gguf_file")
    @classmethod
    def gguf_required_for_llamacpp(cls, v: str | None, info) -> str | None:
        if info.data.get("engine") == "llamacpp" and not v:
            raise ValueError("gguf_file is required when engine is llamacpp")
        return v


def _load_models() -> list[ModelEntry]:
    with open(settings.models_file) as f:
        raw = yaml.safe_load(f)["models"]
    return [ModelEntry.model_validate(entry) for entry in raw]


def _check_hf_exists(model_id: str) -> None:
    try:
        _hf.model_info(model_id, token=settings.hf_token or None)
    except RepositoryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Model not found on HuggingFace: {model_id}",
        )


async def _has_completed_run(model: str, engine: str) -> bool:
    async with _db.AsyncSessionLocal() as session:
        stmt = select(
            exists().where(
                Run.model == model,
                Run.engine == engine,
                Run.status == RunStatus.done,
            )
        )
        return bool((await session.execute(stmt)).scalar())


async def _has_active_run(model: str, engine: str) -> bool:
    async with _db.AsyncSessionLocal() as session:
        stmt = select(
            exists().where(
                Run.model == model,
                Run.engine == engine,
                Run.status.in_(_ACTIVE_STATUSES),
            )
        )
        return bool((await session.execute(stmt)).scalar())


async def submit(force: bool = False, model_filter: str | None = None) -> dict:
    entries = _load_models()

    if model_filter:
        entries = [e for e in entries if model_filter.lower() in e.model.lower()]
        if not entries:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No model matching '{model_filter}' in models.yaml",
            )

    submitted: list[str] = []
    skipped: list[str] = []

    for entry in entries:
        label = f"{entry.model} [{entry.engine}]"

        if not force and await _has_completed_run(entry.model, entry.engine):
            skipped.append(label)
            continue

        if await _has_active_run(entry.model, entry.engine):
            skipped.append(f"{label} (already active)")
            continue

        _check_hf_exists(entry.model)

        run = await RunService.create(
            RunCreate(
                model=entry.model,
                model_size_b=entry.size_b,
                engine=Engine(entry.engine),
                scenario_path=entry.scenario,
                gguf_file=entry.gguf_file,
            )
        )
        submitted.append(str(run.id))

    return {"submitted": submitted, "skipped": skipped}


async def bench_status() -> dict:
    async with _db.AsyncSessionLocal() as session:
        all_runs = (await session.execute(select(Run))).scalars().all()

    counts: dict[str, int] = {s.value: 0 for s in RunStatus}
    for run in all_runs:
        counts[run.status.value] += 1

    active = sum(counts[s.value] for s in _ACTIVE_STATUSES)
    return {"active": active, "counts": counts}
