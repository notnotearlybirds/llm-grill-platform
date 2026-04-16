"""Composition root for the nightly benchmark run."""

import asyncio
import datetime as dt
import subprocess
import sys
from pathlib import Path
from typing import Any

import typer
import yaml
from loguru import logger

from pipeline.adapters.huggingface.model_discovery_adapter import (
    HuggingFaceModelDiscoveryAdapter,
)
from pipeline.adapters.storage.filesystem_results_repository import (
    FilesystemResultsRepository,
)
from pipeline.application.domain.types import Backend, ModelCandidate
from pipeline.application.ports.infrastructure_port import (
    BenchmarkRunnerPort,
    InfrastructurePort,
    ProvisionedMachine,
)
from pipeline.application.services.aggregation_service import AggregationService
from pipeline.application.services.discovery_service import (
    DiscoveryFiltersConfig,
    DiscoveryResult,
    DiscoveryService,
)
from pipeline.application.services.orchestration_service import (
    OrchestrationConfig,
    OrchestrationService,
    compute_run_id,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
app = typer.Typer()


class _FixtureDiscovery:
    """Surfaces the fixture directory as a model catalog for --dry-run."""

    def __init__(self, fixtures_root: Path) -> None:
        self._root = fixtures_root

    def discover(self, filters: Any) -> list[ModelCandidate]:
        if not self._root.exists():
            return []
        seen: dict[str, ModelCandidate] = {}
        for date_dir in sorted(self._root.iterdir()):
            for slug_dir in sorted(date_dir.iterdir()):
                has_gguf = (slug_dir / "llamacpp.jsonl").exists()
                c = ModelCandidate(
                    model_id=slug_dir.name.replace("--", "/"),
                    size_gb=0.0,
                    has_gguf=has_gguf,
                )
                seen[c.model_id] = c
        return list(seen.values())


class _NoopInfrastructure:
    def provision(
        self, model_id: str, backends: list[str], run_id: str
    ) -> list[ProvisionedMachine]:
        return [
            ProvisionedMachine(backend=b, host="dry-run", instance_id="dry-run")
            for b in backends
        ]

    def destroy(self, model_id: str, run_id: str) -> None:
        return None


class _FixtureRunner:
    def __init__(self, fixtures_root: Path, date: str) -> None:
        self._root = fixtures_root
        self._date = date

    async def run(
        self, machine: ProvisionedMachine, model_id: str, run_id: str
    ) -> list[dict]:
        import json

        slug = model_id.replace("/", "--")
        path = self._root / self._date / slug / f"{machine.backend}.jsonl"
        if not path.exists():
            raise FileNotFoundError(path)
        with path.open("r", encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]


class _LiveRunner:  # pragma: no cover
    async def run(
        self, machine: ProvisionedMachine, model_id: str, run_id: str
    ) -> list[dict]:
        raise NotImplementedError(
            "Live benchmark runner is provisioned by infra and not part of this module."
        )


def _git_sha() -> str:
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )
    except Exception:
        return "0000000"


async def _amain(dry_run: bool) -> int:
    cfg = yaml.safe_load((REPO_ROOT / "pipeline" / "config.yaml").read_text())
    date = dt.date.today().isoformat()
    run_id = compute_run_id(date, _git_sha())

    results_root = REPO_ROOT / "results"
    fixtures_root = results_root / "fixtures"
    repo = FilesystemResultsRepository(
        root=results_root,
        read_roots=[fixtures_root] if dry_run else None,
    )

    if dry_run:
        date = "2026-04-14"
        discovery_port = _FixtureDiscovery(fixtures_root)
        infra: InfrastructurePort = _NoopInfrastructure()
        runner: BenchmarkRunnerPort = _FixtureRunner(fixtures_root, date)
    else:  # pragma: no cover
        discovery_port = HuggingFaceModelDiscoveryAdapter()
        from pipeline.adapters.terraform.infrastructure_adapter import (
            TerraformInfrastructureAdapter,
        )

        infra = TerraformInfrastructureAdapter(tf_dir=REPO_ROOT / "infra")
        runner = _LiveRunner()

    filters = DiscoveryFiltersConfig(**cfg["discovery"])
    backends: list[Backend] = list(cfg["backends"])

    discovery_service = DiscoveryService(discovery_port, repo)
    plan = discovery_service.plan(filters, backends, date)

    if dry_run and not plan:
        plan = [
            DiscoveryResult(model=c, pending_backends=c.eligible_backends(backends))
            for c in _FixtureDiscovery(fixtures_root).discover(filters)
        ]

    logger.info("plan: {} model(s)", len(plan))

    orchestration = OrchestrationService(infra, runner, repo)
    await orchestration.run(
        plan,
        OrchestrationConfig(
            per_backend_timeout_s=float(cfg["load"]["per_backend_timeout_s"]),
            date=date,
            run_id=run_id,
        ),
    )

    AggregationService(repo).aggregate()
    logger.info("done run_id={}", run_id)
    return 0


@app.command()
def main(
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Use fixtures, no provisioning."
    ),
) -> None:
    sys.exit(asyncio.run(_amain(dry_run=dry_run)))


if __name__ == "__main__":
    app()
