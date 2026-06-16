from __future__ import annotations

import httpx

from src.config import settings
from src.models import GpuType

_IAM_QUOTA_URL = "https://api.scaleway.com/iam/v1alpha1/quota"

# Scaleway quotum name per GPU instance type (locality_type=zone). The `limits`
# array carries one {zone, limit} entry per AZ; we read the one for GPU_ZONE.
_QUOTUM_NAME: dict[GpuType, str] = {
    GpuType.H100: "cp_servers_type_H100_1_80G",
    GpuType.L40S: "cp_servers_type_L40S_1_48G",
}


class ScalewayQuotaAdapter:
    """Reads per-zone GPU instance quotas from the Scaleway IAM Quotas API."""

    @staticmethod
    async def fetch_gpu_quota(zone: str) -> dict[GpuType, int]:
        """Return {GpuType: limit} for `zone`. Raises on transport/HTTP error.

        Only types the API reports for `zone` are included; the caller decides
        the fallback for anything missing.
        """
        by_name = {name: gpu_type for gpu_type, name in _QUOTUM_NAME.items()}
        params: list[tuple[str, str | int | float | None]] = [
            ("organization_id", settings.scw_default_organization_id)
        ]
        params += [("quotum_names", name) for name in _QUOTUM_NAME.values()]
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                _IAM_QUOTA_URL,
                params=params,
                headers={"X-Auth-Token": settings.scw_secret_key},
            )
            resp.raise_for_status()
            payload = resp.json()

        quota: dict[GpuType, int] = {}
        for entry in payload.get("quota", []):
            gpu_type = by_name.get(entry.get("name"))
            if gpu_type is None:
                continue
            for limit in entry.get("limits", []):
                if limit.get("zone") == zone:
                    quota[gpu_type] = limit["limit"]
                    break
        return quota
