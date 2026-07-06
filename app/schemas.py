from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


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
    address: str = Field(min_length=1, max_length=255)
    customer_name: str | None = Field(default=None, min_length=1, max_length=200)
    status: SiteStatus = SiteStatus.new
    comment: str | None = Field(default=None, min_length=1, max_length=2000)

    @field_validator("address", "customer_name", "comment", mode="before")
    @classmethod
    def strip_text_fields(cls, value):
        if isinstance(value, str):
            return value.strip()

        return value


class SiteUpdate(BaseModel):
    address: str | None = Field(default=None, min_length=1, max_length=255)
    customer_name: str | None = Field(default=None, min_length=1, max_length=200)
    status: SiteStatus | None = None
    comment: str | None = Field(default=None, min_length=1, max_length=2000)

    @field_validator("address", "customer_name", "comment", mode="before")
    @classmethod
    def strip_text_fields(cls, value):
        if isinstance(value, str):
            return value.strip()

        return value

    @model_validator(mode="after")
    def reject_null_required_fields(self):
        if "address" in self.model_fields_set and self.address is None:
            raise ValueError("address cannot be null")

        if "status" in self.model_fields_set and self.status is None:
            raise ValueError("status cannot be null")

        return self


class SiteRead(BaseModel):
    id: int
    user_id: int | None = None
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
    message: str = Field(min_length=1, max_length=2000)

    @field_validator("message", mode="before")
    @classmethod
    def strip_message(cls, value):
        if isinstance(value, str):
            return value.strip()

        return value


class SiteEventRead(BaseModel):
    id: int
    site_id: int
    event_type: SiteEventType
    message: str
    created_at: datetime


class SiteEventListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[SiteEventRead]


class SiteStatsResponse(BaseModel):
    total: int = 0
    new: int
    in_progress: int
    blocked: int
    done: int
    reported: int


class UserCreate(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        if isinstance(value, str):
            return value.strip().lower()

        return value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value):
        if "@" not in value or "." not in value.split("@")[-1]:
            raise ValueError("Invalid email")

        return value


class UserRead(BaseModel):
    id: int
    email: str
    is_active: bool
    created_at: datetime


class UserLogin(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        if isinstance(value, str):
            return value.strip().lower()

        return value


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
