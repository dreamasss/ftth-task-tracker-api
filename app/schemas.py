from pydantic import BaseModel


class SiteCreate(BaseModel):
    address: str
    customer_name: str | None = None
    status: str = "new"
    comment: str | None = None
