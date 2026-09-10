# FastAPI GraphQL Playground — run every target from the repo root.
#
#   make dev        both servers in one terminal (Ctrl-C stops both)
#   make backend    API only,  http://localhost:8080/graphql
#   make frontend   UI only,   http://localhost:3000
#   make test       backend test suite
#   make test-fe    frontend test suite
#   make reset-db   REQUIRED after changing any model
#
.DEFAULT_GOAL := help
.PHONY: help dev stop backend frontend test test-fe lint lint-check fmt codegen schema reset-db install check doctor verify

BE   := backend-python
FE   := frontend

help: ## show this help
	@grep -hE '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

install: ## first-time setup (or after a fresh clone)
	cd $(BE) && uv sync
	cd $(FE) && npm install

doctor: ## verify (and silently repair) the backend venv
	@cd $(BE) && { uv run python -c "import app" && uv run pytest --version; } >/dev/null 2>&1 \
	  || { echo "  backend venv is stale - rebuilding..."; \
	       rm -rf .venv && uv sync -q && echo "  rebuilt."; }

backend: doctor ## API on :8080 with hot reload
	cd $(BE) && uv run uvicorn app.main:app --reload --port 8080

frontend: ## Next.js on :3000
	cd $(FE) && npm run dev

dev: doctor ## both servers; Ctrl-C stops both
	@echo "backend  -> http://localhost:8080/graphql"
	@echo "frontend -> http://localhost:3000"
	@echo "(if anything is ever left running: make stop)"
	@trap 'kill 0' EXIT INT TERM; \
	( cd $(BE) && exec uv run uvicorn app.main:app --reload --port 8080 ) & \
	( cd $(FE) && exec npm run dev ) & \
	wait

stop: ## force-stop whatever is listening on :8080 / :3000
	@pids=$$(lsof -ti tcp:8080 -ti tcp:3000 2>/dev/null); \
	if [ -n "$$pids" ]; then kill -9 $$pids 2>/dev/null; echo "stopped: $$pids"; \
	else echo "nothing running on :8080 or :3000"; fi

test: doctor ## backend tests
	cd $(BE) && uv run pytest -q

lint: ## format + autofix the backend
	cd $(BE) && uv run ruff format src tests && uv run ruff check src tests --fix

lint-check: ## backend lint/format, read-only (rewrites nothing) — what CI runs
	cd $(BE) && uv run ruff format --check src tests && uv run ruff check src tests

fmt: lint ## format backend + frontend — run before verify on files you just wrote
	cd $(FE) && npm run format:write

test-fe: ## frontend tests (Vitest + Testing Library, jsdom)
	cd $(FE) && npm test

check: ## frontend lint + typecheck
	cd $(FE) && npm run check

verify: ## the whole "before you say done" loop, in order
	@$(MAKE) --no-print-directory codegen
	@$(MAKE) --no-print-directory lint-check
	@$(MAKE) --no-print-directory test
	@$(MAKE) --no-print-directory check
	@$(MAKE) --no-print-directory test-fe
	@echo ""
	@echo "  verify OK - codegen, backend lint + tests, frontend lint/format/types + tests."
	@echo "  reset-db is NOT included: it drops data, and is only needed after a"
	@echo "  model change. Run it yourself, then re-run verify."

schema: ## export GraphQL SDL to frontend/schema.graphql
	cd $(BE) && uv run python -c "from app.api.graphql.schema import schema; print(schema.as_str())" > ../frontend/schema.graphql

codegen: schema ## regenerate TS types (no running server needed)
	cd $(FE) && npm run codegen

reset-db: ## drop the dev database — REQUIRED after any model change
	rm -f $(BE)/app.db $(BE)/app.db-wal $(BE)/app.db-shm
	@# SQLite keeps serving a deleted file through its open fd, so a running
	@# server would silently continue on the old database. Touching a watched
	@# .py file makes uvicorn --reload restart, which recreates and reseeds it.
	@if lsof -ti tcp:8080 >/dev/null 2>&1; then \
	  touch $(BE)/src/app/main.py; \
	  echo "dev database removed; backend was running - reload triggered (recreated + reseeded in ~1s)"; \
	else \
	  echo "dev database removed; it is recreated and reseeded on next backend start"; \
	fi
