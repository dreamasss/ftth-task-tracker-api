import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


def get_db_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    return url


def get_engine():
    return create_engine(get_db_url(), pool_pre_ping=True)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())


def db_ping(engine):
    with engine.connect() as conn:
        return conn.execute(text("SELECT version()")).scalar_one()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
