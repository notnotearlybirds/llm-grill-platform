import asyncio
import logging
import re
from datetime import datetime, timedelta, timezone

from huggingface_hub import list_models
from huggingface_hub.hf_api import ModelInfo

from src.config import settings
from src.models import Engine, RunStatus
from src.repositories.run_repository import RunRepository
from src.schemas import RunCreate
from src.services.run_service import RunService

logger = logging.getLogger(__name__)

_SIZE_RE = re.compile(r"(\d+\.?\d*)[Bb]")


async def watching_loop() -> None:
    while True:
        try:
            await _scan_and_enqueue()
        except Exception:
            logger.exception("watcher scan failed")
        await asyncio.sleep(settings.hf_watch_interval_seconds)


async def _scan_and_enqueue() -> None:
    logger.info("watcher: scanning HuggingFace Hub")
    enqueued = 0
    since = datetime.now(timezone.utc) - timedelta(
        seconds=settings.hf_watch_interval_seconds
    )
    num_parameters = f"min:{settings.hf_min_size_b}B,max:{settings.hf_max_size_b}B"
    for model_info in list_models(
        pipeline_tag="text-generation",
        sort="created_at",
        num_parameters=num_parameters,
    ):
        if model_info.created_at and model_info.created_at < since:
            break
        if not _passes_filter(model_info):
            continue
        size_b = _extract_size_b(model_info)
        if size_b is None:
            continue
        if await RunRepository.exists_active(model_info.id):
            continue
        engine = _detect_engine(model_info.id)
        await RunService.create(
            RunCreate(
                model=model_info.id,
                model_size_b=size_b,
                engine=engine,
                scenario_path=settings.hf_default_scenario,
            )
        )
        enqueued += 1
        logger.info("watcher: queued %s (%dB, %s)", model_info.id, size_b, engine.value)
    logger.info("watcher: scan done, %d new runs queued", enqueued)


def _extract_size_b(model_info: ModelInfo) -> int | None:
    match = _SIZE_RE.search(model_info.id)
    if match:
        return round(float(match.group(1)))
    return None


def _detect_engine(model_id: str) -> Engine:
    if "gguf" in model_id.lower():
        return Engine.llamacpp
    return Engine.vllm


def _passes_filter(model_info: ModelInfo) -> bool:
    if not settings.hf_watched_orgs:
        return True
    org = model_info.id.split("/")[0]
    return org in settings.hf_watched_orgs
