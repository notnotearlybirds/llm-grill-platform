"""Shared fixtures for the orchestrator test suite."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.db import get_session
from src.main import app
from src.models import Base, Engine, GpuType, Node, Run

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def session_factory():
    """In-memory SQLite session factory — no real Postgres needed."""
    engine = create_async_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()


@pytest.fixture
async def client(session_factory):
    """AsyncClient wired to an in-memory DB via dependency override."""

    async def override_get_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
async def idle_h100(session_factory):
    """A persisted idle H100 node."""
    async with session_factory() as session:
        node = Node(id="gpu-h100-1", gpu_type=GpuType.H100, gpu_count=1)
        session.add(node)
        await session.commit()
        return node.id


@pytest.fixture
async def idle_l40s(session_factory):
    """A persisted idle L40S node."""
    async with session_factory() as session:
        node = Node(id="gpu-l40s-1", gpu_type=GpuType.L40S, gpu_count=1)
        session.add(node)
        await session.commit()
        return node.id


@pytest.fixture
async def queued_run(session_factory):
    """A persisted queued run targeting an H100 node (70B model)."""
    async with session_factory() as session:
        run = Run(
            model="test/model",
            model_size_b=70,
            engine=Engine.vllm,
            gpu_type_required=GpuType.H100,
            scenario_path="scenarios/basic.yaml",
        )
        session.add(run)
        await session.commit()
        return run.id
