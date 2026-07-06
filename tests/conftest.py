import os

import pytest
from alembic.config import Config
from sqlalchemy import delete, text

from alembic import command

test_db_url = os.getenv("TEST_DATABASE_URL")
if not test_db_url:
    raise RuntimeError("TEST_DATABASE_URL is not set")

os.environ["DATABASE_URL"] = test_db_url

from app.db import SessionLocal, get_engine  # noqa: E402
from app.models import Site, SiteEvent  # noqa: E402,F401


def reset_public_schema():
    engine = get_engine()

    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))


@pytest.fixture(scope="session", autouse=True)
def prepare_test_database():
    reset_public_schema()

    alembic_config = Config("alembic.ini")
    command.upgrade(alembic_config, "head")

    yield

    reset_public_schema()


@pytest.fixture(autouse=True)
def clean_tables():
    with SessionLocal() as db:
        db.execute(delete(SiteEvent))
        db.execute(delete(Site))
        db.commit()

    yield

    with SessionLocal() as db:
        db.execute(delete(SiteEvent))
        db.execute(delete(Site))
        db.commit()
