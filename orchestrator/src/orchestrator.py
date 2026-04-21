import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.config import settings
from src.models import Node, NodeStatus, Run, RunStatus
from src.terraform import destroy_node, provision_node

logger = logging.getLogger(__name__)


async def handle_queued_run(session: AsyncSession, run: Run) -> None:
    node = Node(
        id=f"node-{run.id}",
        gpu_type=run.gpu_type_required,
        status=NodeStatus.provisioning,
        current_run_id=run.id,
    )
    session.add(node)
    run.status = RunStatus.provisioning
    await session.commit()

    try:
        instance_id, public_ip = await provision_node(run.id, run.gpu_type_required)
        node.id = instance_id
        node.ip_address = public_ip
        node.status = NodeStatus.busy
        run.status = RunStatus.running
        run.started_at = datetime.now(timezone.utc)
        await session.commit()
        logger.info("run %s running on node %s (%s)", run.id, instance_id, public_ip)
    except Exception:
        logger.exception("failed to provision node for run %s", run.id)
        run.status = RunStatus.failed
        run.ended_at = datetime.now(timezone.utc)
        node.status = NodeStatus.down
        await session.commit()


async def release_node(run_id, session_factory: async_sessionmaker) -> None:
    """Destroy the ephemeral node and mark it down. Called after run completion."""
    try:
        await destroy_node(run_id)
    except Exception:
        logger.exception("failed to destroy node for run %s", run_id)
    async with session_factory() as session:
        result = await session.execute(
            select(Node).where(Node.current_run_id == run_id)
        )
        node = result.scalar_one_or_none()
        if node:
            node.status = NodeStatus.down
            await session.commit()


async def poll_once(session_factory: async_sessionmaker) -> None:
    async with session_factory() as session:
        result = await session.execute(
            select(Run).where(Run.status == RunStatus.queued)
        )
        queued = result.scalars().all()
        for run in queued:
            asyncio.create_task(handle_queued_run(session, run))


async def polling_loop(session_factory: async_sessionmaker) -> None:
    while True:
        try:
            await poll_once(session_factory)
        except Exception:
            logger.exception("orchestrator poll error")
        await asyncio.sleep(settings.poll_interval_seconds)
