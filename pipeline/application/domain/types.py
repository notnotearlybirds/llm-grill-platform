"""Domain value objects for the pipeline."""

from typing import Literal

from pydantic import BaseModel

Backend = Literal["vllm", "llamacpp"]
ModelStatus = Literal[
    "success", "partial", "infra_failed", "unknown_error", "destroy_failed"
]


class ModelCandidate(BaseModel, frozen=True):
    model_id: str
    size_gb: float
    has_gguf: bool

    @property
    def slug(self) -> str:
        return self.model_id.replace("/", "--")

    def eligible_backends(self, configured: list[Backend]) -> list[Backend]:
        return [b for b in configured if not (b == "llamacpp" and not self.has_gguf)]


class BackendOutcome(BaseModel):
    backend: str
    success: bool
    error: str | None = None


class ModelRunResult(BaseModel):
    model_id: str
    status: ModelStatus
    backends: list[BackendOutcome] = []
    error: str | None = None
