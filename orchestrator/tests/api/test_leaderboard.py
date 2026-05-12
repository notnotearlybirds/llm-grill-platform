"""
Tests for the GET /leaderboard endpoint.

Covers: empty state, grouping by (model, engine, gpu_type),
most-recent-wins selection, and ordering by total_tokens_per_second.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from src.models import Engine, GpuType, Result, Run, RunStatus


def _make_run(session_factory):
    async def _inner(**kwargs):
        defaults = dict(
            model="meta-llama/Llama-3-8B",
            model_size_b=8,
            engine=Engine.vllm,
            gpu_type_required=GpuType.L40S,
            scenario_path="scenarios/basic_8b.yaml",
            status=RunStatus.done,
        )
        async with session_factory() as session:
            run = Run(**{**defaults, **kwargs})
            session.add(run)
            await session.commit()
            return run.id

    return _inner


def _make_result(run_id: uuid.UUID, **kwargs) -> Result:
    defaults = dict(
        id=uuid.uuid4(),
        run_id=run_id,
        model="meta-llama/Llama-3-8B",
        engine="vllm",
        gpu_type=GpuType.L40S,
        scenario="scenarios/basic_8b.yaml",
        total_requests=100,
        success_count=99,
        error_count=1,
        success_rate=0.99,
        ttft_mean_s=0.12,
        ttft_median_s=0.11,
        ttft_p95_s=0.25,
        tpot_mean_s=0.03,
        e2e_mean_s=0.50,
        e2e_p95_s=0.80,
        tokens_per_second_mean=45.0,
        total_tokens_per_second=120.0,
        requests_per_second=3.5,
        total_duration_s=28.6,
    )
    return Result(**{**defaults, **kwargs})


async def _insert(session_factory, result: Result) -> None:
    async with session_factory() as session:
        session.add(result)
        await session.commit()


class TestLeaderboard:
    async def test_should_return_empty_list_when_no_results(self, client):
        """
        Should return an empty list when no benchmark results exist.

        Given: Empty DB
        When: GET /leaderboard is called
        Then: 200 with empty list
        """
        # When
        resp = await client.get("/leaderboard")

        # Then
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_should_return_one_entry_per_model_engine_gpu_group(
        self, client, session_factory
    ):
        """
        Should deduplicate to one entry per (model, engine, gpu_type) group.

        Given: Two results for the same (model, engine, gpu_type)
        When: GET /leaderboard is called
        Then: Only one entry returned
        """
        # Given
        create_run = _make_run(session_factory)
        run_id_1 = await create_run()
        run_id_2 = await create_run()
        now = datetime.now(timezone.utc)
        await _insert(
            session_factory, _make_result(run_id_1, created_at=now - timedelta(hours=2))
        )
        await _insert(session_factory, _make_result(run_id_2, created_at=now))

        # When
        resp = await client.get("/leaderboard")

        # Then
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_should_return_most_recent_result_when_multiple_runs(
        self, client, session_factory
    ):
        """
        Should select the most recent result when multiple runs exist for the same group.

        Given: Two results for the same group, one older with higher throughput
        When: GET /leaderboard is called
        Then: The most recent result is returned (not the highest throughput)
        """
        # Given
        create_run = _make_run(session_factory)
        run_id_old = await create_run()
        run_id_new = await create_run()
        now = datetime.now(timezone.utc)
        await _insert(
            session_factory,
            _make_result(
                run_id_old,
                total_tokens_per_second=999.0,
                created_at=now - timedelta(hours=5),
            ),
        )
        await _insert(
            session_factory,
            _make_result(
                run_id_new,
                total_tokens_per_second=50.0,
                created_at=now,
            ),
        )

        # When
        resp = await client.get("/leaderboard")

        # Then
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["total_tokens_per_second"] == pytest.approx(50.0)
        assert resp.json()[0]["run_id"] == str(run_id_new)

    async def test_should_sort_by_total_tokens_per_second_descending(
        self, client, session_factory
    ):
        """
        Should return entries sorted by total_tokens_per_second descending.

        Given: Two results for different models with different throughput
        When: GET /leaderboard is called
        Then: Higher throughput appears first
        """
        # Given
        create_run = _make_run(session_factory)
        run_id_fast = await create_run(model="mistralai/Mistral-7B-v0.1")
        run_id_slow = await create_run(model="meta-llama/Llama-3-8B")
        await _insert(
            session_factory,
            _make_result(
                run_id_fast,
                model="mistralai/Mistral-7B-v0.1",
                total_tokens_per_second=200.0,
            ),
        )
        await _insert(
            session_factory,
            _make_result(
                run_id_slow,
                model="meta-llama/Llama-3-8B",
                total_tokens_per_second=80.0,
            ),
        )

        # When
        resp = await client.get("/leaderboard")

        # Then
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["model"] == "mistralai/Mistral-7B-v0.1"
        assert data[1]["model"] == "meta-llama/Llama-3-8B"

    async def test_should_group_separately_by_gpu_type(self, client, session_factory):
        """
        Should return one entry per GPU type for the same model+engine.

        Given: Same model/engine benchmarked on L40S and H100
        When: GET /leaderboard is called
        Then: Two entries returned, one per GPU
        """
        # Given
        create_run = _make_run(session_factory)
        run_l40s = await create_run(gpu_type_required=GpuType.L40S)
        run_h100 = await create_run(gpu_type_required=GpuType.H100)
        await _insert(
            session_factory,
            _make_result(
                run_l40s, gpu_type=GpuType.L40S, total_tokens_per_second=120.0
            ),
        )
        await _insert(
            session_factory,
            _make_result(
                run_h100, gpu_type=GpuType.H100, total_tokens_per_second=180.0
            ),
        )

        # When
        resp = await client.get("/leaderboard")

        # Then
        assert resp.status_code == 200
        assert len(resp.json()) == 2
        gpus = {e["gpu_type"] for e in resp.json()}
        assert gpus == {"L40S", "H100"}
