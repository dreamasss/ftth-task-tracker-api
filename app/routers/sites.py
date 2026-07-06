from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user
from app.models import Site, SiteEvent, User
from app.schemas import (
    SiteCreate,
    SiteDeleteResponse,
    SiteEventCreate,
    SiteEventListResponse,
    SiteEventRead,
    SiteEventType,
    SiteListResponse,
    SiteRead,
    SiteStatsResponse,
    SiteStatus,
    SiteUpdate,
)

router = APIRouter(prefix="/sites", tags=["sites"])


def get_user_site_or_404(db: Session, site_id: int, user_id: int) -> Site:
    site = db.execute(
        select(Site).where(
            Site.id == site_id,
            Site.user_id == user_id,
        )
    ).scalar_one_or_none()

    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")

    return site


def site_to_dict(site: Site):
    return {
        "id": site.id,
        "user_id": site.user_id,
        "address": site.address,
        "customer_name": site.customer_name,
        "status": site.status,
        "comment": site.comment,
        "created_at": site.created_at,
        "updated_at": site.updated_at,
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
def create_site(site_in: SiteCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    site = Site(
        user_id=current_user.id,
        address=site_in.address,
        customer_name=site_in.customer_name,
        status=site_in.status.value,
        comment=site_in.comment,
    )

    db.add(site)
    db.commit()
    db.refresh(site)

    return site_to_dict(site)


@router.get("", response_model=SiteListResponse)
def list_sites(
    status: SiteStatus | None = None,
    search: str | None = Query(default=None, min_length=1, max_length=100),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sort_by: Literal["id", "address", "status", "created_at"] = Query(default="id"),
    sort_order: Literal["asc", "desc"] = Query(default="asc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Site).where(Site.user_id == current_user.id)

    if status is not None:
        query = query.where(Site.status == status.value)

    if search:
        pattern = f"%{search}%"
        query = query.where(
            or_(
                Site.address.ilike(pattern),
                Site.customer_name.ilike(pattern),
            )
        )

    total = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()

    sort_columns = {
        "id": Site.id,
        "address": Site.address,
        "status": Site.status,
        "created_at": Site.created_at,
    }
    sort_column = sort_columns[sort_by]
    order_by = sort_column.desc() if sort_order == "desc" else sort_column.asc()

    sites = db.execute(query.order_by(order_by).limit(limit).offset(offset)).scalars().all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [site_to_dict(site) for site in sites],
    }


@router.get("/stats", response_model=SiteStatsResponse)
def get_sites_stats(db: Session = Depends(get_db)):
    stats = {status.value: 0 for status in SiteStatus}

    rows = db.execute(select(Site.status, func.count(Site.id)).group_by(Site.status)).all()

    for status, count in rows:
        stats[status] = count

    return stats


@router.get("/{site_id}", response_model=SiteRead)
def get_site(site_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    site = get_user_site_or_404(db, site_id, current_user.id)

    return site_to_dict(site)


@router.patch("/{site_id}", response_model=SiteRead)
def update_site(
    site_id: int, site_in: SiteUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    site = get_user_site_or_404(db, site_id, current_user.id)

    old_status = site.status

    update_data = site_in.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    if "address" in update_data:
        site.address = update_data["address"]

    if "customer_name" in update_data:
        site.customer_name = update_data["customer_name"]

    if "status" in update_data:
        new_status = site_in.status.value

        if new_status != old_status:
            site.status = new_status

            event = SiteEvent(
                site_id=site.id,
                event_type="status_change",
                message=f"Status changed from {old_status} to {new_status}",
            )
            db.add(event)

    if "comment" in update_data:
        site.comment = update_data["comment"]

    db.commit()
    db.refresh(site)

    return site_to_dict(site)


@router.delete("/{site_id}", response_model=SiteDeleteResponse)
def delete_site(site_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    site = get_user_site_or_404(db, site_id, current_user.id)

    db.delete(site)
    db.commit()

    return {"deleted": True, "id": site_id}


@router.post("/{site_id}/events", response_model=SiteEventRead)
def create_site_event(
    site_id: int,
    event_in: SiteEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
    site.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(event)

    return event_to_dict(event)


@router.get("/{site_id}/events", response_model=SiteEventListResponse)
def list_site_events(
    site_id: int,
    event_type: SiteEventType | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sort_order: Literal["asc", "desc"] = Query(default="asc"),
    db: Session = Depends(get_db),
):
    site = db.get(Site, site_id)

    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")

    query = select(SiteEvent).where(SiteEvent.site_id == site_id)

    if event_type is not None:
        query = query.where(SiteEvent.event_type == event_type.value)

    total = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()

    order_by = SiteEvent.id.desc() if sort_order == "desc" else SiteEvent.id.asc()

    events = db.execute(query.order_by(order_by).limit(limit).offset(offset)).scalars().all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [event_to_dict(event) for event in events],
    }
