import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status

import src.db as _db
from src.aggregation import aggregate
from src.models import GpuType, Run, RunStatus
from src.repositories.run_repository import RunRepository
from src.schemas import RunCreate
from src.storage import upload_results

_L40S_THRESHOLD_B = 26


class RunService:
    @staticmethod
    async def get(run_id: uuid.UUID) -> Run | None:
        return await RunRepository.get(run_id)

    @staticmethod
    async def list_all(status: RunStatus | None = None) -> list[Run]:
        return await RunRepository.get_all(status)

    @staticmethod
    def select_gpu(model_size_b: int) -> GpuType:
        if model_size_b < _L40S_THRESHOLD_B:
            return GpuType.L40S
        return GpuType.H100

    @staticmethod
    async def create(body: RunCreate) -> Run:
        run = Run(
            **body.model_dump(),
            gpu_type_required=RunService.select_gpu(body.model_size_b),
        )
        async with _db.AsyncSessionLocal() as session:
            session.add(run)
            await session.commit()
            await session.refresh(run)
            return run

    @staticmethod
    async def complete(run_id: uuid.UUID, results_jsonl: str) -> Run:
        async with _db.AsyncSessionLocal() as session:
            run = await session.get(Run, run_id)
            if run is None:
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="run not found")
            if run.status != RunStatus.running:
                raise HTTPException(
                    status.HTTP_409_CONFLICT, detail="run is not running"
                )
            result = aggregate(results_jsonl, run)
            run.status = RunStatus.done
            run.ended_at = datetime.now(timezone.utc)
            session.add(result)
            await session.commit()
            await session.refresh(run)

        results_url = await upload_results(run_id, results_jsonl)
        async with _db.AsyncSessionLocal() as session:
            run = await session.get(Run, run_id)
            if run is None:
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="run not found")
            run.results_url = results_url
            await session.commit()
            await session.refresh(run)
        return run

    @staticmethod
    async def fail(run_id: uuid.UUID, error_message: str) -> Run:
        async with _db.AsyncSessionLocal() as session:
            run = await session.get(Run, run_id)
            if run is None:
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="run not found")
            if run.status not in {RunStatus.running, RunStatus.provisioning}:
                raise HTTPException(
                    status.HTTP_409_CONFLICT, detail="run cannot be failed"
                )
            run.status = RunStatus.failed
            run.error_message = error_message
            run.ended_at = datetime.now(timezone.utc)
            await session.commit()
            await session.refresh(run)
            return run
