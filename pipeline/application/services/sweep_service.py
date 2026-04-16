"""Orphan instance sweep."""

from pydantic import BaseModel

from pipeline.application.ports.infrastructure_port import InstanceSweeperPort


class SweepReport(BaseModel):
    orphans_found: list[str]
    destroyed: list[str]
    failed: list[tuple[str, str]]

    @property
    def exit_code(self) -> int:
        return 0 if not self.orphans_found else 1


class SweepService:
    def __init__(
        self,
        sweeper: InstanceSweeperPort,
        name_prefix: str = "grill-",
        max_age_hours: float = 2.0,
    ) -> None:
        self._sweeper = sweeper
        self._prefix = name_prefix
        self._max_age = max_age_hours

    def run(self) -> SweepReport:
        orphans = self._sweeper.list_orphans(self._prefix, self._max_age)
        destroyed: list[str] = []
        failed: list[tuple[str, str]] = []
        for instance_id in orphans:
            try:
                self._sweeper.destroy(instance_id)
                destroyed.append(instance_id)
            except Exception as exc:
                failed.append((instance_id, str(exc)))
        return SweepReport(orphans_found=orphans, destroyed=destroyed, failed=failed)
