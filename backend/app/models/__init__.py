from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32))  # admin | viewer
    tenant: Mapped[str] = mapped_column(String(64), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        Index("ix_events_tenant_ts", "tenant", "timestamp"),
        Index("ix_events_source", "source"),
        Index("ix_events_event_type", "event_type"),
        Index("ix_events_src_ip", "src_ip"),
        Index("ix_events_user", "event_user"),
        Index("ix_events_tags", "tags", postgresql_using="gin"),
        Index("ix_events_raw", "raw", postgresql_using="gin"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    tenant: Mapped[str] = mapped_column(String(64), index=True)
    source: Mapped[str] = mapped_column(String(64))
    vendor: Mapped[str | None] = mapped_column(String(128), nullable=True)
    product: Mapped[str | None] = mapped_column(String(128), nullable=True)
    event_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    event_subtype: Mapped[str | None] = mapped_column(String(128), nullable=True)
    severity: Mapped[float | None] = mapped_column(Float, nullable=True)
    action: Mapped[str | None] = mapped_column(String(64), nullable=True)
    src_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    src_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dst_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    dst_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    protocol: Mapped[str | None] = mapped_column(String(32), nullable=True)
    user: Mapped[str | None] = mapped_column("event_user", String(256), nullable=True)
    host: Mapped[str | None] = mapped_column(String(256), nullable=True)
    process: Mapped[str | None] = mapped_column(String(256), nullable=True)
    url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    http_method: Mapped[str | None] = mapped_column(String(16), nullable=True)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rule_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    rule_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    cloud_account_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    cloud_region: Mapped[str | None] = mapped_column(String(64), nullable=True)
    cloud_service: Mapped[str | None] = mapped_column(String(128), nullable=True)
    raw: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tenant: Mapped[str | None] = mapped_column(String(64), nullable=True)  # None = all
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    # failed_login_burst: same src_ip, login failures, window minutes, threshold
    rule_type: Mapped[str] = mapped_column(String(64), default="failed_login_burst")
    window_minutes: Mapped[int] = mapped_column(Integer, default=5)
    threshold: Mapped[int] = mapped_column(Integer, default=3)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (Index("ix_alerts_tenant_ts", "tenant", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rule_id: Mapped[int] = mapped_column(Integer, index=True)
    rule_name: Mapped[str] = mapped_column(String(128))
    tenant: Mapped[str] = mapped_column(String(64), index=True)
    severity: Mapped[float] = mapped_column(Float, default=7.0)
    title: Mapped[str] = mapped_column(String(256))
    message: Mapped[str] = mapped_column(Text)
    src_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    event_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default="open")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    meta: Mapped[dict[str, Any] | None] = mapped_column("alert_meta", JSONB, nullable=True)
