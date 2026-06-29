import asyncio
import json
import re
import shutil
import uuid
from pathlib import Path

from loguru import logger

from src.config import settings
from src.models import GpuType, Run


class TerraformError(RuntimeError):
    """Base class for terraform-driven provisioning failures."""


class OutOfStockError(TerraformError):
    """Scaleway reports the requested instance SKU has no capacity."""


class ScalewayAuthError(TerraformError):
    """Scaleway credentials are missing or invalid."""


class ScalewayQuotaError(TerraformError):
    """Account quota exceeded for the requested resource."""


class ServerStartError(TerraformError):
    """Scaleway created the instance but it never reached `running`.

    The provider reports "expected state running but found stopped" when the
    hypervisor can't actually power on the GPU SKU — in practice a capacity
    (stock) condition surfacing at start time rather than as an explicit
    out-of-stock API error. Transient and retryable.
    """


_OUT_OF_STOCK_RE = re.compile(r"out of stock", re.IGNORECASE)
_AUTH_RE = re.compile(
    r"(access key cannot be empty|secret key cannot be empty|"
    r"invalid (?:access|secret) key|authentication failed|unauthorized)",
    re.IGNORECASE,
)
_QUOTA_RE = re.compile(r"(quota|limit).*(exceed|reach)", re.IGNORECASE)
# Provider wait failure: server created but not running (stopped/error/locked).
_SERVER_START_RE = re.compile(
    r"expected state running but found (?:stopped|error|locked)", re.IGNORECASE
)


def _classify(stderr: str) -> TerraformError:
    if _OUT_OF_STOCK_RE.search(stderr):
        return OutOfStockError(stderr.strip())
    if _AUTH_RE.search(stderr):
        return ScalewayAuthError(stderr.strip())
    if _QUOTA_RE.search(stderr):
        return ScalewayQuotaError(stderr.strip())
    if _SERVER_START_RE.search(stderr):
        return ServerStartError(stderr.strip())
    return TerraformError(stderr.strip())


def _find_repo_root() -> Path:
    """Find the ancestor that holds infra/gpu-vm/

    Works both in local dev (repo root) and in the Docker image (/app), as long
    as the Dockerfile copies `infra/gpu-vm/` as a directory.
    """
    for parent in Path(__file__).resolve().parents:
        if (parent / "infra" / "gpu-vm" / "main.tf").is_file():
            return parent
    raise RuntimeError("could not locate repo root (infra/gpu-vm/main.tf not found)")


_REPO_ROOT = _find_repo_root()
_TERRAFORM_DIR = _REPO_ROOT / "infra" / "gpu-vm"
_WORKSPACES_DIR = _TERRAFORM_DIR / "workspaces"
_SCENARIOS_ROOT = _REPO_ROOT

_IP_RE = re.compile(r"https?://(\d{1,3}(?:\.\d{1,3}){3})")


def _extract_ip(url: str) -> str | None:
    m = _IP_RE.match(url)
    return m.group(1) if m else None


_INSTANCE_TYPE = {
    GpuType.L40S: "L40S-1-48G",
    GpuType.H100: "H100-1-80G",
}


def _workspace(run_id: uuid.UUID) -> Path:
    return _WORKSPACES_DIR / str(run_id)


# Per-run state object on the shared Scaleway tfstate bucket. Keying by run_id
# means the state survives the orchestrator VM that created it, so a leftover GPU
# VM can always be destroyed
_STATE_BUCKET = "llm-grill-platform-tfstate"


def _state_key(run_id: uuid.UUID) -> str:
    return f"gpu/{run_id}.tfstate"


def _backend_config(run_id: uuid.UUID) -> list[str]:
    """`-backend-config` flags supplying the per-run key + Scaleway S3 credentials
    to the partial backend declared in infra/gpu-vm/versions.tf."""
    return [
        "-backend-config",
        f"bucket={_STATE_BUCKET}",
        "-backend-config",
        f"key={_state_key(run_id)}",
        "-backend-config",
        f"region={settings.scw_region}",
        "-backend-config",
        f"access_key={settings.scw_access_key}",
        "-backend-config",
        f"secret_key={settings.scw_secret_key}",
    ]


async def _terraform(workspace: Path, *args: str) -> str:
    cmd = ["terraform", f"-chdir={workspace}", *args]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise _classify(stderr.decode())
    return stdout.decode()


async def provision_node(run: Run) -> tuple[str, str]:
    run_id = run.id
    gpu_type = run.gpu_type_required
    workspace = _workspace(run_id)

    def _stage_workspace() -> None:
        workspace.mkdir(parents=True, exist_ok=True)
        for f in _TERRAFORM_DIR.glob("*.tf"):
            shutil.copy(f, workspace)
        shutil.copy(_TERRAFORM_DIR / "cloud-init.tpl.yaml", workspace)
        # Stage the baked, pinned lock file so the per-run `init` installs the
        # exact provider already present in the shared plugin cache instead of
        # re-resolving the version range and re-writing the cache (the ETXTBSY
        # race). Guarded: absent in local dev where the image isn't built.
        lock = _TERRAFORM_DIR / ".terraform.lock.hcl"
        if lock.exists():
            shutil.copy(lock, workspace)

    await asyncio.to_thread(_stage_workspace)

    instance_type = settings.gpu_instance_type_override or _INSTANCE_TYPE[gpu_type]

    ssh_keys = [k.strip() for k in settings.ssh_public_keys.split(",") if k.strip()]
    ssh_keys_hcl = "[" + ", ".join(f'"{k}"' for k in ssh_keys) + "]"

    admin_cidrs = [c.strip() for c in settings.admin_cidrs.split(",") if c.strip()]
    # The orchestrator VM doubles as the SSH jump host for GPU VM debugging
    # (make vm-shell ORCHESTRATOR_IP=<ip>). Its IP is resolved from
    # ORCHESTRATOR_URL, which only carries a literal IPv4 in CI deployments.
    orchestrator_ip = _extract_ip(settings.orchestrator_url)
    if orchestrator_ip and f"{orchestrator_ip}/32" not in admin_cidrs:
        admin_cidrs.append(f"{orchestrator_ip}/32")
    admin_cidrs_hcl = "[" + ", ".join(f'"{c}"' for c in admin_cidrs) + "]"

    scenario_file = (_SCENARIOS_ROOT / run.scenario_path).resolve()
    if not scenario_file.is_file():
        raise TerraformError(f"scenario file not found: {scenario_file}")
    scenario_content = (await asyncio.to_thread(scenario_file.read_text)).replace(
        "${MODEL}", run.model
    )
    # The scenario is embedded in an interpolating HCL heredoc below. Any
    # remaining ${...} / %{...} sequences (e.g. a ${ENGINE} TODO reference in a
    # comment) would be parsed as Terraform interpolation and fail. Escape them
    # to their literal forms ($${ / %%{) so HCL treats them as plain text.
    scenario_content = scenario_content.replace("${", "$${").replace("%{", "%%{")

    # Non-secret vars written to file; secrets passed via -var flags to avoid disk exposure
    var_file = workspace / "terraform.tfvars"
    docker_image = (
        settings.docker_image_vllm
        if run.engine.value == "vllm"
        else settings.docker_image_llamacpp
    )
    var_file_contents = (
        f'run_id           = "{run_id}"\n'
        f'gpu_type         = "{gpu_type.value}"\n'
        f'instance_type    = "{instance_type}"\n'
        f'orchestrator_url = "{settings.orchestrator_url}"\n'
        f'gpu_zone         = "{settings.gpu_zone}"\n'
        f"ssh_public_keys  = {ssh_keys_hcl}\n"
        f"admin_cidrs      = {admin_cidrs_hcl}\n"
        f'model            = "{run.model}"\n'
        f'engine           = "{run.engine.value}"\n'
        f'scenario_path    = "{run.scenario_path}"\n'
        f'gguf_file        = "{run.gguf_file or ""}"\n'
        f'docker_image     = "{docker_image}"\n'
        f"download_timeout_seconds = {settings.download_timeout_seconds}\n"
        f"engine_health_timeout_seconds = {settings.engine_health_timeout_seconds}\n"
        f"scenario_content = <<EOT_SCENARIO\n{scenario_content}\nEOT_SCENARIO\n"
    )
    await asyncio.to_thread(var_file.write_text, var_file_contents)

    secret_vars = [
        "-var",
        f"hf_token={settings.hf_token}",
        "-var",
        f"orchestrator_api_key={settings.api_key}",
    ]

    await _terraform(workspace, "init", "-input=false", *_backend_config(run_id))
    await _terraform(workspace, "apply", "-auto-approve", "-input=false", *secret_vars)

    output = await _terraform(workspace, "output", "-json")
    out = json.loads(output)
    instance_id: str = out["instance_id"]["value"]
    public_ip: str = out["public_ip"]["value"]
    logger.info("provisioned node {} ({}) for run {}", instance_id, public_ip, run_id)
    return instance_id, public_ip


async def destroy_node(run_id: uuid.UUID) -> None:
    workspace = _workspace(run_id)
    if not workspace.exists():
        logger.warning("workspace {} not found, skipping destroy", workspace)
        return
    secret_vars = [
        "-var",
        f"hf_token={settings.hf_token}",
        "-var",
        f"orchestrator_api_key={settings.api_key}",
    ]
    await _terraform(
        workspace, "destroy", "-auto-approve", "-input=false", *secret_vars
    )
    await asyncio.to_thread(_delete_remote_state, run_id)
    await asyncio.to_thread(shutil.rmtree, workspace)
    logger.info("destroyed node for run {}", run_id)


def _delete_remote_state(run_id: uuid.UUID) -> None:
    """Remove the per-run state object after a clean destroy so the bench.yml
    reaper only ever sees states for VMs that still need reclaiming."""
    import boto3

    client = boto3.client(
        "s3",
        endpoint_url=f"https://s3.{settings.scw_region}.scw.cloud",
        aws_access_key_id=settings.scw_access_key,
        aws_secret_access_key=settings.scw_secret_key,
        region_name=settings.scw_region,
    )
    client.delete_object(Bucket=_STATE_BUCKET, Key=_state_key(run_id))
