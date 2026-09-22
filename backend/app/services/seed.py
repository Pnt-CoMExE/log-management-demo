"""Seed demo users, default alert rule, and optional sample events."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.models import AlertRule, User
from app.services.events import insert_events
from app.services.normalize import normalize_any, normalize_syslog


def _ts(hours_ago: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def _samples() -> list:
    return [
        "<134>Aug 20 12:44:56 fw01 vendor=demo product=ngfw action=deny "
        "src=10.0.1.10 dst=8.8.8.8 spt=5353 dpt=53 proto=udp msg=DNS_blocked policy=Block-DNS",
        "<190>Aug 20 13:01:02 r1 if=ge-0/0/1 event=link-down mac=aa:bb:cc:dd:ee:ff reason=carrier-loss",
        {
            "tenant": "demoA",
            "source": "api",
            "event_type": "app_login_failed",
            "user": "alice",
            "ip": "203.0.113.7",
            "reason": "wrong_password",
            "@timestamp": _ts(2),
        },
        {
            "tenant": "demoA",
            "source": "crowdstrike",
            "event_type": "malware_detected",
            "host": "WIN10-01",
            "process": "powershell.exe",
            "severity": 8,
            "sha256": "abc...",
            "action": "quarantine",
            "@timestamp": _ts(1.5),
        },
        {
            "tenant": "demoB",
            "source": "aws",
            "cloud": {
                "service": "iam",
                "account_id": "123456789012",
                "region": "ap-southeast-1",
            },
            "event_type": "CreateUser",
            "user": "admin",
            "@timestamp": _ts(1),
            "raw": {
                "eventName": "CreateUser",
                "requestParameters": {"userName": "temp-user"},
            },
        },
        {
            "tenant": "demoB",
            "source": "m365",
            "event_type": "UserLoggedIn",
            "user": "bob@demo.local",
            "ip": "198.51.100.23",
            "status": "Success",
            "workload": "Exchange",
            "@timestamp": _ts(0.8),
        },
        {
            "tenant": "demoA",
            "source": "ad",
            "event_id": 4625,
            "event_type": "LogonFailed",
            "user": "demo\\eve",
            "host": "DC01",
            "ip": "203.0.113.77",
            "logon_type": 3,
            "@timestamp": _ts(0.5),
        },
    ]


def seed(db: Session, with_samples: bool = True) -> None:
    settings = get_settings()

    def ensure_user(username: str, password: str, role: str, tenant: str) -> None:
        existing = db.scalar(select(User).where(User.username == username))
        if existing:
            return
        db.add(
            User(
                username=username,
                hashed_password=hash_password(password),
                role=role,
                tenant=tenant,
            )
        )

    ensure_user(settings.admin_username, settings.admin_password, "admin", settings.admin_tenant)
    ensure_user(
        settings.viewer_username, settings.viewer_password, "viewer", settings.viewer_tenant
    )

    # Second tenant viewer for RBAC demo
    ensure_user("viewer_b", "password", "viewer", "demoB")

    rule = db.scalar(select(AlertRule).where(AlertRule.name == "Failed Login Burst"))
    if not rule:
        db.add(
            AlertRule(
                name="Failed Login Burst",
                description="Alert when same IP fails login >= 3 times within 5 minutes",
                tenant=None,
                enabled=True,
                rule_type="failed_login_burst",
                window_minutes=5,
                threshold=3,
            )
        )
    db.commit()

    if with_samples:
        from sqlalchemy import func

        from app.models import Event

        count = db.scalar(select(func.count()).select_from(Event)) or 0
        if count == 0:
            normalized = []
            for item in _samples():
                if isinstance(item, str):
                    normalized.append(normalize_syslog(item, "demoA"))
                else:
                    normalized.append(normalize_any(item))
            insert_events(db, normalized)
