from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Site
from app.schemas import SiteCreate, SiteUpdate, SiteStatus


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


@router.post("")
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


@router.get("")
def list_sites(status: SiteStatus | None = None, db: Session = Depends(get_db)):
    query = select(Site)

    if status is not None:
        query = query.where(Site.status == status.value)

    sites = db.execute(query.order_by(Site.id)).scalars().all()
    return [site_to_dict(site) for site in sites]


@router.get("/stats")
def get_sites_stats(db: Session = Depends(get_db)):
    stats = {status.value: 0 for status in SiteStatus}

    rows = db.execute(
        select(Site.status, func.count(Site.id)).group_by(Site.status)
    ).all()

    for status, count in rows:
        stats[status] = count

    return stats


@router.get("/{site_id}")
def get_site(site_id: int, db: Session = Depends(get_db)):
    site = db.get(Site, site_id)

    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")

    return site_to_dict(site)


@router.patch("/{site_id}")
def update_site(site_id: int, site_in: SiteUpdate, db: Session = Depends(get_db)):
    site = db.get(Site, site_id)

    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")

    if site_in.address is not None:
        site.address = site_in.address

    if site_in.customer_name is not None:
        site.customer_name = site_in.customer_name

    if site_in.status is not None:
        site.status = site_in.status.value

    if site_in.comment is not None:
        site.comment = site_in.comment

    db.commit()
    db.refresh(site)

    return site_to_dict(site)


@router.delete("/{site_id}")
def delete_site(site_id: int, db: Session = Depends(get_db)):
    site = db.get(Site, site_id)

    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")

    db.delete(site)
    db.commit()

    return {"deleted": True, "id": site_id}
