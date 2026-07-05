import pytest
from sqlalchemy import delete

from app.db import SessionLocal
from app.models import Site


@pytest.fixture(autouse=True)
def clean_sites_table():
    with SessionLocal() as db:
        db.execute(delete(Site))
        db.commit()

    yield

    with SessionLocal() as db:
        db.execute(delete(Site))
        db.commit()
