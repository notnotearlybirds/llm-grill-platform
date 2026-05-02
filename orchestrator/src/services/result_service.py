from __future__ import annotations

import uuid

from src.models import Result
from src.repositories.result_repository import ResultRepository
from src.schemas import LeaderboardEntry
from src.storage import presigned_url


class ResultService:
    @staticmethod
    async def list() -> list[Result]:
        return await ResultRepository.get_all()

    @staticmethod
    async def get_by_run(run_id: uuid.UUID) -> Result | None:
        return await ResultRepository.get_by_run(run_id)

    @staticmethod
    async def get_download_url(run_id: uuid.UUID) -> str:
        return await presigned_url(run_id)

    @staticmethod
    async def get_leaderboard() -> list[LeaderboardEntry]:
        rows = await ResultRepository.get_latest_per_combination()
        return [LeaderboardEntry.model_validate(r) for r in rows]
