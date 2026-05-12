import uuid

from fastapi import BackgroundTasks, HTTPException, status

from src.models import RunStatus
from src.orchestrator import release_node
from src.schemas import RunComplete, RunCreate, RunFail, RunRead
from src.services.run_service import RunService


class RunController:
    @staticmethod
    async def create(body: RunCreate) -> RunRead:
        run = await RunService.create(body)
        return RunRead.model_validate(run)

    @staticmethod
    async def list_all(status: RunStatus | None) -> list[RunRead]:
        runs = await RunService.list_all(status)
        return [RunRead.model_validate(r) for r in runs]

    @staticmethod
    async def get(run_id: uuid.UUID) -> RunRead:
        run = await RunService.get(run_id)
        if run is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="run not found")
        return RunRead.model_validate(run)

    @staticmethod
    async def complete(
        run_id: uuid.UUID,
        body: RunComplete,
        background_tasks: BackgroundTasks,
    ) -> RunRead:
        run = await RunService.complete(run_id, body.results_jsonl)
        background_tasks.add_task(release_node, run_id)
        return RunRead.model_validate(run)

    @staticmethod
    async def fail(
        run_id: uuid.UUID,
        body: RunFail,
        background_tasks: BackgroundTasks,
    ) -> RunRead:
        run = await RunService.fail(run_id, body.error_message)
        background_tasks.add_task(release_node, run_id)
        return RunRead.model_validate(run)
