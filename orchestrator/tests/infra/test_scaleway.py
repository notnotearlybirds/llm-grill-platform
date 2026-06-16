"""Tests for ScalewayQuotaAdapter — parsing the IAM Quotas API response."""

from __future__ import annotations

import pytest

from src.infra import scaleway
from src.infra.scaleway import ScalewayQuotaAdapter
from src.models import GpuType

# Trimmed shape of the real IAM /quota response (two GPU instance quotas, each
# with one {zone, limit} entry per AZ).
_PAYLOAD = {
    "quota": [
        {
            "name": "cp_servers_type_H100_1_80G",
            "limits": [
                {"zone": "fr-par-1", "limit": 1},
                {"zone": "fr-par-2", "limit": 3},
            ],
        },
        {
            "name": "cp_servers_type_L40S_1_48G",
            "limits": [
                {"zone": "fr-par-2", "limit": 2},
            ],
        },
    ],
    "total_count": 2,
}


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


class _FakeClient:
    def __init__(self, payload):
        self._payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def get(self, *args, **kwargs):
        return _FakeResponse(self._payload)


class TestFetchGpuQuota:
    async def test_reads_the_limit_for_the_requested_zone(self, mocker):
        """
        Given the IAM API returns per-zone limits for both GPU types
        When  fetch_gpu_quota("fr-par-2")
        Then  each type maps to its fr-par-2 limit (not another zone's)
        """
        # Given
        mocker.patch.object(
            scaleway.httpx, "AsyncClient", return_value=_FakeClient(_PAYLOAD)
        )

        # When
        quota = await ScalewayQuotaAdapter.fetch_gpu_quota("fr-par-2")

        # Then
        assert quota == {GpuType.H100: 3, GpuType.L40S: 2}

    async def test_omits_types_absent_for_the_zone(self, mocker):
        """
        Given a type with no entry for the requested zone
        When  fetch_gpu_quota
        Then  that type is omitted (caller falls back to config)
        """
        # Given
        mocker.patch.object(
            scaleway.httpx, "AsyncClient", return_value=_FakeClient(_PAYLOAD)
        )

        # When
        quota = await ScalewayQuotaAdapter.fetch_gpu_quota("nl-ams-1")

        # Then
        assert quota == {}

    async def test_raises_on_http_error(self, mocker):
        """Given the API errors, When fetch_gpu_quota, Then the error propagates."""

        # Given
        class _Boom(_FakeResponse):
            def raise_for_status(self):
                raise RuntimeError("503")

        class _BoomClient(_FakeClient):
            async def get(self, *args, **kwargs):
                return _Boom(None)

        mocker.patch.object(
            scaleway.httpx, "AsyncClient", return_value=_BoomClient(None)
        )

        # When / Then
        with pytest.raises(RuntimeError):
            await ScalewayQuotaAdapter.fetch_gpu_quota("fr-par-2")
