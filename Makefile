.SILENT:
.DEFAULT_GOAL := help

help:
	echo "Please use \`make \033[36m<target>\033[0m\`"
	echo "\t where \033[36m<target>\033[0m is one of"
	grep -E '^\.PHONY: [a-zA-Z_-]+ .*?## .*$$' $(MAKEFILE_LIST) \
		| sort | awk 'BEGIN {FS = "(: |##)"}; {printf "• \033[36m%-30s\033[0m %s\n", $$2, $$3}'

# ==============================================================================
# SETUP
# ==============================================================================

.PHONY: install ## 📦 Install pipeline dependencies (Python)
install:
	uv sync --all-extras

.PHONY: install-site ## 📦 Install site dependencies (Node)
install-site:
	cd site && npm ci

# ==============================================================================
# CODE QUALITY
# ==============================================================================

.PHONY: lint ## 🔎 Auto-fix lint issues & format with ruff
lint:
	uv run ruff check . --fix
	uv run ruff format .

.PHONY: check ## 🔎 Check code quality with ruff (no fix)
check:
	uv run ruff check .

# ==============================================================================
# TESTING
# ==============================================================================

.PHONY: tests ## 🧪 Run pipeline tests
tests:
	uv run pytest pipeline/tests --cov=pipeline --cov-fail-under=80

# ==============================================================================
# PIPELINE
# ==============================================================================

.PHONY: run-dry ## 🧪 Run the pipeline against fixtures, no provisioning
run-dry:
	uv run python -m pipeline.run --dry-run

.PHONY: run ## 🚀 Run the full nightly pipeline (provisions H100s)
run:
	uv run python -m pipeline.run

.PHONY: aggregate ## 📊 Aggregate raw JSONL into results/aggregated/
aggregate:
	uv run python -m pipeline.aggregate

.PHONY: sweep ## 🧹 Destroy orphan Scaleway instances (>2h old)
sweep:
	uv run python -m pipeline.sweep

# ==============================================================================
# SITE
# ==============================================================================

.PHONY: site-dev ## 🌐 Serve the site locally
site-dev:
	cd site && npm run dev

.PHONY: site-build ## 🏗️  Build the static site
site-build:
	cd site && npm run build
