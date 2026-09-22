from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    tenant: str
    username: str


class LoginRequest(BaseModel):
    username: str
    password: str


class EventOut(BaseModel):
    id: int
    timestamp: datetime
    tenant: str
    source: str
    vendor: str | None = None
    product: str | None = None
    event_type: str | None = None
    event_subtype: str | None = None
    severity: float | None = None
    action: str | None = None
    src_ip: str | None = None
    src_port: int | None = None
    dst_ip: str | None = None
    dst_port: int | None = None
    protocol: str | None = None
    user: str | None = None
    host: str | None = None
    process: str | None = None
    url: str | None = None
    http_method: str | None = None
    status_code: int | None = None
    rule_name: str | None = None
    rule_id: str | None = None
    cloud_account_id: str | None = None
    cloud_region: str | None = None
    cloud_service: str | None = None
    raw: dict[str, Any] | None = None
    tags: list[str] | None = None
    ingested_at: datetime | None = None

    model_config = {"from_attributes": True}


class SearchResponse(BaseModel):
    total: int
    items: list[EventOut]


class IngestResponse(BaseModel):
    accepted: int
    normalized: list[dict[str, Any]] = Field(default_factory=list)


class DashboardSummary(BaseModel):
    total_events: int
    top_ips: list[dict[str, Any]]
    top_users: list[dict[str, Any]]
    top_event_types: list[dict[str, Any]]
    timeline: list[dict[str, Any]]
    by_source: list[dict[str, Any]]


class AlertOut(BaseModel):
    id: int
    rule_id: int
    rule_name: str
    tenant: str
    severity: float
    title: str
    message: str
    src_ip: str | None = None
    event_count: int
    status: str
    created_at: datetime
    meta: dict[str, Any] | None = None

    model_config = {"from_attributes": True}


class AlertRuleOut(BaseModel):
    id: int
    name: str
    description: str | None = None
    tenant: str | None = None
    enabled: bool
    rule_type: str
    window_minutes: int
    threshold: int

    model_config = {"from_attributes": True}


class AlertRuleCreate(BaseModel):
    name: str
    description: str | None = None
    tenant: str | None = None
    enabled: bool = True
    rule_type: Literal["failed_login_burst"] = "failed_login_burst"
    window_minutes: int = 5
    threshold: int = 3


class HealthResponse(BaseModel):
    status: str
    app: str
