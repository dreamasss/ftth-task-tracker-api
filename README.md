[![Tests](https://github.com/dreamasss/ftth-task-tracker-api/actions/workflows/tests.yml/badge.svg)](https://github.com/dreamasss/ftth-task-tracker-api/actions/workflows/tests.yml)

# FTTH Task Tracker API

Small FastAPI + PostgreSQL backend for tracking FTTH/telecom work sites, statuses, and site history events.

## Current features

- Create, list, get, update, and delete sites
- Validate site statuses
- Filter sites by status
- Site status statistics
- Add events and notes to sites
- Automatically create a status_change event when a site's status changes
- Dockerized API and PostgreSQL
- Pytest test suite

## Tech stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Docker Compose
- Pytest

## Site statuses

- new
- in_progress
- blocked
- done
- reported

## Site event types

- note
- issue
- status_change
- measurement
- customer

## Run locally

docker compose up -d --build

## Run tests

docker compose exec api python -m pytest -q

## Health check

curl http://localhost:8000/health/db

## API examples

Create a site:

curl -X POST http://localhost:8000/sites \
  -H "Content-Type: application/json" \
  -d '{"address":"Objektas A","status":"new"}'

List sites:

curl http://localhost:8000/sites

Filter sites by status:

curl "http://localhost:8000/sites?status=blocked"

Get site stats:

curl http://localhost:8000/sites/stats

Update site status:

curl -X PATCH http://localhost:8000/sites/1 \
  -H "Content-Type: application/json" \
  -d '{"status":"blocked"}'

List site events:

curl http://localhost:8000/sites/1/events

Add a site event:

curl -X POST http://localhost:8000/sites/1/events \
  -H "Content-Type: application/json" \
  -d '{"event_type":"issue","message":"Customer did not answer"}'

## API documentation

FastAPI automatically exposes API documentation at:

http://localhost:8000/docs

The API uses explicit Pydantic response schemas for sites, site events, and delete responses.

## Database setup

Docker Compose runs PostgreSQL with two databases:

- task_tracker - development/demo database
- task_tracker_test - test database used by pytest

Tests use TEST_DATABASE_URL so they do not delete development/demo data.

## Environment variables

Local configuration is loaded from `.env`.

Create it from the example file:

    cp .env.example .env

The `.env` file is ignored by Git. Use `.env.example` as the public template.

## Linting

Run Ruff locally:

    docker compose exec api ruff check .

## Formatting

Format code with Ruff:

    docker compose exec api ruff format .

Check formatting without changing files:

    docker compose exec api ruff format --check .

## Common commands

Start services:

    make up

Rebuild services:

    make build

Run tests:

    make test

Run lint and format checks:

    make ci

Format code:

    make format

Stop services:

    make down

## Database migrations

Run migrations on the development database:

    make migrate

Run migrations against a clean test database:

    make migrate-test
