"""Composition root for the orphan sweep job (ADR 001e)."""

from __future__ import annotations

import logging
import sys

from pipeline.adapters.scaleway.instance_sweeper_adapter import (
    ScalewayInstanceSweeperAdapter,
)
from pipeline.application.services.sweep_service import SweepService


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    adapter = ScalewayInstanceSweeperAdapter()
    service = SweepService(adapter, name_prefix="grill-", max_age_hours=2.0)
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
    return report.exit_code


if __name__ == "__main__":
    sys.exit(main())
