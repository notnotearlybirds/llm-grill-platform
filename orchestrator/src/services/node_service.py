from __future__ import annotations

from fastapi import HTTPException, status

from src.models import Node, NodeStatus
from src.repositories.node_repository import NodeRepository
from src.schemas import NodeCreate


class NodeService:
    @staticmethod
    async def register(body: NodeCreate) -> Node:
        existing = await NodeRepository.get(body.id)
        if existing:
            raise HTTPException(
                status.HTTP_409_CONFLICT, detail="node already registered"
            )
        node = Node(**body.model_dump())
        return await NodeRepository.create(node)

    @staticmethod
    async def list() -> list[Node]:
        return await NodeRepository.get_all()

    @staticmethod
    async def get(node_id: str) -> Node | None:
        return await NodeRepository.get(node_id)

    @staticmethod
    async def deregister(node_id: str) -> Node:
        node = await NodeRepository.get(node_id)
        node.status = NodeStatus.down
        return await NodeRepository.save(node)
