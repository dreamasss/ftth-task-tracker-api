import os

import pytest
from sqlalchemy import delete

test_db_url = os.getenv("TEST_DATABASE_URL")
if not test_db_url:
    raise RuntimeError("TEST_DATABASE_URL is not set")

os.environ["DATABASE_URL"] = test_db_url

from app.db import Base, SessionLocal, get_engine  # noqa: E402
from app.models import Site, SiteEvent  # noqa: E402,F401


@pytest.fixture(scope="session", autouse=True)
def prepare_test_database():
    engine = get_engine()

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    yield

    Base.metadata.drop_all(bind=engine)


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
