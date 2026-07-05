from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_engine, db_ping, get_db
from app.models import Site
from app.schemas import SiteCreate


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
