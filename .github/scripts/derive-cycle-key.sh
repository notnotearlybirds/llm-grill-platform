#!/usr/bin/env bash
# Per-cycle orchestrator API key: sha256(<repo API_KEY secret>:<run id>:<run attempt>).
#
# The key crosses the public internet in cleartext (X-API-Key over plain HTTP to
# the orchestrator VM), so it must be worthless once the cycle's VM is destroyed.
# Each job that needs it re-derives it with this script: GitHub drops masked job
# outputs, so the value cannot be passed between jobs.
set -euo pipefail
: "${API_KEY_SEED:?API_KEY_SEED must be set}"
printf '%s' "${API_KEY_SEED}:${GITHUB_RUN_ID}:${GITHUB_RUN_ATTEMPT}" | sha256sum | cut -d' ' -f1
