"""
Tests for the runs API and orchestrator polling logic.

Covers: run creation, retrieval, listing, status filtering,
and the GPU node assignment loop.
"""

import uuid

import pytest

from src.models import GpuType, Run, RunStatus
from src.orchestrator import poll_once
from src.routing import select_gpu

SMALL_MODEL_PAYLOAD = {
    "model": "meta-llama/Llama-3-8B",
    "model_size_b": 8,
    "engine": "vllm",
    "scenario_path": "scenarios/basic.yaml",
}

LARGE_MODEL_PAYLOAD = {
    "model": "meta-llama/Llama-3-70B",
    "model_size_b": 70,
    "engine": "vllm",
    "scenario_path": "scenarios/basic.yaml",
}


class TestRunCreation:
    """Tests for POST /runs."""

    async def test_should_create_run_with_queued_status(self, client):
        """
        Should persist a new run and return it as queued.

        Given: A valid run payload for an 8B model
        When: POST /runs is called
        Then: 201 response with a UUID, status=queued, gpu_count=1
        """
        # When
        resp = await client.post("/runs", json=SMALL_MODEL_PAYLOAD)

        # Then
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "queued"
        assert uuid.UUID(data["id"])
        assert data["gpu_count"] == 1

    async def test_should_auto_assign_gpu_type_from_model_size(self, client):
        """
        Should set gpu_type_required automatically based on model_size_b.

        Given: An 8B model payload
        When: POST /runs is called
        Then: gpu_type_required is L40S (routed automatically)
        """
        # When
        resp = await client.post("/runs", json=SMALL_MODEL_PAYLOAD)

        # Then
        assert resp.json()["gpu_type_required"] == "L40S"

    async def test_should_reject_non_positive_model_size(self, client):
        """
        Should return 422 when model_size_b is zero or negative.

        Given: A payload with model_size_b=0
        When: POST /runs is called
        Then: 422 Unprocessable Entity
        """
        # Given
        bad_payload = {**SMALL_MODEL_PAYLOAD, "model_size_b": 0}

        # When
        resp = await client.post("/runs", json=bad_payload)

        # Then
        assert resp.status_code == 422


class TestRunRetrieval:
    """Tests for GET /runs/{id}."""

    async def test_should_return_run_by_id(self, client):
        """
        Should return the run matching the given UUID.

        Given: A run was created
        When: GET /runs/{id} is called with the returned UUID
        Then: 200 with the same run id
        """
        # Given
        run_id = (await client.post("/runs", json=SMALL_MODEL_PAYLOAD)).json()["id"]

        # When
        resp = await client.get(f"/runs/{run_id}")

        # Then
        assert resp.status_code == 200
        assert resp.json()["id"] == run_id

    async def test_should_return_404_when_run_does_not_exist(self, client):
        """
        Should return 404 for an unknown run UUID.

        Given: No run exists with the given id
        When: GET /runs/{id} is called
        Then: 404 Not Found
        """
        # When
        resp = await client.get(f"/runs/{uuid.uuid4()}")

        # Then
        assert resp.status_code == 404


class TestRunListing:
    """Tests for GET /runs."""

    async def test_should_list_all_runs(self, client):
        """
        Should return all runs regardless of status.

        Given: Two runs created with different model sizes
        When: GET /runs is called without filter
        Then: Both runs are returned
        """
        # Given
        await client.post("/runs", json=SMALL_MODEL_PAYLOAD)
        await client.post("/runs", json=LARGE_MODEL_PAYLOAD)

        # When
        resp = await client.get("/runs")

        # Then
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    async def test_should_filter_runs_by_status(self, client):
        """
        Should return only runs matching the requested status.

        Given: One queued run exists
        When: GET /runs?status=queued and GET /runs?status=running
        Then: One result for queued, zero for running
        """
        # Given
        await client.post("/runs", json=SMALL_MODEL_PAYLOAD)

        # When / Then
        assert len((await client.get("/runs?status=queued")).json()) == 1
        assert len((await client.get("/runs?status=running")).json()) == 0


class TestOrchestratorPolling:
    """Tests for the GPU node assignment polling loop."""

    async def test_should_assign_run_when_compatible_node_available(
        self, session_factory, idle_h100, queued_run
    ):
        """
        Should transition run to running when a matching idle node exists.

        Given: A queued H100 run and one idle H100 node in the DB
        When: poll_once is called
        Then: Run status becomes running and started_at is set
        """
        # When
        await poll_once(session_factory)

        # Then
        async with session_factory() as session:
            run = await session.get(Run, queued_run)
        assert run.status == RunStatus.running
        assert run.started_at is not None

    async def test_should_leave_run_queued_when_no_compatible_node(
        self, session_factory, idle_l40s, queued_run
    ):
        """
        Should not assign an H100 run when only an L40S node is available.

        Given: A queued H100 run and one idle L40S node in the DB
        When: poll_once is called
        Then: Run status remains queued
        """
        # When
        await poll_once(session_factory)

        # Then
        async with session_factory() as session:
            run = await session.get(Run, queued_run)
        assert run.status == RunStatus.queued


class TestGpuRouting:
    """Unit tests for the GPU routing logic (threshold: < 26B → L40S, else H100)."""

    @pytest.mark.parametrize("model_size_b", [3, 7, 8, 13, 25])
    def test_should_route_below_threshold_to_l40s(self, model_size_b):
        """
        Should return L40S for any model strictly below 26B.

        Given: A model size in billions below the 26B threshold
        When: select_gpu is called
        Then: GpuType.L40S is returned
        """
        assert select_gpu(model_size_b) == GpuType.L40S

    @pytest.mark.parametrize("model_size_b", [26, 30, 70, 405])
    def test_should_route_at_or_above_threshold_to_h100(self, model_size_b):
        """
        Should return H100 for any model at or above 26B.

        Given: A model size in billions at or above the 26B threshold
        When: select_gpu is called
        Then: GpuType.H100 is returned
        """
        assert select_gpu(model_size_b) == GpuType.H100
