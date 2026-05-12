"""Integration tests: verify every entry in models.yaml exists on HuggingFace."""

import pytest
from huggingface_hub import list_repo_files
from huggingface_hub.utils import RepositoryNotFoundError

from src.models import Engine
from src.services.bench_service import ModelEntry, _load_models


@pytest.mark.integration
@pytest.mark.parametrize("entry", _load_models(), ids=lambda e: e.model)
def test_model_repo_exists_and_gguf_file_present(entry: ModelEntry):
    """Given a model entry from models.yaml, the HF repo must exist and gguf_file (if set) must be present."""
    try:
        files = set(list_repo_files(entry.model))
    except RepositoryNotFoundError:
        pytest.fail(f"Repo not found on HuggingFace: {entry.model}")

    if entry.engine == Engine.llamacpp:
        assert entry.gguf_file is not None, (
            f"{entry.model}: llamacpp entry must specify gguf_file"
        )

    if entry.gguf_file is not None:
        gguf_files = sorted(f for f in files if f.endswith(".gguf"))
        assert entry.gguf_file in files, (
            f"{entry.model}: gguf_file '{entry.gguf_file}' not found in repo.\n"
            f"Available GGUF files: {gguf_files[:10]}"
        )
