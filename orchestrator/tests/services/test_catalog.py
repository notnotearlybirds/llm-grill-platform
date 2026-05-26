"""Tests for catalog derivation — models.json and scenarios.json builders."""

from typing import Literal

import pytest

from src.catalog import build_models_catalog, build_scenarios_catalog
from src.services.bench_service import ModelEntry


def _entry(
    model: str,
    engine: Literal["vllm", "llamacpp"] = "vllm",
    size_b: int = 8,
    gguf_file: str | None = None,
    categories: list[str] | None = None,
) -> ModelEntry:
    return ModelEntry(
        model=model,
        engine=engine,
        size_b=size_b,
        gguf_file=gguf_file,
        categories=categories,
    )


class TestBuildModelsCatalog:
    """build_models_catalog() derives editorial metadata, no hand-maintained fields."""

    def test_should_derive_brand_and_params_from_id_and_size(self):
        """
        Given: a vLLM entry "Qwen/Qwen2.5-14B-Instruct" of size 14
        When: the models catalog is built
        Then: brand is the HF org, params_b is size_b, quantization is null
        """
        catalog = build_models_catalog([_entry("Qwen/Qwen2.5-14B-Instruct", size_b=14)])

        assert catalog == [
            {
                "model": "Qwen/Qwen2.5-14B-Instruct",
                "engine": "vllm",
                "display_name": "Qwen2.5 14B",
                "brand": "Qwen",
                "params_b": 14,
                "quantization": None,
                "categories": ["Dense"],
                "scenario": "scenarios/ramp.yaml",
            }
        ]

    def test_should_parse_quantization_from_gguf_filename(self):
        """
        Given: a llamacpp entry with a Q4_K_M GGUF file
        When: the models catalog is built
        Then: quantization is parsed from the filename
        """
        catalog = build_models_catalog(
            [
                _entry(
                    "bartowski/Qwen2.5-14B-Instruct-GGUF",
                    engine="llamacpp",
                    gguf_file="Qwen2.5-14B-Instruct-Q4_K_M.gguf",
                )
            ]
        )

        assert catalog[0]["quantization"] == "Q4_K_M"


class TestDisplayName:
    """display_name is derived from the HF id (strip org + instruct/format suffixes)."""

    @pytest.mark.parametrize(
        "model, expected",
        [
            ("Qwen/Qwen2.5-14B-Instruct", "Qwen2.5 14B"),
            ("meta-llama/Llama-3.1-8B-Instruct", "Llama 3.1 8B"),
            ("mistralai/Mixtral-8x7B-Instruct-v0.1", "Mixtral 8x7B"),
            ("google/gemma-2-27b-it", "gemma 2 27b"),
            ("bartowski/Qwen2.5-14B-Instruct-GGUF", "Qwen2.5 14B"),
            ("meta-llama/Llama-3.1-8B-Base", "Llama 3.1 8B Base"),
            ("org/model-v0.3-Instruct", "model"),  # version token + noise stripped
            ("org/Gemma_2_27b_it", "Gemma 2 27b"),  # underscores + lowercase noise
            ("org/MODEL-IT", "MODEL"),  # case-insensitive noise
        ],
    )
    def test_should_derive_readable_name(self, model, expected):
        """Given an HF id, When the catalog is built, Then display_name is cleaned."""
        catalog = build_models_catalog([_entry(model)])
        assert catalog[0]["display_name"] == expected

    def test_should_fall_back_to_segment_when_fully_stripped(self):
        """Given a name that is all noise tokens, Then keep the raw segment."""
        catalog = build_models_catalog([_entry("x/Instruct")])
        assert catalog[0]["display_name"] == "Instruct"


class TestCategories:
    """categories: declared in models.yaml (default Dense) + automatic Quantized."""

    def test_should_use_editorial_categories_when_provided(self):
        """Given explicit categories, When built, Then they pass through verbatim."""
        catalog = build_models_catalog(
            [_entry("x/Custom-Model", categories=["Reasoning", "MoE"])]
        )
        assert catalog[0]["categories"] == ["Reasoning", "MoE"]

    def test_should_default_to_dense_when_omitted(self):
        """Given no categories, When built, Then defaults to ["Dense"] (no guessing)."""
        catalog = build_models_catalog([_entry("mistralai/Mixtral-8x7B-Instruct")])
        assert catalog[0]["categories"] == ["Dense"]

    def test_should_append_quantized_even_to_editorial_categories(self):
        """Given editorial tags + a GGUF file, Then Quantized is still appended."""
        catalog = build_models_catalog(
            [
                _entry(
                    "x/Custom-Model",
                    engine="llamacpp",
                    gguf_file="Custom-Q4_K_M.gguf",
                    categories=["Reasoning"],
                )
            ]
        )
        assert catalog[0]["categories"] == ["Reasoning", "Quantized"]

    def test_should_tag_quantized_on_default_dense_for_gguf(self):
        """Given a GGUF entry with no editorial tags, Then ["Dense", "Quantized"]."""
        catalog = build_models_catalog(
            [
                _entry(
                    "bartowski/Qwen2.5-14B-Instruct-GGUF",
                    engine="llamacpp",
                    gguf_file="Qwen2.5-14B-Instruct-Q4_K_M.gguf",
                )
            ]
        )
        assert catalog[0]["categories"] == ["Dense", "Quantized"]


class TestBuildScenariosCatalog:
    """build_scenarios_catalog() summarizes referenced scenario YAMLs."""

    def test_should_summarize_scenario_load_shape(self, tmp_path):
        """
        Given: a scenarios/ramp.yaml under the root
        When: the scenarios catalog is built
        Then: a summary is returned with the load shape and first user prompt
        """
        (tmp_path / "scenarios").mkdir()
        (tmp_path / "scenarios" / "ramp.yaml").write_text(
            "name: ramp\n"
            "description: |\n  Ramp test.\n"
            "models:\n  - name: m\n    max_tokens: 256\n"
            "conversations:\n  - name: c\n    turns:\n"
            "      - role: user\n        content: Hello?\n"
            "load:\n  ramp_levels: [1, 4, 64]\n  iterations: 2\n"
        )

        catalog = build_scenarios_catalog(tmp_path)

        assert catalog == [
            {
                "path": "scenarios/ramp.yaml",
                "name": "ramp",
                "description": "Ramp test.",
                "concurrency_levels": [1, 4, 64],
                "iterations": 2,
                "max_tokens": 256,
                "prompt": "Hello?",
            }
        ]

    def test_should_discover_all_scenarios_sorted(self, tmp_path):
        """
        Given: two scenario files in the scenarios/ directory
        When: the scenarios catalog is built
        Then: both are discovered, sorted by filename, regardless of model refs
        """
        (tmp_path / "scenarios").mkdir()
        (tmp_path / "scenarios" / "ramp.yaml").write_text("name: ramp\n")
        (tmp_path / "scenarios" / "burst.yaml").write_text("name: burst\n")

        catalog = build_scenarios_catalog(tmp_path)

        assert [s["name"] for s in catalog] == ["burst", "ramp"]

    def test_should_return_empty_when_no_scenarios_dir(self, tmp_path):
        """
        Given: a root with no scenarios/ directory
        When: the scenarios catalog is built
        Then: an empty list is returned rather than raising
        """
        assert build_scenarios_catalog(tmp_path) == []

    def test_should_take_max_tokens_from_first_model_that_declares_it(self, tmp_path):
        """
        Should scan models in order and return the first declared max_tokens,
        skipping earlier entries that omit the key.

        Given: a scenario whose first model has no max_tokens, second has 512
        When: the scenarios catalog is built
        Then: max_tokens is 512 (the first one that actually declares it)
        """
        (tmp_path / "scenarios").mkdir()
        (tmp_path / "scenarios" / "ramp.yaml").write_text(
            "name: ramp\n"
            "models:\n"
            "  - name: no-cap\n"
            "  - name: capped\n    max_tokens: 512\n"
        )

        catalog = build_scenarios_catalog(tmp_path)

        assert catalog[0]["max_tokens"] == 512

    def test_should_have_null_max_tokens_when_no_model_declares_it(self, tmp_path):
        """
        Should return null max_tokens (not crash) when no model carries the key.

        Given: a scenario whose only model omits max_tokens
        When: the scenarios catalog is built
        Then: max_tokens is None
        """
        (tmp_path / "scenarios").mkdir()
        (tmp_path / "scenarios" / "ramp.yaml").write_text(
            "name: ramp\nmodels:\n  - name: uncapped\n"
        )

        catalog = build_scenarios_catalog(tmp_path)

        assert catalog[0]["max_tokens"] is None

    def test_should_skip_malformed_scenario_keep_valid_ones(self, tmp_path):
        """
        Given: one valid scenario and one with a top-level list (not a mapping)
        When: the scenarios catalog is built
        Then: the malformed file is skipped, the valid one still published
        """
        (tmp_path / "scenarios").mkdir()
        (tmp_path / "scenarios" / "ramp.yaml").write_text("name: ramp\n")
        (tmp_path / "scenarios" / "broken.yaml").write_text("- just\n- a\n- list\n")

        catalog = build_scenarios_catalog(tmp_path)

        assert [s["name"] for s in catalog] == ["ramp"]
