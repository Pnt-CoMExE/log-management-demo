from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import Select, and_, cast, desc, func, or_, select
from sqlalchemy.orm import Session
from sqlalchemy.types import DateTime

from app.models import Alert, AlertRule, Event

FAILED_TYPES = (
    "app_login_failed",
    "LogonFailed",
    "login_failed",
    "failed_login",
    "UserLoginFailed",
)


def event_from_normalized(data: dict[str, Any]) -> Event:
    return Event(
        timestamp=data["timestamp"],
        tenant=data["tenant"],
        source=data["source"],
        vendor=data.get("vendor"),
        product=data.get("product"),
        event_type=data.get("event_type"),
        event_subtype=str(data["event_subtype"]) if data.get("event_subtype") is not None else None,
        severity=data.get("severity"),
        action=data.get("action"),
        src_ip=data.get("src_ip"),
        src_port=data.get("src_port"),
        dst_ip=data.get("dst_ip"),
        dst_port=data.get("dst_port"),
        protocol=data.get("protocol"),
        user=data.get("user"),
        host=data.get("host"),
        process=data.get("process"),
        url=data.get("url"),
        http_method=data.get("http_method"),
        status_code=data.get("status_code"),
        rule_name=data.get("rule_name"),
        rule_id=data.get("rule_id"),
        cloud_account_id=data.get("cloud_account_id"),
        cloud_region=data.get("cloud_region"),
        cloud_service=data.get("cloud_service"),
        raw=data.get("raw"),
        tags=data.get("tags") or [],
    )


def insert_events(db: Session, normalized_list: list[dict[str, Any]]) -> list[Event]:
    events = [event_from_normalized(item) for item in normalized_list]
    db.add_all(events)
    db.commit()
    for ev in events:
        db.refresh(ev)
    return events


def apply_tenant_filter(stmt: Select, role: str, user_tenant: str, requested: str | None) -> Select:
    if role == "admin":
        if requested:
            return stmt.where(Event.tenant == requested)
        return stmt
    # viewer: locked to own tenant
    return stmt.where(Event.tenant == user_tenant)


def search_events(
    db: Session,
    *,
    role: str,
    user_tenant: str,
    tenant: str | None = None,
    source: str | None = None,
    event_type: str | None = None,
    src_ip: str | None = None,
    user: str | None = None,
    q: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[int, list[Event]]:
    stmt = select(Event)
    stmt = apply_tenant_filter(stmt, role, user_tenant, tenant)

    filters = []
    if source:
        filters.append(Event.source == source)
    if event_type:
        filters.append(Event.event_type == event_type)
    if src_ip:
        filters.append(Event.src_ip == src_ip)
    if user:
        filters.append(Event.user == user)
    if start:
        filters.append(Event.timestamp >= start)
    if end:
        filters.append(Event.timestamp <= end)
    if q:
        like = f"%{q}%"
        filters.append(
            or_(
                Event.event_type.ilike(like),
                Event.user.ilike(like),
                Event.host.ilike(like),
                Event.src_ip.ilike(like),
                Event.action.ilike(like),
            )
        )
    if filters:
        stmt = stmt.where(and_(*filters))

    count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
    total = db.scalar(count_stmt) or 0

    items = db.scalars(stmt.order_by(desc(Event.timestamp)).limit(limit).offset(offset)).all()
    return total, list(items)


def dashboard_summary(
    db: Session,
    *,
    role: str,
    user_tenant: str,
    tenant: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
) -> dict[str, Any]:
    if start is None:
        start = datetime.now(timezone.utc) - timedelta(hours=24)
    if end is None:
        end = datetime.now(timezone.utc)

    base = select(Event).where(Event.timestamp >= start, Event.timestamp <= end)
    base = apply_tenant_filter(base, role, user_tenant, tenant)
    subq = base.subquery()

    total = db.scalar(select(func.count()).select_from(subq)) or 0

    def top(column, label: str, n: int = 5):
        rows = db.execute(
            select(column, func.count().label("count"))
            .select_from(subq)
            .where(column.is_not(None))
            .group_by(column)
            .order_by(desc("count"))
            .limit(n)
        ).all()
        return [{label: r[0], "count": r[1]} for r in rows]

    # Hourly timeline
    hour_bucket = func.date_trunc("hour", cast(subq.c.timestamp, DateTime(timezone=True)))
    timeline_rows = db.execute(
        select(hour_bucket.label("bucket"), func.count().label("count"))
        .select_from(subq)
        .group_by("bucket")
        .order_by("bucket")
    ).all()
    timeline = [
        {"timestamp": r.bucket.isoformat() if r.bucket else None, "count": r.count}
        for r in timeline_rows
    ]

    return {
        "total_events": total,
        "top_ips": top(subq.c.src_ip, "src_ip"),
        "top_users": top(subq.c.event_user, "user"),
        "top_event_types": top(subq.c.event_type, "event_type"),
        "timeline": timeline,
        "by_source": top(subq.c.source, "source", n=10),
    }


def purge_old_events(db: Session, retention_days: int) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    result = db.query(Event).filter(Event.timestamp < cutoff).delete(synchronize_session=False)
    db.commit()
    return result


def evaluate_failed_login_burst(db: Session, rule: AlertRule) -> list[Alert]:
    """Create alerts when failed logins from same IP exceed threshold in window."""
    window_start = datetime.now(timezone.utc) - timedelta(minutes=rule.window_minutes)
    stmt = (
        select(Event.tenant, Event.src_ip, func.count().label("cnt"))
        .where(
            Event.timestamp >= window_start,
            Event.src_ip.is_not(None),
            or_(
                Event.event_type.in_(FAILED_TYPES),
                and_(Event.action == "login", Event.event_type.ilike("%fail%")),
            ),
        )
        .group_by(Event.tenant, Event.src_ip)
        .having(func.count() >= rule.threshold)
    )
    if rule.tenant:
        stmt = stmt.where(Event.tenant == rule.tenant)

    created: list[Alert] = []
    for tenant, src_ip, cnt in db.execute(stmt).all():
        # Dedup: skip if open alert for same IP+rule in last window
        existing = db.scalar(
            select(Alert).where(
                Alert.rule_id == rule.id,
                Alert.src_ip == src_ip,
                Alert.tenant == tenant,
                Alert.status == "open",
                Alert.created_at >= window_start,
            )
        )
        if existing:
            continue
        alert = Alert(
            rule_id=rule.id,
            rule_name=rule.name,
            tenant=tenant,
            severity=8.0,
            title=f"Failed login burst from {src_ip}",
            message=(
                f"{cnt} failed login events from {src_ip} "
                f"within {rule.window_minutes} minutes (threshold={rule.threshold})"
            ),
            src_ip=src_ip,
            event_count=cnt,
            status="open",
            meta={"window_minutes": rule.window_minutes, "threshold": rule.threshold},
        )
        db.add(alert)
        created.append(alert)
    if created:
        db.commit()
        for a in created:
            db.refresh(a)
    return created


def run_all_alert_rules(db: Session) -> list[Alert]:
    rules = db.scalars(select(AlertRule).where(AlertRule.enabled.is_(True))).all()
    alerts: list[Alert] = []
    for rule in rules:
        if rule.rule_type == "failed_login_burst":
            alerts.extend(evaluate_failed_login_burst(db, rule))
    return alerts
