.PHONY: up down build test lint format format-check ci logs shell db-shell

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose up -d --build

test:
	docker compose exec api python -m pytest -q

lint:
	docker compose exec api ruff check .

format:
	docker compose exec api ruff format .
	docker compose exec api ruff check . --fix

format-check:
	docker compose exec api ruff format --check .
	docker compose exec api ruff check .

ci:
	docker compose exec api ruff check .
	docker compose exec api ruff format --check .
	docker compose exec api python -m pytest -q

logs:
	docker compose logs -f

shell:
	docker compose exec api sh

db-shell:
	docker compose exec db sh -lc 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'

migrate:
	docker compose exec api alembic upgrade head

migrate-test:
	docker compose exec db sh -lc 'dropdb -U "$$POSTGRES_USER" task_tracker_test || true'
	docker compose exec db sh -lc 'createdb -U "$$POSTGRES_USER" task_tracker_test'
	docker compose exec api sh -lc 'DATABASE_URL="$$TEST_DATABASE_URL" alembic upgrade head'
