from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db import db_ping, get_engine
from app.routers.auth import router as auth_router
from app.routers.sites import router as sites_router

openapi_tags = [
    {
        "name": "auth",
        "description": "User registration, login, and current user endpoints.",
    },
    {
        "name": "sites",
        "description": "FTTH work site CRUD, status tracking, stats, and history events.",
    },
]


app = FastAPI(
    title="FTTH Task Tracker API",
    description="Backend API for tracking FTTH work sites, statuses, and site history events.",
    version="1.0.0",
    openapi_tags=openapi_tags,
)

app.include_router(auth_router)
app.include_router(sites_router)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

if FRONTEND_DIR.exists():
    app.mount("/demo", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="demo")


@app.get("/")
def root():
    return {
        "name": "FTTH Task Tracker API",
        "version": "1.0.0",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/health/db")
def health_db():
    engine = get_engine()
    version = db_ping(engine)
    return {"db": "ok", "version": version}
