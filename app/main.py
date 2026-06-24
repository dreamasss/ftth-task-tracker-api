from fastapi import FastAPI
from app.db import get_engine, db_ping

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/health/db")
def health_db():
    engine = get_engine()
    version = db_ping(engine)
    return {"db": "ok", "version": version}
