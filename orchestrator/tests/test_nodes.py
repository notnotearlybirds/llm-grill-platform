"""
Tests for the nodes API and DB-backed allocation logic.

Covers: node registration, listing, deregistration,
and strict idle/gpu_type allocation enforcement.
"""

from src.models import GpuType, Node, NodeStatus, Run, RunStatus
from src.orchestrator import find_idle_node, poll_once

NODE_H100 = {"id": "gpu-h100-1", "gpu_type": "H100", "gpu_count": 1}
NODE_L40S = {"id": "gpu-l40s-1", "gpu_type": "L40S", "gpu_count": 1}


class TestNodeRegistration:
    """Tests for POST /nodes."""

    async def test_should_register_node_as_idle(self, client):
        """
        Should persist a new node with idle status.

        Given: A valid node payload
        When: POST /nodes is called
        Then: 201 with status=idle and correct gpu_type
        """
        # When
        resp = await client.post("/nodes", json=NODE_H100)

        # Then
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "idle"
        assert data["gpu_type"] == "H100"
        assert data["current_run_id"] is None

    async def test_should_reject_duplicate_node_id(self, client):
        """
        Should return 409 when a node with the same id already exists.

        Given: A node with id gpu-h100-1 already registered
        When: POST /nodes is called again with the same id
        Then: 409 Conflict
        """
        # Given
        await client.post("/nodes", json=NODE_H100)

        # When
        resp = await client.post("/nodes", json=NODE_H100)

        # Then
        assert resp.status_code == 409


class TestNodeListing:
    """Tests for GET /nodes and GET /nodes/{id}."""

    async def test_should_list_all_nodes(self, client):
        """
        Should return all registered nodes.

        Given: Two nodes registered (H100 and L40S)
        When: GET /nodes is called
        Then: Both nodes are returned
        """
        # Given
        await client.post("/nodes", json=NODE_H100)
        await client.post("/nodes", json=NODE_L40S)

        # When
        resp = await client.get("/nodes")

        # Then
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    async def test_should_return_node_by_id(self, client):
        """
        Should return the node matching the given id.

        Given: A registered H100 node
        When: GET /nodes/gpu-h100-1 is called
        Then: 200 with correct node data
        """
        # Given
        await client.post("/nodes", json=NODE_H100)

        # When
        resp = await client.get("/nodes/gpu-h100-1")

        # Then
        assert resp.status_code == 200
        assert resp.json()["id"] == "gpu-h100-1"

    async def test_should_return_404_for_unknown_node(self, client):
        """
        Should return 404 for an unregistered node id.

        Given: No node with id unknown-node
        When: GET /nodes/unknown-node is called
        Then: 404 Not Found
        """
        # When
        resp = await client.get("/nodes/unknown-node")

        # Then
        assert resp.status_code == 404


class TestNodeDeregistration:
    """Tests for DELETE /nodes/{id}."""

    async def test_should_mark_node_as_down(self, client):
        """
        Should transition node status to down without deleting it.

        Given: An idle H100 node
        When: DELETE /nodes/gpu-h100-1 is called
        Then: Node status is down
        """
        # Given
        await client.post("/nodes", json=NODE_H100)

        # When
        resp = await client.delete("/nodes/gpu-h100-1")

        # Then
        assert resp.status_code == 200
        assert resp.json()["status"] == "down"

    async def test_should_exclude_down_node_from_allocation(self, session_factory):
        """
        Should not allocate a run to a node marked as down.

        Given: One H100 node marked as down and a queued H100 run
        When: poll_once is called
        Then: Run remains queued
        """
        # Given
        async with session_factory() as session:
            from src.models import Engine

            node = Node(id="gpu-h100-1", gpu_type=GpuType.H100, status=NodeStatus.down)
            run = Run(
                model="x",
                model_size_b=70,
                engine=Engine.vllm,
                gpu_type_required=GpuType.H100,
                scenario_path="s.yaml",
            )
            session.add_all([node, run])
            await session.commit()
            run_id = run.id

        # When
        await poll_once(session_factory)

        # Then
        async with session_factory() as session:
            run = await session.get(Run, run_id)
        assert run.status == RunStatus.queued


class TestNodeAllocation:
    """Tests for DB-backed node assignment in the polling loop."""

    async def test_should_assign_run_to_idle_matching_node(
        self, session_factory, idle_h100, queued_run
    ):
        """
        Should assign a queued run to an idle node with matching gpu_type.

        Given: One idle H100 node and one queued H100 run
        When: poll_once is called
        Then: Run is running, node is busy, current_run_id is set
        """
        # When
        await poll_once(session_factory)

        # Then
        async with session_factory() as session:
            run = await session.get(Run, queued_run)
            node = await session.get(Node, idle_h100)
        assert run.status == RunStatus.running
        assert node.status == NodeStatus.busy
        assert node.current_run_id == queued_run

    async def test_should_leave_run_queued_when_no_idle_node(
        self, session_factory, queued_run
    ):
        """
        Should not assign a run when no compatible idle node exists.

        Given: No nodes in the pool, one queued H100 run
        When: poll_once is called
        Then: Run status remains queued
        """
        # When
        await poll_once(session_factory)

        # Then
        async with session_factory() as session:
            run = await session.get(Run, queued_run)
        assert run.status == RunStatus.queued

    async def test_should_leave_run_queued_when_node_gpu_type_mismatch(
        self, session_factory, idle_l40s, queued_run
    ):
        """
        Should not assign an H100 run to an idle L40S node.

        Given: One idle L40S node and one queued H100 run
        When: poll_once is called
        Then: Run remains queued, L40S node remains idle
        """
        # When
        await poll_once(session_factory)

        # Then
        async with session_factory() as session:
            run = await session.get(Run, queued_run)
            node = await session.get(Node, idle_l40s)
        assert run.status == RunStatus.queued
        assert node.status == NodeStatus.idle

    async def test_should_not_assign_two_runs_to_same_node(
        self, session_factory, idle_h100
    ):
        """
        Should assign at most one run per node (strict isolation).

        Given: One idle H100 node and two queued H100 runs
        When: poll_once is called
        Then: One run is running, the other remains queued
        """
        # Given
        async with session_factory() as session:
            from src.models import Engine

            for i in range(2):
                session.add(
                    Run(
                        model=f"model-{i}",
                        model_size_b=70,
                        engine=Engine.vllm,
                        gpu_type_required=GpuType.H100,
                        scenario_path="s.yaml",
                    )
                )
            await session.commit()

        # When
        await poll_once(session_factory)

        # Then
        async with session_factory() as session:
            from sqlalchemy import select

            runs = (await session.execute(select(Run))).scalars().all()
        statuses = {r.status for r in runs}
        assert RunStatus.running in statuses
        assert RunStatus.queued in statuses


class TestFindIdleNode:
    """Unit tests for the find_idle_node helper."""

    async def test_should_return_idle_node_matching_gpu_type(
        self, session_factory, idle_h100
    ):
        """
        Should return the idle H100 node when run requires H100.

        Given: One idle H100 node in DB
        When: find_idle_node is called for an H100 run
        Then: The H100 node is returned
        """
        # Given
        async with session_factory() as session:
            from src.models import Engine

            run = Run(
                model="x",
                model_size_b=70,
                engine=Engine.vllm,
                gpu_type_required=GpuType.H100,
                scenario_path="s.yaml",
            )

            # When
            node = await find_idle_node(session, run)

        # Then
        assert node is not None
        assert node.id == idle_h100

    async def test_should_return_none_when_no_idle_node(
        self, session_factory, queued_run
    ):
        """
        Should return None when no idle node matches.

        Given: No nodes in DB
        When: find_idle_node is called
        Then: None is returned
        """
        # Given
        async with session_factory() as session:
            run = await session.get(Run, queued_run)

            # When
            node = await find_idle_node(session, run)

        # Then
        assert node is None
