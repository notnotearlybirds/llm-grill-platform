"""Composition root for the orphan sweep job."""

from __future__ import annotations

import logging
import os

from pipeline.adapters.scaleway.instance_sweeper_adapter import (
    ScalewayInstanceSweeperAdapter,
)
from pipeline.application.services.sweep_service import SweepService

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)
    name_prefix = os.getenv("SWEEP_NAME_PREFIX", "grill-")
    max_age_hours = float(os.getenv("SWEEP_MAX_AGE_HOURS", "2.0"))
    adapter = ScalewayInstanceSweeperAdapter()
    service = SweepService(adapter, name_prefix=name_prefix, max_age_hours=max_age_hours)
    report = service.run()
    if report.orphans_found:
        logging.error(
            "orphans detected: %d found, %d destroyed, %d failed",
            len(report.orphans_found),
            len(report.destroyed),
            len(report.failed),
        )
    else:
        logging.info("no orphans")
    sys.exit(report.exit_code)
