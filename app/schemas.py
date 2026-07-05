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


class SiteEventCreate(BaseModel):
    event_type: SiteEventType = SiteEventType.note
    message: str
