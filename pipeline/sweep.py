"""Composition root for the orphan sweep job."""

import os

from loguru import logger

from pipeline.adapters.scaleway.instance_sweeper_adapter import (
    ScalewayInstanceSweeperAdapter,
)
from pipeline.application.services.sweep_service import SweepService

if __name__ == "__main__":
    import sys

    name_prefix = os.getenv("SWEEP_NAME_PREFIX", "grill-")
    max_age_hours = float(os.getenv("SWEEP_MAX_AGE_HOURS", "2.0"))
    adapter = ScalewayInstanceSweeperAdapter()
    service = SweepService(
        adapter, name_prefix=name_prefix, max_age_hours=max_age_hours
    )
    report = service.run()
    if report.orphans_found:
        logger.error(
            "orphans detected: {} found, {} destroyed, {} failed",
            len(report.orphans_found),
            len(report.destroyed),
            len(report.failed),
        )
    else:
        logger.info("no orphans")
    sys.exit(report.exit_code)
