"""
Tests for orchestrator logic: release_node and poll_once.

Covers: node teardown after run completion, queued-run polling,
and error handling when destroy or poll fails.
"""

import uuid

from src.models import Engine, GpuType, Node, NodeStatus, Run, RunStatus
from src.orchestrator import poll_once, release_node


async def _create_run_with_node(
    session_factory, run_id: uuid.UUID | None = None
) -> uuid.UUID:
    async with session_factory() as session:
        run = Run(
            model="meta-llama/Llama-3-8B",
            model_size_b=8,
            engine=Engine.vllm,
            gpu_type_required=GpuType.L40S,
            scenario_path="scenarios/basic.yaml",
            status=RunStatus.running,
        )
        if run_id:
            run.id = run_id
        session.add(run)
        await session.flush()
        node = Node(
            id=f"node-{run.id}",
            gpu_type=GpuType.L40S,
            status=NodeStatus.busy,
            current_run_id=run.id,
        )
        session.add(node)
        await session.commit()
        return run.id


class TestReleaseNode:
    """Tests for release_node — destroy ephemeral node after a run ends."""

    async def test_should_mark_node_down_after_destroy(self, session_factory, mocker):
        """
        Should call destroy_node and set node status to down.

        Given: A running run with an associated busy node
        When: release_node is called
        Then: Node status is down
        """
        # Given
        mocker.patch("src.orchestrator.destroy_node", return_value=None)
        run_id = await _create_run_with_node(session_factory)

        # When
        await release_node(run_id)

        # Then
        async with session_factory() as session:
            node = await session.get(Node, f"node-{run_id}")
        assert node.status == NodeStatus.down

    async def test_should_not_raise_when_destroy_fails(self, session_factory, mocker):
        """
        Should swallow destroy errors and still mark the node down.

        Given: destroy_node raises a RuntimeError
        When: release_node is called
        Then: No exception propagates, node is still marked down
        """
        # Given
        mocker.patch(
            "src.orchestrator.destroy_node", side_effect=RuntimeError("timeout")
        )
        run_id = await _create_run_with_node(session_factory)

        # When (should not raise)
        await release_node(run_id)

        # Then
        async with session_factory() as session:
            node = await session.get(Node, f"node-{run_id}")
        assert node.status == NodeStatus.down

    async def test_should_do_nothing_when_no_node_found(self, session_factory, mocker):
        """
        Should not fail when there is no node associated with the run.

        Given: A run_id with no matching node
        When: release_node is called
        Then: No exception is raised
        """
        # Given
        mocker.patch("src.orchestrator.destroy_node", return_value=None)
        run_id = uuid.uuid4()

        # When / Then (no exception)
        await release_node(run_id)


class TestPollOnce:
    """Tests for poll_once — pick up queued runs and spawn provisioning tasks."""

    async def test_should_create_task_for_each_queued_run(
        self, session_factory, mocker
    ):
        """
        Should spawn one task per queued run found.

        Given: Two queued runs in the DB
        When: poll_once is called
        Then: handle_queued_run is called twice
        """
        # Given
        async with session_factory() as session:
            for _ in range(2):
                session.add(
                    Run(
                        model="meta-llama/Llama-3-8B",
                        model_size_b=8,
                        engine=Engine.vllm,
                        gpu_type_required=GpuType.L40S,
                        scenario_path="scenarios/basic.yaml",
                        status=RunStatus.queued,
                    )
                )
            await session.commit()

        async def _noop(session, run):
            pass

        mock_handle = mocker.patch(
            "src.orchestrator.handle_queued_run", side_effect=_noop
        )

        # When
        await poll_once()

        # Then
        assert mock_handle.call_count == 2

    async def test_should_not_create_task_when_no_queued_runs(
        self, session_factory, mocker
    ):
        """
        Should not spawn any task when there are no queued runs.

        Given: Empty DB
        When: poll_once is called
        Then: handle_queued_run is not called
        """

        # Given
        async def _noop(session, run):
            pass

        mock_handle = mocker.patch(
            "src.orchestrator.handle_queued_run", side_effect=_noop
        )

        # When
        await poll_once()

        # Then
        mock_handle.assert_not_called()
