from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_session
from src.models import Node, NodeStatus
from src.schemas import NodeCreate, NodeRead

router = APIRouter(prefix="/nodes", tags=["nodes"])


@router.post("", response_model=NodeRead, status_code=status.HTTP_201_CREATED)
async def register_node(body: NodeCreate, session: AsyncSession = Depends(get_session)):
    existing = await session.get(Node, body.id)
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="node already registered")
    node = Node(**body.model_dump())
    session.add(node)
    await session.commit()
    await session.refresh(node)
    return node


@router.get("", response_model=list[NodeRead])
async def list_nodes(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Node).order_by(Node.id))
    return result.scalars().all()


@router.get("/{node_id}", response_model=NodeRead)
async def get_node(node_id: str, session: AsyncSession = Depends(get_session)):
    node = await session.get(Node, node_id)
    if node is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="node not found")
    return node


@router.delete("/{node_id}", response_model=NodeRead)
async def deregister_node(node_id: str, session: AsyncSession = Depends(get_session)):
    node = await session.get(Node, node_id)
    if node is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="node not found")
    node.status = NodeStatus.down
    await session.commit()
    await session.refresh(node)
    return node
