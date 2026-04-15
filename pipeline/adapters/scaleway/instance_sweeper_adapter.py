"""Scaleway API adapter that lists and terminates orphan benchmark instances."""

from __future__ import annotations

import datetime as dt
import logging
from typing import Any

logger = logging.getLogger(__name__)


class ScalewayInstanceSweeperAdapter:
    """Uses the official ``scaleway`` SDK. The concrete client is injectable
    so the class is testable without credentials or network."""

    def __init__(self, instance_api: Any | None = None, now: Any | None = None) -> None:
        if instance_api is None:
            try:  # pragma: no cover - exercised only when lib is installed
                import scaleway
                from scaleway.instance.v1 import InstanceV1API

                client = scaleway.Client.from_config_file_and_env()
                instance_api = InstanceV1API(client)
            except Exception as exc:  # pragma: no cover
                logger.warning("scaleway SDK not available: %s", exc)
                instance_api = None
        self._api = instance_api
        self._now = now or (lambda: dt.datetime.now(dt.timezone.utc))

    def list_orphans(self, name_prefix: str, max_age_hours: float) -> list[str]:
        if self._api is None:
            return []
        cutoff = self._now() - dt.timedelta(hours=max_age_hours)
        servers = self._api.list_servers_all()
        orphans: list[str] = []
        for s in servers:
            name = getattr(s, "name", "") or ""
            created = getattr(s, "creation_date", None)
            if not name.startswith(name_prefix):
                continue
            if created is None or created <= cutoff:
                orphans.append(getattr(s, "id", ""))
        return [o for o in orphans if o]

    def destroy(self, instance_id: str) -> None:
        if self._api is None:
            return
        self._api.delete_server(server_id=instance_id)
