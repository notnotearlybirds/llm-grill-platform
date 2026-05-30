import uuid

from fastapi import HTTPException, status

from src.models import Result
from src.repositories.result_repository import ResultRepository
from src.repositories.run_repository import RunRepository
from src.storage import presigned_url


class ResultService:
    @staticmethod
    async def get_by_run(run_id: uuid.UUID) -> Result | None:
        return await ResultRepository.get_by_run(run_id)

    @staticmethod
    async def get_download_url(run_id: uuid.UUID) -> str:
        run = await RunRepository.get(run_id)
        if run is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="run not found")
        return await presigned_url(run)
