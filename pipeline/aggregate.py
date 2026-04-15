"""Composition root for the aggregation step (ADR 001f)."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from pipeline.adapters.storage.filesystem_results_repository import (
    FilesystemResultsRepository,
)
from pipeline.application.services.aggregation_service import AggregationService

REPO_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(prog="pipeline.aggregate")
    parser.add_argument(
        "--include-fixtures",
        action="store_true",
        help="Also read results/fixtures/** (used in dry-run and tests).",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)

    results_root = REPO_ROOT / "results"
    fixtures_root = results_root / "fixtures"
    repo = FilesystemResultsRepository(
        root=results_root,
        read_roots=[fixtures_root] if args.include_fixtures else None,
    )
    AggregationService(repo).aggregate()
    return 0


if __name__ == "__main__":
    sys.exit(main())
