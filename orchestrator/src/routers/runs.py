import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_session
from src.models import Run, RunStatus
from src.routing import select_gpu
from src.schemas import RunCreate, RunRead

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
