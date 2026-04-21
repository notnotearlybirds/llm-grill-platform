import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_session
from src.models import Result
from src.schemas import ResultRead
from src.storage import presigned_url

router = APIRouter(prefix="/results", tags=["results"])


@router.get("", response_model=list[ResultRead])
async def list_results(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Result).order_by(Result.created_at.desc()))
    return result.scalars().all()


@router.get("/{run_id}", response_model=ResultRead)
async def get_result(run_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Result).where(Result.run_id == run_id))
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="result not found")
    return row


@router.get("/{run_id}/download")
async def download_result(
    run_id: uuid.UUID, session: AsyncSession = Depends(get_session)
):
    result = await session.execute(select(Result).where(Result.run_id == run_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="result not found")
    url = await presigned_url(run_id)
    return {"url": url}
