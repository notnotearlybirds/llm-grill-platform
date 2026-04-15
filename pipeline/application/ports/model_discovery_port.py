"""Port describing HuggingFace-style model discovery."""

from __future__ import annotations

from typing import Protocol

from pipeline.application.domain.types import ModelCandidate


class DiscoveryFilters(Protocol):
    task: str
    sort: str
    max_size_gb: float
    limit: int
    include_patterns: list[str]
    exclude_patterns: list[str]
    exclude_models: list[str]


class ModelDiscoveryPort(Protocol):
    """Discover candidate models from an external catalog."""

    def discover(self, filters: DiscoveryFilters) -> list[ModelCandidate]: ...
