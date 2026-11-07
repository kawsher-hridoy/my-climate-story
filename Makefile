.PHONY: setup data db api web worker build test validate
setup:
	uv sync --extra dev
	npm ci
data:
	uv run climate ingest
	uv run climate build
db:
	docker compose -f infra/compose.dev.yml up -d --wait
	uv run climate migrate
	uv run climate queue-schema
	uv run climate seed
api:
	uv run uvicorn climate.main:app --host 127.0.0.1 --port 8000 --no-access-log
web:
	npm run dev
worker:
	uv run climate worker
build:
	npm run build
test:
	uv run pytest
	npm test
validate:
	uv run climate validate
