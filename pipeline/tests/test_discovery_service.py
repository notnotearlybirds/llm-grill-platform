from __future__ import annotations

from pipeline.adapters.storage.filesystem_results_repository import (
    InMemoryResultsRepository,
)
from pipeline.application.domain.types import ModelCandidate
from pipeline.application.services.discovery_service import (
    DiscoveryFiltersConfig,
    DiscoveryService,
)


class _FakeDiscovery:
    def __init__(self, models: list[ModelCandidate]) -> None:
        self.models = models

    def discover(self, _filters) -> list[ModelCandidate]:
        return self.models


def _filters(**overrides) -> DiscoveryFiltersConfig:
    base = dict(
        task="text-generation",
        sort="trending",
        max_size_gb=75.0,
        limit=50,
        include_patterns=["*instruct*"],
        exclude_patterns=[],
        exclude_models=[],
    )
    base.update(overrides)
    return DiscoveryFiltersConfig(**base)


def test_plan_given_matching_candidates_when_filtered_then_returns_eligible():
    # Given
    models = [
        ModelCandidate("meta-llama/Llama-3.1-8B-Instruct", 15.0, True),
        ModelCandidate("some-org/pretraining-raw", 10.0, False),  # no instruct
        ModelCandidate("too-big/Big-Instruct", 120.0, True),  # over size
        ModelCandidate("excluded/Excluded-Instruct", 5.0, True),
    ]
    repo = InMemoryResultsRepository()
    service = DiscoveryService(_FakeDiscovery(models), repo)

    # When
    plan = service.plan(
        _filters(exclude_models=["excluded/Excluded-Instruct"]),
        ["vllm", "llamacpp"],
        date="2026-04-14",
    )

    # Then
    assert [r.model.model_id for r in plan] == ["meta-llama/Llama-3.1-8B-Instruct"]
    assert plan[0].pending_backends == ["vllm", "llamacpp"]


def test_plan_given_model_without_gguf_when_planned_then_drops_llamacpp():
    # Given
    models = [ModelCandidate("org/Model-Instruct", 5.0, has_gguf=False)]
    service = DiscoveryService(_FakeDiscovery(models), InMemoryResultsRepository())

    # When
    plan = service.plan(_filters(), ["vllm", "llamacpp"], date="2026-04-14")

    # Then
    assert plan[0].pending_backends == ["vllm"]


def test_plan_given_already_benchmarked_pair_when_planned_then_skips_it():
    # Given
    models = [ModelCandidate("org/Model-Instruct", 5.0, has_gguf=True)]
    repo = InMemoryResultsRepository()
    repo.write_jsonl("2026-04-14", "org--Model-Instruct", "vllm", [{"success": True}])
    service = DiscoveryService(_FakeDiscovery(models), repo)

    # When
    plan = service.plan(_filters(), ["vllm", "llamacpp"], date="2026-04-14")

    # Then: only llamacpp remains pending
    assert plan[0].pending_backends == ["llamacpp"]


def test_plan_given_all_backends_benchmarked_when_planned_then_drops_model_entirely():
    # Given
    models = [ModelCandidate("org/Model-Instruct", 5.0, has_gguf=True)]
    repo = InMemoryResultsRepository()
    repo.write_jsonl("2026-04-14", "org--Model-Instruct", "vllm", [])
    repo.write_jsonl("2026-04-14", "org--Model-Instruct", "llamacpp", [])
    service = DiscoveryService(_FakeDiscovery(models), repo)

    # When
    plan = service.plan(_filters(), ["vllm", "llamacpp"], date="2026-04-14")

    # Then
    assert plan == []
