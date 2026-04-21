from fastapi import APIRouter, Depends
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_session
from src.models import Result
from src.schemas import LeaderboardEntry

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@router.get("", response_model=list[LeaderboardEntry])
async def get_leaderboard(session: AsyncSession = Depends(get_session)):
    subq = (
        select(
            Result.model,
            Result.engine,
            Result.gpu_type,
            func.max(Result.created_at).label("latest"),
        )
        .group_by(Result.model, Result.engine, Result.gpu_type)
        .subquery()
    )
    stmt = (
        select(Result)
        .join(
            subq,
            and_(
                Result.model == subq.c.model,
                Result.engine == subq.c.engine,
                Result.gpu_type == subq.c.gpu_type,
                Result.created_at == subq.c.latest,
            ),
        )
        .order_by(Result.total_tokens_per_second.desc())
    )
    rows = (await session.execute(stmt)).scalars().all()
    return [
        LeaderboardEntry(
            model=r.model,
            engine=r.engine,
            gpu_type=r.gpu_type,
            tokens_per_second_mean=r.tokens_per_second_mean,
            total_tokens_per_second=r.total_tokens_per_second,
            requests_per_second=r.requests_per_second,
            e2e_p95_s=r.e2e_p95_s,
            ttft_p95_s=r.ttft_p95_s,
            success_rate=r.success_rate,
            run_id=r.run_id,
            measured_at=r.created_at,
        )
        for r in rows
    ]
