import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class RunStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    done = "done"
    failed = "failed"


class NodeStatus(str, enum.Enum):
    idle = "idle"
    busy = "busy"
    down = "down"


class Engine(str, enum.Enum):
    vllm = "vllm"
    llamacpp = "llamacpp"


class GpuType(str, enum.Enum):
    L40S = "L40S"
    H100 = "H100"


class Node(Base):
    __tablename__ = "nodes"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    gpu_type: Mapped[GpuType] = mapped_column(Enum(GpuType), nullable=False)
    gpu_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[NodeStatus] = mapped_column(
        Enum(NodeStatus), nullable=False, default=NodeStatus.idle
    )
    current_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    status: Mapped[RunStatus] = mapped_column(
        Enum(RunStatus), nullable=False, default=RunStatus.queued
    )
    model: Mapped[str] = mapped_column(String, nullable=False)
    model_size_b: Mapped[int] = mapped_column(Integer, nullable=False)
    engine: Mapped[Engine] = mapped_column(Enum(Engine), nullable=False)
    gpu_type_required: Mapped[GpuType] = mapped_column(Enum(GpuType), nullable=False)
    gpu_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    scenario_path: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
