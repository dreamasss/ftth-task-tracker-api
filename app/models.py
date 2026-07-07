from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tasks: Mapped[list["Task"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    sites: Mapped[list["Site"]] = relationship(back_populates="user")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_done: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    owner: Mapped["User"] = relationship(back_populates="tasks")


class Site(Base):
    __tablename__ = "sites"
    __table_args__ = (
        CheckConstraint(
            "status IN ('new', 'in_progress', 'blocked', 'done', 'reported')",
            name="ck_sites_status_valid",
        ),
        CheckConstraint(
            "priority IN ('low', 'medium', 'high')",
            name="ck_sites_priority_valid",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="new", nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    planned_date: Mapped["Date | None"] = mapped_column(Date, nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped["User | None"] = relationship(back_populates="sites")
    events: Mapped[list["SiteEvent"]] = relationship(back_populates="site", cascade="all, delete-orphan")


class SiteEvent(Base):
    __tablename__ = "site_events"
    __table_args__ = (
        CheckConstraint(
            "event_type IN ('note', 'issue', 'status_change')",
            name="ck_site_events_event_type_valid",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"), index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), default="note", nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    site: Mapped["Site"] = relationship(back_populates="events")
