"""Verify that all models in the config exist on HuggingFace, and that gguf_file is present when set."""
from huggingface_hub import list_repo_files
from huggingface_hub.utils import RepositoryNotFoundError

# Inline the list to avoid importing the full orchestrator stack
MODELS = [
    ("meta-llama/Llama-3.1-8B-Instruct", None),
    ("meta-llama/Llama-3.3-70B-Instruct", None),
    ("mistralai/Mistral-7B-Instruct-v0.3", None),
    ("Qwen/Qwen2.5-7B-Instruct", None),
    ("Qwen/Qwen2.5-14B-Instruct", None),
    ("Qwen/Qwen2.5-72B-Instruct", None),
    ("microsoft/phi-4", None),
    ("mistralai/Mistral-Small-3.1-24B-Instruct-2503", None),
    ("google/gemma-3-9b-it", None),
    ("google/gemma-3-27b-it", None),
    ("deepseek-ai/DeepSeek-R1-Distill-Llama-8B", None),
    ("deepseek-ai/DeepSeek-R1-Distill-Qwen-32B", None),
    ("Qwen/QwQ-32B", None),
    ("bartowski/Llama-3.1-8B-Instruct-GGUF", "Llama-3.1-8B-Instruct-Q4_K_M.gguf"),
    ("bartowski/Qwen2.5-14B-Instruct-GGUF", "Qwen2.5-14B-Instruct-Q4_K_M.gguf"),
]

ok = 0
errors = []

for model_id, gguf_file in MODELS:
    try:
        files = set(list_repo_files(model_id))
        if gguf_file:
            if gguf_file in files:
                print(f"  OK  {model_id} :: {gguf_file}")
                ok += 1
            else:
                gguf_files = sorted(f for f in files if f.endswith(".gguf"))
                print(f"  !!  {model_id} :: {gguf_file} NOT FOUND")
                if gguf_files:
                    print(f"      available: {', '.join(gguf_files[:5])}")
                errors.append((model_id, gguf_file))
        else:
            print(f"  OK  {model_id}")
            ok += 1
    except RepositoryNotFoundError:
        print(f"  !!  {model_id} — repo not found")
        errors.append((model_id, gguf_file))

print(f"\n{ok}/{len(MODELS)} OK", end="")
if errors:
    print(f"  |  {len(errors)} errors: {[m for m, _ in errors]}")
else:
    print()
