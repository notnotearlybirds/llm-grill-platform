"""Composition root for the aggregation step."""

from pathlib import Path

from pipeline.adapters.storage.filesystem_results_repository import (
    FilesystemResultsRepository,
)
from pipeline.application.services.aggregation_service import AggregationService

REPO_ROOT = Path(__file__).resolve().parent.parent

if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(prog="pipeline.aggregate")
    parser.add_argument(
        "--include-fixtures",
        action="store_true",
        help="Also read results/fixtures/** (used in dry-run and tests).",
    )
    args = parser.parse_args()

    results_root = REPO_ROOT / "results"
    fixtures_root = results_root / "fixtures"
    repo = FilesystemResultsRepository(
        root=results_root,
        read_roots=[fixtures_root] if args.include_fixtures else None,
    )
    AggregationService(repo).aggregate()
    sys.exit(0)
