"""Pydantic model for pipeline/config.yaml."""

from pydantic import BaseModel

from pipeline.application.domain.types import Backend, DiscoveryFiltersConfig


class LoadConfig(BaseModel):
    max_models_per_day: int
    iterations_per_conversation: int
    per_backend_timeout_s: float


class PipelineConfig(BaseModel):
    discovery: DiscoveryFiltersConfig
    backends: list[Backend]
    load: LoadConfig
