import asyncio
import logging
from datetime import datetime, timezone

from src.config import settings
from src.infra.terraform import destroy_node, provision_node
from src.repositories.node_repository import NodeRepository
from src.repositories.run_repository import RunRepository

logger = logging.getLogger(__name__)


async def handle_queued_run(run_id, gpu_type_required) -> None:
    await NodeRepository.create_provisioning(run_id, gpu_type_required)
    await RunRepository.set_provisioning(run_id)

    try:
        instance_id, public_ip = await provision_node(run_id, gpu_type_required)
        await NodeRepository.set_busy(run_id, instance_id, public_ip)
        await RunRepository.set_running(run_id, datetime.now(timezone.utc))
        logger.info("run %s running on node %s (%s)", run_id, instance_id, public_ip)
    except Exception as exc:
        logger.exception("failed to provision node for run %s", run_id)
        await NodeRepository.set_down_by_run(run_id)
        await RunRepository.set_failed(run_id, datetime.now(timezone.utc), str(exc))


async def release_node(run_id) -> None:
    try:
        await destroy_node(run_id)
    except Exception:
        logger.exception("failed to destroy node for run %s", run_id)
    await NodeRepository.set_down_by_run(run_id)


async def poll_once() -> None:
    queued = await RunRepository.get_queued()
    for run_id, gpu_type_required in queued:
        asyncio.create_task(handle_queued_run(run_id, gpu_type_required))


async def polling_loop() -> None:
    while True:
        try:
            await poll_once()
        except Exception:
            logger.exception("orchestrator poll error")
        await asyncio.sleep(settings.poll_interval_seconds)
