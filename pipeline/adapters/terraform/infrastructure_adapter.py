"""Terraform-based infrastructure adapter.

Shells out to ``terraform`` with per-model workspaces so provision/destroy
is idempotent. In tests and dry-run the composition root substitutes a
lighter implementation (see ``pipeline.run``).
"""

import subprocess
from pathlib import Path

from loguru import logger

from pipeline.application.ports.infrastructure_port import ProvisionedMachine


class TerraformInfrastructureAdapter:
    def __init__(self, tf_dir: Path) -> None:
        self._tf_dir = Path(tf_dir)

    def provision(
        self, model_id: str, backends: list[str], run_id: str
    ) -> list[ProvisionedMachine]:
        workspace = self._workspace(model_id, run_id)
        self._run(["terraform", "workspace", "select", "-or-create", workspace])
        self._run(
            [
                "terraform",
                "apply",
                "-auto-approve",
                f"-var=model_id={model_id}",
                f"-var=backends={','.join(backends)}",
                f"-var=run_id={run_id}",
            ]
        )
        return []  # pragma: no cover - exercised in integration tests only

    def destroy(self, model_id: str, run_id: str) -> None:
        workspace = self._workspace(model_id, run_id)
        self._run(["terraform", "workspace", "select", workspace])
        self._run(["terraform", "destroy", "-auto-approve"])

    @staticmethod
    def _workspace(model_id: str, run_id: str) -> str:
        slug = model_id.replace("/", "--")
        return f"{slug}-{run_id}"

    def _run(
        self, cmd: list[str]
    ) -> None:  # pragma: no cover - thin subprocess wrapper
        logger.info("terraform: {}", " ".join(cmd))
        subprocess.run(cmd, cwd=self._tf_dir, check=True)
