"""Port for provisioning/destroying benchmark infrastructure."""

from typing import Protocol

from pydantic import BaseModel


class ProvisionedMachine(BaseModel, frozen=True):
    backend: str
    host: str
    instance_id: str


class InfrastructurePort(Protocol):
    """Provision and destroy the machines used by a single model benchmark."""

    def provision(
        self, model_id: str, backends: list[str], run_id: str
    ) -> list[ProvisionedMachine]: ...

    def destroy(self, model_id: str, run_id: str) -> None: ...


class BenchmarkRunnerPort(Protocol):
    """Run a benchmark on a provisioned machine and return raw JSONL rows."""

    async def run(
        self, machine: ProvisionedMachine, model_id: str, run_id: str
    ) -> list[dict]: ...


class InstanceSweeperPort(Protocol):
    """List and terminate orphan benchmark instances."""

    def list_orphans(self, name_prefix: str, max_age_hours: float) -> list[str]: ...

    def destroy(self, instance_id: str) -> None: ...
