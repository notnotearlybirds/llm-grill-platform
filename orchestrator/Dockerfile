FROM python:3.12-slim

WORKDIR /app

ARG TERRAFORM_VERSION=1.15.3

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl unzip ca-certificates \
    && curl -fsSL -o /tmp/terraform.zip "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip" \
    && unzip /tmp/terraform.zip -d /usr/local/bin \
    && rm /tmp/terraform.zip \
    && apt-get purge -y unzip \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY orchestrator/pyproject.toml orchestrator/uv.lock ./
RUN uv sync --frozen --no-dev

COPY orchestrator/src ./src
COPY orchestrator/alembic ./alembic
COPY orchestrator/alembic.ini ./alembic.ini
COPY orchestrator/models.yaml ./models.yaml
COPY infra/gpu-vm ./infra/gpu-vm
COPY scenarios ./scenarios

RUN useradd --system --no-create-home appuser && chown -R appuser /app
USER appuser

ENV UV_CACHE_DIR=/app/.cache/uv
# Share the Scaleway provider across per-run terraform workspaces so every
# `terraform init` doesn't re-download/extract it (saves disk + RAM under load).
ENV TF_PLUGIN_CACHE_DIR=/app/.cache/terraform-plugins
# Pre-warm the cache and pin the provider at build time. The plugin cache is
# NOT concurrency-safe: when several per-run `terraform init`s race to populate
# the same provider binary, the kernel rejects writing a file another process is
# executing (ETXTBSY → "text file busy"). Baking the exact version into the
# cache + a complete linux_amd64 lock file makes every runtime `init` read-only
# against the cache, so concurrent provisioning never writes it.
RUN mkdir -p /app/.cache/terraform-plugins \
    && terraform -chdir=/app/infra/gpu-vm providers lock -platform=linux_amd64 \
    && terraform -chdir=/app/infra/gpu-vm init -input=false -backend=false

CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
