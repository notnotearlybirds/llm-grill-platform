.SILENT:
.DEFAULT_GOAL: help

help:
	echo "Please use \`make \033[36m<target>\033[0m\`"
	echo "\t where \033[36m<target>\033[0m is one of"
	grep -E '^\.PHONY: [a-zA-Z_-]+ .*?## .*$$' $(MAKEFILE_LIST) \
		| sort | awk 'BEGIN {FS = "(: |##)"}; {printf "• \033[36m%-30s\033[0m %s\n", $$2, $$3}'

.PHONY: up ## 🚀 Start all services with migrations
up:
	docker-compose -f docker-compose.yaml -f docker-compose.with-migrations.yaml up --build --force-recreate -d

.PHONY: up-dev ## 🛠️  Start without rebuilding (no migrations)
up-dev:
	docker-compose up -d

.PHONY: up-debug ## 🔍 Start in foreground with logs
up-debug:
	docker-compose -f docker-compose.yaml -f docker-compose.with-migrations.yaml up --build --force-recreate

.PHONY: down ## 📉 Stop all services
down:
	docker-compose down

.PHONY: logs ## 📋 Follow orchestrator logs
logs:
	docker-compose logs -f orchestrator

.PHONY: migrate ## 🗄️  Run Alembic migrations manually
migrate:
	cd orchestrator && uv run alembic upgrade head
