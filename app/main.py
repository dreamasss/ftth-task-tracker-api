from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_engine, db_ping, get_db
from app.models import Site
from app.schemas import SiteCreate, SiteUpdate


app = FastAPI()


def site_to_dict(site: Site):
    return {
        "id": site.id,
        "address": site.address,
        "customer_name": site.customer_name,
        "status": site.status,
        "comment": site.comment,
        "created_at": site.created_at,
    }


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/health/db")
def health_db():
    engine = get_engine()
    version = db_ping(engine)
    return {"db": "ok", "version": version}


@app.post("/sites")
def create_site(site_in: SiteCreate, db: Session = Depends(get_db)):
    site = Site(
        address=site_in.address,
        customer_name=site_in.customer_name,
        status=site_in.status,
        comment=site_in.comment,
    )

    db.add(site)
    db.commit()
    db.refresh(site)

    return site_to_dict(site)


@app.get("/sites")
def list_sites(db: Session = Depends(get_db)):
    sites = db.execute(select(Site).order_by(Site.id)).scalars().all()
    return [site_to_dict(site) for site in sites]


@app.get("/sites/{site_id}")
def get_site(site_id: int, db: Session = Depends(get_db)):
    site = db.get(Site, site_id)

    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")

    return site_to_dict(site)


@app.patch("/sites/{site_id}")
def update_site(site_id: int, site_in: SiteUpdate, db: Session = Depends(get_db)):
    site = db.get(Site, site_id)

    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")

    if site_in.address is not None:
        site.address = site_in.address

    if site_in.customer_name is not None:
        site.customer_name = site_in.customer_name

    if site_in.status is not None:
        site.status = site_in.status

    if site_in.comment is not None:
        site.comment = site_in.comment

    db.commit()
    db.refresh(site)

    return site_to_dict(site)


@app.delete("/sites/{site_id}")
def delete_site(site_id: int, db: Session = Depends(get_db)):
    site = db.get(Site, site_id)

    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")

    db.delete(site)
    db.commit()

    return {"deleted": True, "id": site_id}
