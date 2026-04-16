"""HuggingFace Hub discovery adapter."""

from loguru import logger
from huggingface_hub import HfApi, ModelInfo

from pipeline.application.domain.types import ModelCandidate
from pipeline.application.ports.model_discovery_port import DiscoveryFilters


class HuggingFaceModelDiscoveryAdapter:
    """Wraps ``huggingface_hub.HfApi`` to surface candidate models."""

    def __init__(self, token: str | None = None) -> None:
        try:  # pragma: no cover - exercised only when lib is installed
            self._api: HfApi | None = HfApi(token=token)
        except Exception as exc:  # pragma: no cover
            logger.warning("huggingface_hub not available: {}", exc)
            self._api = None

    def discover(self, filters: DiscoveryFilters) -> list[ModelCandidate]:
        if self._api is None:
            return []
        raw = self._api.list_models(
            task=filters.task,
            sort=filters.sort,
            limit=filters.limit,
            full=True,
        )
        return [
            ModelCandidate(
                model_id=m.id or "",
                size_gb=_safetensors_size_gb(m),
                has_gguf=_has_gguf(m),
            )
            for m in raw
            if m.id
        ]


def _safetensors_size_gb(model: ModelInfo) -> float:
    siblings = model.siblings or []
    total = sum(
        s.size for s in siblings if s.rfilename.endswith(".safetensors") and s.size
    )
    return total / (1024**3) if total else 0.0


def _has_gguf(model: ModelInfo) -> bool:
    return any(s.rfilename.endswith(".gguf") for s in (model.siblings or []))
