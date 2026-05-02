from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import exists, select

import src.db as _db
from src.models import GpuType, Run, RunStatus

_ACTIVE_STATUSES = {RunStatus.queued, RunStatus.provisioning, RunStatus.running}


class RunRepository:
    @staticmethod
    async def get(run_id: uuid.UUID) -> Run | None:
        async with _db.AsyncSessionLocal() as session:
            return await session.get(Run, run_id)

    @staticmethod
    async def get_all(status: RunStatus | None = None) -> list[Run]:
        async with _db.AsyncSessionLocal() as session:
            q = select(Run)
            if status is not None:
                q = q.where(Run.status == status)
            result = await session.execute(q.order_by(Run.created_at.desc()))
            return list(result.scalars().all())

    @staticmethod
    async def get_queued() -> list[tuple[uuid.UUID, GpuType]]:
        async with _db.AsyncSessionLocal() as session:
            result = await session.execute(
                select(Run).where(Run.status == RunStatus.queued)
            )
            runs = result.scalars().all()
            return [(r.id, r.gpu_type_required) for r in runs]

    @staticmethod
    async def exists_active(model_id: str) -> bool:
        async with _db.AsyncSessionLocal() as session:
            stmt = select(
                exists()
                .where(Run.model == model_id)
                .where(Run.status.in_(_ACTIVE_STATUSES))
            )
            result = await session.execute(stmt)
            return result.scalar()

    @staticmethod
    async def create(run: Run) -> Run:
        async with _db.AsyncSessionLocal() as session:
            session.add(run)
            await session.commit()
            await session.refresh(run)
            return run

    @staticmethod
    async def save(run: Run) -> Run:
        async with _db.AsyncSessionLocal() as session:
            run = await session.merge(run)
            await session.commit()
            await session.refresh(run)
            return run

    @staticmethod
    async def set_provisioning(run_id: uuid.UUID) -> None:
        async with _db.AsyncSessionLocal() as session:
            run = await session.get(Run, run_id)
            run.status = RunStatus.provisioning
            await session.commit()

    @staticmethod
    async def set_running(run_id: uuid.UUID, started_at: datetime) -> None:
        async with _db.AsyncSessionLocal() as session:
            run = await session.get(Run, run_id)
            run.status = RunStatus.running
            run.started_at = started_at
            await session.commit()

    @staticmethod
    async def set_failed(
        run_id: uuid.UUID, ended_at: datetime, error_message: str | None = None
    ) -> None:
        async with _db.AsyncSessionLocal() as session:
            run = await session.get(Run, run_id)
            run.status = RunStatus.failed
            run.ended_at = ended_at
            if error_message is not None:
                run.error_message = error_message
            await session.commit()
