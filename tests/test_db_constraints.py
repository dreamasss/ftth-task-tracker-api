from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.db import SessionLocal
from app.models import Site, SiteEvent


def test_database_rejects_invalid_site_status():
    with SessionLocal() as db:
        site = Site(
            address=f"Invalid status objektas {uuid4()}",
            status="bad_status",
        )

        db.add(site)

        with pytest.raises(IntegrityError):
            db.commit()

        db.rollback()


def test_database_rejects_invalid_site_event_type():
    with SessionLocal() as db:
        site = Site(
            address=f"Invalid event type objektas {uuid4()}",
            status="new",
        )

        db.add(site)
        db.commit()
        db.refresh(site)

        event = SiteEvent(
            site_id=site.id,
            event_type="bad_type",
            message="Bad event type",
        )

        db.add(event)

        with pytest.raises(IntegrityError):
            db.commit()

        db.rollback()
