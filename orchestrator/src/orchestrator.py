import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.config import settings
from src.models import Node, NodeStatus, Run, RunStatus

logger = logging.getLogger(__name__)


async def find_idle_node(session: AsyncSession, run: Run) -> Node | None:
    result = await session.execute(
        select(Node)
        .where(Node.gpu_type == run.gpu_type_required)
        .where(Node.status == NodeStatus.idle)
        .limit(1)
    )
    return result.scalar_one_or_none()


async def assign_and_launch(session: AsyncSession, run: Run, node: Node) -> None:
    run.status = RunStatus.running
    run.started_at = datetime.now(timezone.utc)
    node.status = NodeStatus.busy
    node.current_run_id = run.id
    await session.commit()
    logger.info("run %s assigned to node %s", run.id, node.id)


async def poll_once(session_factory: async_sessionmaker) -> None:
    async with session_factory() as session:
        result = await session.execute(
            select(Run).where(Run.status == RunStatus.queued)
        )
        queued = result.scalars().all()
        for run in queued:
            node = await find_idle_node(session, run)
            if node:
                await assign_and_launch(session, run, node)


async def polling_loop(session_factory: async_sessionmaker) -> None:
    while True:
        try:
            await poll_once(session_factory)
        except Exception:
            logger.exception("orchestrator poll error")
        await asyncio.sleep(settings.poll_interval_seconds)
