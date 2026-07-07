# FTTH Task Tracker API

[![Tests](https://github.com/dreamasss/ftth-task-tracker-api/actions/workflows/tests.yml/badge.svg)](https://github.com/dreamasss/ftth-task-tracker-api/actions/workflows/tests.yml)

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

## Site priorities

- low
- medium (default)
- high

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

## API examples

Protected site endpoints require a Bearer token. Site priority can be low, medium, or high. Sites can also have an optional planned_date in YYYY-MM-DD format.

Set API base URL:

    BASE_URL=http://localhost:8000

For the deployed API:

    BASE_URL=https://ftth-task-tracker-api.onrender.com

Register and login:

    EMAIL="demo+$(date +%s)@example.com"
    PASSWORD="strong-password-123"

    curl -X POST "$BASE_URL/auth/register" \
      -H "Content-Type: application/json" \
      -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}"

    TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
      -H "Content-Type: application/json" \
      -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" \
      | python3 -c 'import json, sys; print(json.load(sys.stdin)["access_token"])')

Create and use a site:

    SITE_ID=$(curl -s -X POST "$BASE_URL/sites" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"address":"Objektas A","status":"new","priority":"high","planned_date":"2026-07-15"}' \
      | python3 -c 'import json, sys; print(json.load(sys.stdin)["id"])')

    curl "$BASE_URL/sites" \
      -H "Authorization: Bearer $TOKEN"

    curl "$BASE_URL/sites/stats" \
      -H "Authorization: Bearer $TOKEN"

    curl -X PATCH "$BASE_URL/sites/$SITE_ID" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"status":"blocked"}'

    curl -X POST "$BASE_URL/sites/$SITE_ID/events" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"event_type":"issue","message":"Customer did not answer"}'

    curl "$BASE_URL/sites/$SITE_ID/events" \
      -H "Authorization: Bearer $TOKEN"

## API documentation

FastAPI automatically exposes API documentation at:

http://localhost:8000/docs

The API uses explicit Pydantic response schemas for sites, site events, and delete responses.

## Database setup

Docker Compose runs PostgreSQL with two databases:

- task_tracker - development/demo database
- task_tracker_test - test database used by pytest

Tests use TEST_DATABASE_URL so they do not delete development/demo data.

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

Site endpoints require authentication. Users can only access their own sites and site events.

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

## Local development shortcuts

Common commands:

- `make up` — start Docker containers
- `make test-db` — create the test database if missing
- `make ci` — run linting, formatting check, and tests
- `make smoke` — run the API smoke test against the local server
- `make down` — stop Docker containers without deleting volumes

## Deployment checklist

Required environment variables:

- `DATABASE_URL` — production PostgreSQL connection string
- `SECRET_KEY` — secret used to sign access tokens
- `PORT` — provided by the hosting platform, defaults to `8000` locally

Container startup:

- `scripts/start.sh` runs `alembic upgrade head`
- then starts FastAPI with Uvicorn

After deployment, verify the live API with:

```bash
BASE_URL=https://your-api-url.example.com make smoke
```

## Live demo

- API: https://ftth-task-tracker-api.onrender.com
- Swagger docs: https://ftth-task-tracker-api.onrender.com/docs
- Health check: https://ftth-task-tracker-api.onrender.com/health

Smoke test against the deployed API:

```bash
BASE_URL=https://ftth-task-tracker-api.onrender.com make smoke
```

## Known limitations

- The Render free instance may sleep after inactivity, so the first request can be slower.
- There is no frontend/admin UI yet; the API is tested through Swagger docs and smoke tests.
- Access tokens expire, but refresh tokens are not implemented yet.
- There is no role-based admin system yet.
- This is a portfolio/demo project, not a production SaaS service.

## Using Swagger authentication

1. Open the Swagger docs: https://ftth-task-tracker-api.onrender.com/docs
2. Run `POST /auth/register` with an email and password.
3. Run `POST /auth/login` with the same credentials.
4. Copy the returned access token.
5. Click `Authorize` in Swagger.
6. Enter the token in this format: `Bearer <token>`.
7. Try protected endpoints such as `POST /sites`, `GET /sites`, or `POST /sites/{site_id}/events`.

Example protected flow:

```text
Register user -> Login -> Authorize -> Create site -> Add event -> List site events
```

## Planned date filters

Sites can be filtered by planned date:

    curl "$BASE_URL/sites?planned_after=2026-07-01" \
      -H "Authorization: Bearer $TOKEN"

    curl "$BASE_URL/sites?planned_before=2026-08-01" \
      -H "Authorization: Bearer $TOKEN"

    curl "$BASE_URL/sites?planned_after=2026-07-01&planned_before=2026-08-01" \
      -H "Authorization: Bearer $TOKEN"

## Planned date sorting

Sites can be sorted by planned date:

    curl "$BASE_URL/sites?sort_by=planned_date&sort_order=asc" \
      -H "Authorization: Bearer $TOKEN"

    curl "$BASE_URL/sites?sort_by=planned_date&sort_order=desc" \
      -H "Authorization: Bearer $TOKEN"
