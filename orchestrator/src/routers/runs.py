import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.aggregation import aggregate
from src.db import AsyncSessionLocal, get_session
from src.models import Run, RunStatus
from src.orchestrator import release_node
from src.routing import select_gpu
from src.schemas import RunComplete, RunCreate, RunFail, RunRead
from src.storage import upload_results

router = APIRouter(prefix="/runs", tags=["runs"])


@router.post("", response_model=RunRead, status_code=status.HTTP_201_CREATED)
async def create_run(body: RunCreate, session: AsyncSession = Depends(get_session)):
    run = Run(**body.model_dump(), gpu_type_required=select_gpu(body.model_size_b))
    session.add(run)
    await session.commit()
    await session.refresh(run)
    return run


@router.get("", response_model=list[RunRead])
async def list_runs(
    status: RunStatus | None = Query(None),
    session: AsyncSession = Depends(get_session),
):
    q = select(Run)
    if status is not None:
        q = q.where(Run.status == status)
    result = await session.execute(q.order_by(Run.created_at.desc()))
    return result.scalars().all()


@router.get("/{run_id}", response_model=RunRead)
async def get_run(run_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    run = await session.get(Run, run_id)
    if run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="run not found")
    return run


@router.post("/{run_id}/complete", response_model=RunRead)
async def complete_run(
    run_id: uuid.UUID,
    body: RunComplete,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    run = await session.get(Run, run_id)
    if run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="run not found")
    if run.status != RunStatus.running:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="run is not running")
    results_url = await upload_results(run_id, body.results_jsonl)
    result = aggregate(body.results_jsonl, run)
    session.add(result)
    run.status = RunStatus.done
    run.results_url = results_url
    run.ended_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(run)
    background_tasks.add_task(release_node, run_id, AsyncSessionLocal)
    return run


@router.post("/{run_id}/fail", response_model=RunRead)
async def fail_run(
    run_id: uuid.UUID,
    body: RunFail,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    run = await session.get(Run, run_id)
    if run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="run not found")
    if run.status not in {RunStatus.running, RunStatus.provisioning}:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="run cannot be failed")
    run.status = RunStatus.failed
    run.error_message = body.error_message
    run.ended_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(run)
    background_tasks.add_task(release_node, run_id, AsyncSessionLocal)
    return run
