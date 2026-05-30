.SILENT:
.DEFAULT_GOAL: help

help:
	echo "Please use \`make \033[36m<target>\033[0m\`"
	echo "\t where \033[36m<target>\033[0m is one of"
	grep -E '^\.PHONY: [a-zA-Z_-]+ .*?## .*$$' $(MAKEFILE_LIST) \
		| sort | awk 'BEGIN {FS = "(: |##)"}; {printf "• \033[36m%-30s\033[0m %s\n", $$2, $$3}'

.PHONY: setup ## 📦 Install node dependencies (npm ci)
setup:
	npm ci

.PHONY: dev ## 🚀 Run the dev server (uses static/sample/ unless VITE_DATA_BASE_URL is set)
dev:
	npm run dev

.PHONY: build ## 🏗  Build the static site into build/
build:
	npm run build

.PHONY: preview ## 👀 Serve the production build locally
preview:
	npm run preview

.PHONY: check ## 🕵 Type-check (svelte-check)
check:
	npm run check

.PHONY: sample ## 🎲 Regenerate dev fixtures in static/sample/
sample:
	node scripts/gen-sample.mjs

.PHONY: clean ## 💣 Remove build artifacts and node_modules
clean:
	rm -rf build .svelte-kit node_modules
