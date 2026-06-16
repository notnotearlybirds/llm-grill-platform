import uuid
from datetime import datetime, timezone

from sqlalchemy import exists, func, select

from src import db
from src.models import ACTIVE_RUN_STATUSES, GpuType, Result, Run, RunStatus


class RunRepository:
    @staticmethod
    async def get(run_id: uuid.UUID) -> Run | None:
        async with db.AsyncSessionLocal() as session:
            return await session.get(Run, run_id)

    @staticmethod
    async def get_all(status: RunStatus | None = None) -> list[Run]:
        async with db.AsyncSessionLocal() as session:
            q = select(Run)
            if status is not None:
                q = q.where(Run.status == status)
            result = await session.execute(q.order_by(Run.created_at.desc()))
            return list(result.scalars().all())

    @staticmethod
    async def claim_queued(
        gpu_type: GpuType, limit: int
    ) -> list[tuple[uuid.UUID, GpuType]]:
        """Atomically claim up to `limit` queued runs of `gpu_type`, set provisioning.

        Uses SELECT FOR UPDATE SKIP LOCKED so concurrent pollers never pick up
        the same run twice. Filtered by GPU type so the caller can cap claims to
        the per-type free quota (live GPUs of that type must stay <= quota).
        """
        if limit <= 0:
            return []
        async with db.AsyncSessionLocal() as session:
            result = await session.execute(
                select(Run)
                .where(
                    Run.status == RunStatus.queued,
                    Run.gpu_type_required == gpu_type,
                )
                .with_for_update(skip_locked=True)
                .limit(limit)
            )
            runs = result.scalars().all()
            now = datetime.now(timezone.utc)
            for run in runs:
                run.status = RunStatus.provisioning
                run.provisioning_started_at = now
            await session.commit()
            return [(r.id, r.gpu_type_required) for r in runs]

    @staticmethod
    async def count_live_by_type() -> dict[GpuType, int]:
        """Live GPUs per type = runs holding a VM (provisioning or running).

        `claim_queued` flips a run to `provisioning` in the same transaction it
        claims it, so this count reflects committed work immediately — it is the
        authoritative basis for the per-type capacity gate.
        """
        async with db.AsyncSessionLocal() as session:
            rows = (
                await session.execute(
                    select(Run.gpu_type_required, func.count())
                    .where(
                        Run.status.in_([RunStatus.provisioning, RunStatus.running])
                    )
                    .group_by(Run.gpu_type_required)
                )
            ).all()
        return {gt: 0 for gt in GpuType} | {gt: n for gt, n in rows}

    @staticmethod
    async def has_active_run(model: str, engine: str) -> bool:
        async with db.AsyncSessionLocal() as session:
            stmt = select(
                exists().where(
                    Run.model == model,
                    Run.engine == engine,
                    Run.status.in_(ACTIVE_RUN_STATUSES),
                )
            )
            return bool((await session.execute(stmt)).scalar())

    @staticmethod
    async def count_by_status() -> dict[str, int]:
        async with db.AsyncSessionLocal() as session:
            rows = (
                await session.execute(
                    select(Run.status, func.count()).group_by(Run.status)
                )
            ).all()
        counts: dict[str, int] = {s.value: 0 for s in RunStatus}
        for row_status, count in rows:
            counts[row_status.value] = count
        return counts

    @staticmethod
    async def create(run: Run) -> Run:
        async with db.AsyncSessionLocal() as session:
            session.add(run)
            await session.commit()
            await session.refresh(run)
            return run

    @staticmethod
    async def complete_run(run_id: uuid.UUID, results_url: str, result: Result) -> Run:
        async with db.AsyncSessionLocal() as session:
            run = await session.get(Run, run_id)
            if run is None:
                raise ValueError(f"Run {run_id} not found")
            run.status = RunStatus.done
            run.ended_at = datetime.now(timezone.utc)
            run.results_url = results_url
            session.add(result)
            await session.commit()
            await session.refresh(run)
            return run

    @staticmethod
    async def fail_run(run_id: uuid.UUID, error_message: str) -> Run:
        async with db.AsyncSessionLocal() as session:
            run = await session.get(Run, run_id)
            if run is None:
                raise ValueError(f"Run {run_id} not found")
            run.status = RunStatus.failed
            run.error_message = error_message
            run.ended_at = datetime.now(timezone.utc)
            await session.commit()
            await session.refresh(run)
            return run

    @staticmethod
    async def save(run: Run) -> Run:
        async with db.AsyncSessionLocal() as session:
            run = await session.merge(run)
            await session.commit()
            await session.refresh(run)
            return run

    @staticmethod
    async def set_provisioning(run_id: uuid.UUID) -> None:
        async with db.AsyncSessionLocal() as session:
            run = await session.get(Run, run_id)
            if run is None:
                raise ValueError(f"Run with id {run_id} not found")
            run.status = RunStatus.provisioning
            run.provisioning_started_at = datetime.now(timezone.utc)
            await session.commit()

    @staticmethod
    async def set_running(run_id: uuid.UUID, started_at: datetime) -> None:
        async with db.AsyncSessionLocal() as session:
            run = await session.get(Run, run_id)
            if run is None:
                raise ValueError(f"Run with id {run_id} not found")
            run.status = RunStatus.running
            run.started_at = started_at
            await session.commit()

    @staticmethod
    async def set_logs_url(run_id: uuid.UUID, logs_url: str) -> None:
        async with db.AsyncSessionLocal() as session:
            run = await session.get(Run, run_id)
            if run is None:
                raise ValueError(f"Run {run_id} not found")
            run.logs_url = logs_url
            await session.commit()

    @staticmethod
    async def set_phase(run_id: uuid.UUID, phase: str) -> None:
        async with db.AsyncSessionLocal() as session:
            run = await session.get(Run, run_id)
            if run is None:
                raise ValueError(f"Run {run_id} not found")
            if run.status != RunStatus.running:
                return  # reaper may have already claimed this run; silently ignore
            run.current_phase = phase
            run.phase_updated_at = datetime.now(timezone.utc)
            await session.commit()

    @staticmethod
    async def claim_running_timed_out(
        cutoff: datetime,
    ) -> list[tuple[uuid.UUID, str | None]]:
        """Transition timed-out `running` runs to `failed` and return (id, last_phase) pairs.

        Marks them failed in the same transaction as the SELECT so concurrent
        pollers can't both claim the same run. Caller is expected to release
        any associated node.
        """
        async with db.AsyncSessionLocal() as session:
            result = await session.execute(
                select(Run)
                .where(Run.status == RunStatus.running, Run.started_at < cutoff)
                .with_for_update(skip_locked=True)
            )
            runs = result.scalars().all()
            pairs = [(r.id, r.current_phase) for r in runs]
            now = datetime.now(timezone.utc)
            for r in runs:
                r.status = RunStatus.failed
                r.ended_at = now
                r.error_message = "timeout: claimed by reaper"
            await session.commit()
            return pairs

    @staticmethod
    async def get_orphaned_provisioning() -> list[uuid.UUID]:
        """Return ids of runs left in `provisioning` from a previous process.

        Called once at startup: since no concurrent worker exists yet, any row
        in `provisioning` is necessarily orphaned by the previous crash/restart.
        """
        async with db.AsyncSessionLocal() as session:
            result = await session.execute(
                select(Run.id).where(Run.status == RunStatus.provisioning)
            )
            return [row[0] for row in result.all()]

    @staticmethod
    async def claim_provisioning_timed_out(cutoff: datetime) -> list[uuid.UUID]:
        """Transition timed-out `provisioning` runs to `failed` and return their ids.

        A run can get stuck in `provisioning` if terraform hangs, the
        orchestrator crashed mid-apply, or any unhandled path skipped the
        `set_running`/`set_failed` transition. Measured from
        `provisioning_started_at` (when the run actually entered provisioning),
        coalescing to `created_at` for legacy rows — so time spent waiting in
        `queued` for a free GPU slot never trips the timeout.
        """
        async with db.AsyncSessionLocal() as session:
            started = func.coalesce(Run.provisioning_started_at, Run.created_at)
            result = await session.execute(
                select(Run)
                .where(Run.status == RunStatus.provisioning, started < cutoff)
                .with_for_update(skip_locked=True)
            )
            runs = result.scalars().all()
            ids = [r.id for r in runs]
            now = datetime.now(timezone.utc)
            for r in runs:
                r.status = RunStatus.failed
                r.ended_at = now
                r.error_message = "timeout: stuck in provisioning"
            await session.commit()
            return ids

    @staticmethod
    async def requeue_for_retry(run_id: uuid.UUID, max_attempts: int) -> int | None:
        """Increment provision_attempts and put the run back to queued.

        Returns the new attempt count if the run is eligible for another try,
        or None if max_attempts has been reached (caller should mark failed).
        """
        async with db.AsyncSessionLocal() as session:
            run = await session.get(Run, run_id)
            if run is None:
                raise ValueError(f"Run with id {run_id} not found")
            run.provision_attempts += 1
            if run.provision_attempts >= max_attempts:
                await session.commit()
                return None
            run.status = RunStatus.queued
            await session.commit()
            return run.provision_attempts

    @staticmethod
    async def set_failed(
        run_id: uuid.UUID, ended_at: datetime, error_message: str | None = None
    ) -> None:
        async with db.AsyncSessionLocal() as session:
            run = await session.get(Run, run_id)
            if run is None:
                raise ValueError(f"Run with id {run_id} not found")
            run.status = RunStatus.failed
            run.ended_at = ended_at
            if error_message is not None:
                run.error_message = error_message
            await session.commit()
