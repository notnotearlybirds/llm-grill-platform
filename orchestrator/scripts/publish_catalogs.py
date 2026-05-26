"""Publish models.json + scenarios.json to S3 — no VM, no GPU, no DB.

Used by the `publish-catalogs` CI job on any models.yaml / scenarios change.
Run from the orchestrator/ directory: `uv run python scripts/publish_catalogs.py`.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.services.bench_service import publish_catalogs  # noqa: E402

if __name__ == "__main__":
    asyncio.run(publish_catalogs())
    print("published models.json + scenarios.json")
