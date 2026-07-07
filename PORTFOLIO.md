# FTTH Task Tracker API — Portfolio Notes

## What this project demonstrates

- FastAPI backend with PostgreSQL
- JWT/Bearer token authentication
- User-owned resources
- CRUD operations for telecom/FTTH work sites
- Site events/history tracking
- Filtering, sorting, and pagination
- Database migrations with Alembic
- Dockerized local development
- Pytest test suite
- CI test workflow
- Production deployment on Render with Neon PostgreSQL

## Live demo

- API: https://ftth-task-tracker-api.onrender.com
- Swagger docs: https://ftth-task-tracker-api.onrender.com/docs

## Example use case

A telecom technician can register, create FTTH work sites, track statuses, add notes, issues, measurements, filter planned work, and review site history.

## Technical highlights

- Authenticated endpoints
- Users can only access their own sites
- Pagination metadata with total, limit, offset, and items
- Automatic status_change event when a site status changes
- Local and deployed smoke tests

## Known limitations

- No frontend/admin UI yet
- No refresh tokens
- No role-based admin system
- Render free instance may sleep after inactivity