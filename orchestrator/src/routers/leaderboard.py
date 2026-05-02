from __future__ import annotations

from fastapi import APIRouter

from src.controllers.result_controller import ResultController
from src.schemas import LeaderboardEntry

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@router.get("", response_model=list[LeaderboardEntry])
async def get_leaderboard():
    return await ResultController.leaderboard()
