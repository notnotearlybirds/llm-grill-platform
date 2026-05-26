"""Print how many models would actually be benched — CI provisioning gate.

Reads FORCE / MODEL_FILTER from the environment, checks S3 dedup, prints a
single integer. The bench workflow skips provisioning a VM when it's 0.
Run from orchestrator/: `uv run python scripts/pending_runs.py`.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.services.bench_service import pending_run_count  # noqa: E402

if __name__ == "__main__":
    force = os.environ.get("FORCE", "false").strip().lower() == "true"
    model_filter = os.environ.get("MODEL_FILTER", "").strip() or None
    print(asyncio.run(pending_run_count(force, model_filter)))
