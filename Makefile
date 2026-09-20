.PHONY: setup up down check-setup gt-inspect inspect ingest ask test lint check

setup:
	uv sync
	cp -n .env.example .env || true
	@echo "Now edit .env: set OPENAI_API_KEY and GROUND_TRUTH_DIR"

up:
	docker compose up -d
	@sleep 3
	@curl -sf http://localhost:6333/healthz && echo "\nqdrant: ok"

down:
	docker compose down

check-setup:
	uv run python -m eval.check_setup

gt-inspect:
	uv run python -m eval.inspect_ground_truth

inspect:
	uv run python scripts/inspect_parse.py

ingest:
	uv run python scripts/ingest_one.py

ask:
	uv run python scripts/ask.py

test:
	uv run pytest -q

lint:
	uv run ruff check .

check: test lint
