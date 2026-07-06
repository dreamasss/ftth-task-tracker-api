from fastapi import FastAPI

from app.db import db_ping, get_engine
from app.routers.auth import router as auth_router
from app.routers.sites import router as sites_router

app = FastAPI(
    title="FTTH Task Tracker API",
    description="Backend API for tracking FTTH work sites, statuses, and site history events.",
    version="1.0.0",
)

app.include_router(auth_router)
app.include_router(sites_router)


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/health/db")
def health_db():
    engine = get_engine()
    version = db_ping(engine)
    return {"db": "ok", "version": version}
