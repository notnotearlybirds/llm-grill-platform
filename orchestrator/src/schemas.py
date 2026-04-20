import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from src.models import Engine, GpuType, NodeStatus, RunStatus


class RunCreate(BaseModel):
    model: str
    model_size_b: int = Field(gt=0, description="Model size in billions of parameters")
    engine: Engine
    scenario_path: str


class RunRead(BaseModel):
    id: uuid.UUID
    status: RunStatus
    model: str
    model_size_b: int
    engine: Engine
    gpu_type_required: GpuType
    gpu_count: int
    scenario_path: str
    created_at: datetime
    started_at: datetime | None
    ended_at: datetime | None

    model_config = {"from_attributes": True}


class NodeCreate(BaseModel):
    id: str
    gpu_type: GpuType
    gpu_count: int = Field(default=1, gt=0)


class NodeRead(BaseModel):
    id: str
    gpu_type: GpuType
    gpu_count: int
    status: NodeStatus
    current_run_id: uuid.UUID | None

    model_config = {"from_attributes": True}
