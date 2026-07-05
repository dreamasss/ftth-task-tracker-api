from pydantic import BaseModel


class SiteCreate(BaseModel):
    address: str
    customer_name: str | None = None
    status: str = "new"
    comment: str | None = None


class SiteUpdate(BaseModel):
    address: str | None = None
    customer_name: str | None = None
    status: str | None = None
    comment: str | None = None
