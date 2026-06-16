from pathlib import Path

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _find_repo_root() -> Path:
    """Ancestor holding infra/gpu-vm/main.tf — repo root in dev and /app in Docker.

    Mirrors infra.terraform._find_repo_root; scenarios/ lives at this root.
    """
    for parent in Path(__file__).resolve().parents:
        if (parent / "infra" / "gpu-vm" / "main.tf").is_file():
            return parent
    return Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = ""
    postgres_user: str = "postgres"
    postgres_password: str = ""
    postgres_host: str = "localhost"
    postgres_db: str = "llmgrill"

    poll_interval_seconds: int = 10
    provision_max_attempts: int = 30
    # SSH public keys (comma-separated) injected on provisioned GPU VMs for debug access.
    ssh_public_keys: str = ""
    # CIDRs (comma-separated) allowed to SSH into GPU VMs. Empty = all inbound dropped.
    admin_cidrs: str = ""
    # Force-destroy a node if its run stays in "running" longer than this (minutes).
    run_running_timeout_minutes: int = 60
    # Fail a run if it stays in "provisioning" longer than this (minutes).
    run_provisioning_timeout_minutes: int = 30
    # Max live GPUs per type (= the Scaleway project quota). The poll loop never
    # claims more runs of a type than (quota - currently live), so it never asks
    # Scaleway for capacity we can't have. Excess runs wait in `queued` until a
    # slot frees — no retries burned, no false "quota exceeded" failures.
    gpu_quota_h100: int = 2
    gpu_quota_l40s: int = 2

    @model_validator(mode="after")
    def build_database_url(self) -> "Settings":
        if not self.database_url:
            self.database_url = (
                f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
                f"@{self.postgres_host}/{self.postgres_db}"
            )
        return self

    # Terraform / Scaleway
    orchestrator_url: str = "http://localhost:8000"
    hf_token: str = ""
    gpu_zone: str = "fr-par-2"
    # Debug only: force one instance type for every GPU VM (e.g. L4-1-24G on a
    # throwaway branch). Must stay "" on main — a non-empty value sends every
    # CI bench to that SKU and mislabels results in the leaderboard.
    gpu_instance_type_override: str = ""
    # Docker image URIs for GPU runner containers
    docker_image_vllm: str = "ghcr.io/notnotearlybirds/llmgrill-runner-vllm:latest"
    docker_image_llamacpp: str = "ghcr.io/notnotearlybirds/llmgrill-runner-llamacpp:latest"
    # Maximum seconds to wait for a model download before aborting the run.
    download_timeout_seconds: int = 1800

    # Scaleway Object Storage
    scw_bucket: str = "llm-grill-platform"
    scw_region: str = "fr-par"
    scw_access_key: str = ""
    scw_secret_key: str = ""
    api_key: str
    debug: bool = False

    # Model list (deployed alongside the orchestrator)
    models_file: Path = Path(__file__).resolve().parents[1] / "models.yaml"
    # Repo root holding scenarios/ (scenario_path values are relative to it).
    scenarios_root: Path = _find_repo_root()

    @field_validator("api_key")
    @classmethod
    def api_key_must_be_set(cls, v: str) -> str:
        if not v:
            raise ValueError("API_KEY must be set")
        return v


settings = Settings()  # ty: ignore[missing-argument]
