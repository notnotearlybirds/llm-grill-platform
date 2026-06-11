"""
Tests for the nodes API.

Covers: node registration, listing, retrieval, and deregistration.
Node allocation is handled ephemerally by the orchestrator (see test_runs.py).
"""

NODE_H100 = {"id": "gpu-h100-1", "gpu_type": "H100"}
NODE_L40S = {"id": "gpu-l40s-1", "gpu_type": "L40S"}


class TestNodeRegistration:
    """Tests for POST /nodes."""

    async def test_should_register_node_with_provisioning_status(self, client):
        """
        Should persist a new node with default provisioning status.

        Given: A valid node payload
        When: POST /nodes is called
        Then: 201 with correct gpu_type and no current run
        """
        # When
        resp = await client.post("/nodes", json=NODE_H100)

        # Then
        assert resp.status_code == 201
        data = resp.json()
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

        Given: A registered H100 node
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

    async def test_should_return_404_when_deregistering_unknown_node(self, client):
        """
        Should return 404 when trying to deregister a node that does not exist.

        Given: No node with id ghost-node
        When: DELETE /nodes/ghost-node is called
        Then: 404 Not Found
        """
        # When
        resp = await client.delete("/nodes/ghost-node")

        # Then
        assert resp.status_code == 404
