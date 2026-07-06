from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class SiteStatus(str, Enum):
    new = "new"
    in_progress = "in_progress"
    blocked = "blocked"
    done = "done"
    reported = "reported"


class SiteEventType(str, Enum):
    note = "note"
    issue = "issue"
    status_change = "status_change"
    measurement = "measurement"
    customer = "customer"


class SiteCreate(BaseModel):
    address: str
    customer_name: str | None = None
    status: SiteStatus = SiteStatus.new
    comment: str | None = None


class SiteUpdate(BaseModel):
    address: str | None = None
    customer_name: str | None = None
    status: SiteStatus | None = None
    comment: str | None = None


class SiteRead(BaseModel):
    id: int
    address: str
    customer_name: str | None = None
    status: SiteStatus
    comment: str | None = None
    created_at: datetime
    updated_at: datetime


class SiteListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[SiteRead]


class SiteDeleteResponse(BaseModel):
    deleted: bool
    id: int


class SiteEventCreate(BaseModel):
    event_type: SiteEventType = SiteEventType.note
    message: str


class SiteEventRead(BaseModel):
    id: int
    site_id: int
    event_type: SiteEventType
    message: str
    created_at: datetime


class SiteStatsResponse(BaseModel):
    new: int
    in_progress: int
    blocked: int
    done: int
    reported: int
