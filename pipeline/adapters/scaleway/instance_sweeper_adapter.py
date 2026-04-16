"""Scaleway API adapter that lists and terminates orphan benchmark instances."""

import datetime as dt

from loguru import logger
import scaleway
from scaleway.instance.v1 import InstanceV1API


class ScalewayInstanceSweeperAdapter:
    """Uses the official ``scaleway`` SDK."""

    def __init__(self, now: dt.datetime | None = None) -> None:
        try:  # pragma: no cover - exercised only when credentials are available
            client = scaleway.Client.from_config_file_and_env()
            self._api: InstanceV1API | None = InstanceV1API(client)
        except Exception as exc:  # pragma: no cover
            logger.warning("scaleway SDK not available: {}", exc)
            self._api = None
        self._now = now or (lambda: dt.datetime.now(dt.timezone.utc))

    def list_orphans(self, name_prefix: str, max_age_hours: float) -> list[str]:
        if self._api is None:
            return []
        cutoff = self._now() - dt.timedelta(hours=max_age_hours)
        servers = self._api.list_servers_all()
        return [
            s.id
            for s in servers
            if (s.name or "").startswith(name_prefix)
            and s.creation_date is not None
            and s.creation_date <= cutoff
            and s.id
        ]

    def destroy(self, instance_id: str) -> None:
        if self._api is None:
            return
        self._api.delete_server(server_id=instance_id)
