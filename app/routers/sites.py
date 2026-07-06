from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Site, SiteEvent
from app.schemas import (
    SiteCreate,
    SiteDeleteResponse,
    SiteEventCreate,
    SiteEventRead,
    SiteRead,
    SiteStatus,
    SiteUpdate,
)

router = APIRouter(prefix="/sites", tags=["sites"])


def site_to_dict(site: Site):
    return {
        "id": site.id,
        "address": site.address,
        "customer_name": site.customer_name,
        "status": site.status,
        "comment": site.comment,
        "created_at": site.created_at,
    }


def event_to_dict(event: SiteEvent):
    return {
        "id": event.id,
        "site_id": event.site_id,
        "event_type": event.event_type,
        "message": event.message,
        "created_at": event.created_at,
    }


@router.post("", response_model=SiteRead)
def create_site(site_in: SiteCreate, db: Session = Depends(get_db)):
    site = Site(
        address=site_in.address,
        customer_name=site_in.customer_name,
        status=site_in.status.value,
        comment=site_in.comment,
    )

    db.add(site)
    db.commit()
    db.refresh(site)

    return site_to_dict(site)


@router.get("", response_model=list[SiteRead])
def list_sites(status: SiteStatus | None = None, db: Session = Depends(get_db)):
    query = select(Site)

    if status is not None:
        query = query.where(Site.status == status.value)

    sites = db.execute(query.order_by(Site.id)).scalars().all()
    return [site_to_dict(site) for site in sites]


@router.get("/stats", response_model=dict[str, int])
def get_sites_stats(db: Session = Depends(get_db)):
    stats = {status.value: 0 for status in SiteStatus}

    rows = db.execute(select(Site.status, func.count(Site.id)).group_by(Site.status)).all()

    for status, count in rows:
        stats[status] = count

    return stats


@router.get("/{site_id}", response_model=SiteRead)
def get_site(site_id: int, db: Session = Depends(get_db)):
    site = db.get(Site, site_id)

    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")

    return site_to_dict(site)


@router.patch("/{site_id}", response_model=SiteRead)
def update_site(site_id: int, site_in: SiteUpdate, db: Session = Depends(get_db)):
    site = db.get(Site, site_id)

    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")

    old_status = site.status

    if site_in.address is not None:
        site.address = site_in.address

    if site_in.customer_name is not None:
        site.customer_name = site_in.customer_name

    if site_in.status is not None:
        new_status = site_in.status.value

        if new_status != old_status:
            site.status = new_status

            event = SiteEvent(
                site_id=site.id,
                event_type="status_change",
                message=f"Status changed from {old_status} to {new_status}",
            )
            db.add(event)

    if site_in.comment is not None:
        site.comment = site_in.comment

    db.commit()
    db.refresh(site)

    return site_to_dict(site)


@router.delete("/{site_id}", response_model=SiteDeleteResponse)
def delete_site(site_id: int, db: Session = Depends(get_db)):
    site = db.get(Site, site_id)

    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")

    db.delete(site)
    db.commit()

    return {"deleted": True, "id": site_id}


@router.post("/{site_id}/events", response_model=SiteEventRead)
def create_site_event(
    site_id: int,
    event_in: SiteEventCreate,
    db: Session = Depends(get_db),
):
    site = db.get(Site, site_id)

    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")

    event = SiteEvent(
        site_id=site_id,
        event_type=event_in.event_type.value,
        message=event_in.message,
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return event_to_dict(event)


@router.get("/{site_id}/events", response_model=list[SiteEventRead])
def list_site_events(site_id: int, db: Session = Depends(get_db)):
    site = db.get(Site, site_id)

    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")

    events = db.execute(select(SiteEvent).where(SiteEvent.site_id == site_id).order_by(SiteEvent.id)).scalars().all()

    return [event_to_dict(event) for event in events]
