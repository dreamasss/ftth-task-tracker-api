from fastapi import FastAPI

from app.db import db_ping, get_engine
from app.routers.sites import router as sites_router

app = FastAPI()

app.include_router(sites_router)


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/health/db")
def health_db():
    engine = get_engine()
    version = db_ping(engine)
    return {"db": "ok", "version": version}
