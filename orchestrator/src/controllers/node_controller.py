from __future__ import annotations

from fastapi import HTTPException, status

from src.schemas import NodeCreate, NodeRead
from src.services.node_service import NodeService


class NodeController:
    @staticmethod
    async def register(body: NodeCreate) -> NodeRead:
        node = await NodeService.register(body)
        return NodeRead.model_validate(node)

    @staticmethod
    async def list() -> list[NodeRead]:
        nodes = await NodeService.list()
        return [NodeRead.model_validate(n) for n in nodes]

    @staticmethod
    async def get(node_id: str) -> NodeRead:
        node = await NodeService.get(node_id)
        if node is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="node not found")
        return NodeRead.model_validate(node)

    @staticmethod
    async def deregister(node_id: str) -> NodeRead:
        node = await NodeService.get(node_id)
        if node is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="node not found")
        node = await NodeService.deregister(node_id)
        return NodeRead.model_validate(node)
