import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.db import AsyncSessionLocal, engine
from src.models import Base
from src.orchestrator import polling_loop
from src.routers.nodes import router as nodes_router
from src.routers.runs import router as runs_router

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    task = asyncio.create_task(polling_loop(AsyncSessionLocal))
    yield
    task.cancel()
    await engine.dispose()


app = FastAPI(title="llm-grill orchestrator", lifespan=lifespan)
app.include_router(runs_router)
app.include_router(nodes_router)
