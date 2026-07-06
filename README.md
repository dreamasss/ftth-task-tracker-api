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

## List sites with filters and pagination

The `GET /sites` endpoint supports status filtering, text search, limit/offset pagination, and validated query parameters.

Example request:

```bash
curl "http://localhost:8000/sites?search=Fiber&status=new&limit=10&offset=0"
```

Example response:

```json
{
  "total": 2,
  "limit": 10,
  "offset": 0,
  "items": [
    {
      "id": 1,
      "address": "Vilnius Test Search",
      "customer_name": "Jonas Fiber",
      "status": "new",
      "comment": null,
      "created_at": "2026-07-06T10:44:44.800012Z"
    }
  ]
}
```

Query parameters:

| Parameter | Description |
|---|---|
| `status` | Optional site status filter: `new`, `in_progress`, `blocked`, `done`, `reported` |
| `search` | Optional text search by address or customer name, 1–100 characters |
| `limit` | Number of items to return, from 1 to 100 |
| `offset` | Number of items to skip, minimum 0 |
| `sort_by` | Sort field: `id`, `address`, `status`, `created_at` |
| `sort_order` | Sort direction: `asc` or `desc` |

## Healthcheck

The API exposes a database health endpoint:

```bash
curl http://localhost:8000/health/db
```

The Docker image also defines a container healthcheck that calls this endpoint.

## List site events with pagination

The `GET /sites/{site_id}/events` endpoint returns site events with pagination metadata.

Example request:

```bash
curl "http://localhost:8000/sites/1/events?limit=10&offset=0"
```

Example response:

```json
{
  "total": 1,
  "limit": 10,
  "offset": 0,
  "items": [
    {
      "id": 1,
      "site_id": 1,
      "event_type": "note",
      "message": "Signal level checked",
      "created_at": "2026-07-06T12:30:00Z"
    }
  ]
}
```

Query parameters:

| Parameter | Description |
|---|---|
| `event_type` | Optional event type filter: `note`, `issue`, `status_change` |
| `limit` | Number of events to return, from 1 to 100 |
| `offset` | Number of events to skip, minimum 0 |
| `sort_order` | Sort direction by event id: `asc` or `desc` |

Run a full test migration roundtrip:

```bash
make migrate-test-roundtrip
```

This command resets the test database, runs Alembic migrations up to `head`, downgrades back to `base`, and upgrades to `head` again. It is also checked in CI.

## Authentication

The API supports user registration, login, and Bearer token authentication.

### Register

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","password":"strong-password-123"}'
```

### Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","password":"strong-password-123"}'
```

### Get current user

```bash
TOKEN="paste-access-token-here"

curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

### Protected write endpoints

These endpoints require a Bearer token:

```text
POST /sites
PATCH /sites/{site_id}
DELETE /sites/{site_id}
POST /sites/{site_id}/events
```

Read endpoints such as GET /sites and GET /sites/{site_id} are public.

## Environment variables

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Required variables:

```text
DATABASE_URL
TEST_DATABASE_URL
SECRET_KEY
```

`SECRET_KEY` is used to sign access tokens. Change it in real deployments.

### Protected site endpoints

Most site endpoints require a Bearer token and only return data owned by the current user:

```text
GET /sites
GET /sites/stats
GET /sites/{site_id}
POST /sites
PATCH /sites/{site_id}
DELETE /sites/{site_id}
GET /sites/{site_id}/events
POST /sites/{site_id}/events
```

Users can only access their own sites and site events. Requests for another user's site return 404.

## Demo flow

Full authenticated API flow:

1. Register user

`POST /auth/register` with email and password.

2. Login and save token

`POST /auth/login` returns an `access_token`.

3. Create a site

Use `POST /sites` with `Authorization: Bearer <token>`.

4. List my sites

Use `GET /sites` with `Authorization: Bearer <token>`.

5. Add a site event

Use `POST /sites/{site_id}/events` with `Authorization: Bearer <token>`.

6. Get my site stats

Use `GET /sites/stats` with `Authorization: Bearer <token>`.
