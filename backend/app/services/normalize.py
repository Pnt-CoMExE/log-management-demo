"""Normalize heterogeneous log formats into a central event schema."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

SYSLOG_PRI_RE = re.compile(r"^<(\d+)>")
KV_RE = re.compile(r"(\w+)=([^\s]+)")

FAILED_LOGIN_TYPES = {
    "app_login_failed",
    "LogonFailed",
    "login_failed",
    "failed_login",
    "UserLoginFailed",
}


def _parse_ts(value: Any) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return datetime.now(timezone.utc)


def _base(**kwargs: Any) -> dict[str, Any]:
    defaults = {
        "timestamp": datetime.now(timezone.utc),
        "tenant": "demoA",
        "source": "api",
        "vendor": None,
        "product": None,
        "event_type": None,
        "event_subtype": None,
        "severity": None,
        "action": None,
        "src_ip": None,
        "src_port": None,
        "dst_ip": None,
        "dst_port": None,
        "protocol": None,
        "user": None,
        "host": None,
        "process": None,
        "url": None,
        "http_method": None,
        "status_code": None,
        "rule_name": None,
        "rule_id": None,
        "cloud_account_id": None,
        "cloud_region": None,
        "cloud_service": None,
        "raw": None,
        "tags": [],
    }
    defaults.update({k: v for k, v in kwargs.items() if v is not None})
    return defaults


def normalize_dict(payload: dict[str, Any], default_tenant: str = "demoA") -> dict[str, Any]:
    cloud = payload.get("cloud") or {}
    if isinstance(cloud, str):
        try:
            cloud = json.loads(cloud)
        except json.JSONDecodeError:
            cloud = {}

    src_ip = payload.get("src_ip") or payload.get("ip") or payload.get("src")
    dst_ip = payload.get("dst_ip") or payload.get("dst")
    src_port = payload.get("src_port") or payload.get("spt")
    dst_port = payload.get("dst_port") or payload.get("dpt")

    tags = payload.get("_tags") or payload.get("tags") or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]

    event_type = payload.get("event_type") or payload.get("event")
    action = payload.get("action")
    if event_type in FAILED_LOGIN_TYPES and not action:
        action = "login"

    return _base(
        timestamp=_parse_ts(payload.get("@timestamp") or payload.get("timestamp")),
        tenant=payload.get("tenant") or default_tenant,
        source=str(payload.get("source") or "api").lower(),
        vendor=payload.get("vendor"),
        product=payload.get("product"),
        event_type=event_type,
        event_subtype=payload.get("event_subtype") or payload.get("event_id"),
        severity=_to_float(payload.get("severity")),
        action=action,
        src_ip=str(src_ip) if src_ip is not None else None,
        src_port=_to_int(src_port),
        dst_ip=str(dst_ip) if dst_ip is not None else None,
        dst_port=_to_int(dst_port),
        protocol=payload.get("protocol") or payload.get("proto"),
        user=payload.get("user"),
        host=payload.get("host"),
        process=payload.get("process"),
        url=payload.get("url"),
        http_method=payload.get("http_method"),
        status_code=_to_int(payload.get("status_code") or payload.get("status")),
        rule_name=payload.get("rule_name") or payload.get("policy"),
        rule_id=payload.get("rule_id"),
        cloud_account_id=cloud.get("account_id") or payload.get("cloud.account_id"),
        cloud_region=cloud.get("region") or payload.get("cloud.region"),
        cloud_service=cloud.get("service") or payload.get("cloud.service"),
        raw=payload.get("raw") if isinstance(payload.get("raw"), dict) else payload,
        tags=list(tags),
    )


def normalize_syslog(line: str, default_tenant: str = "demoA") -> dict[str, Any]:
    """Parse RFC3164-ish syslog with key=value pairs (firewall/network samples)."""
    original = line.strip()
    text = original
    pri = None
    m = SYSLOG_PRI_RE.match(text)
    if m:
        pri = int(m.group(1))
        text = text[m.end() :]

    # Strip leading timestamp + host if present: "Aug 20 12:44:56 fw01 ..."
    parts = text.split(None, 3)
    host = None
    msg = text
    if len(parts) >= 4 and re.match(r"^[A-Za-z]{3}$", parts[0]):
        host = parts[2]
        msg = parts[3]
    elif len(parts) >= 1:
        msg = text

    kv = dict(KV_RE.findall(msg))
    source = "firewall"
    if "if=" in msg or kv.get("event") in {"link-down", "link-up"}:
        source = "network"

    severity = None
    if pri is not None:
        severity = float(pri % 8)  # rough map from facility/severity

    tags = ["syslog"]
    if source == "firewall":
        tags.append("network-security")

    return _base(
        timestamp=datetime.now(timezone.utc),
        tenant=default_tenant,
        source=source,
        vendor=kv.get("vendor"),
        product=kv.get("product"),
        event_type=kv.get("event") or kv.get("msg") or "syslog",
        severity=severity,
        action=kv.get("action"),
        src_ip=kv.get("src"),
        src_port=_to_int(kv.get("spt")),
        dst_ip=kv.get("dst"),
        dst_port=_to_int(kv.get("dpt")),
        protocol=kv.get("proto"),
        host=host or kv.get("host"),
        rule_name=kv.get("policy"),
        raw={"message": original, "kv": kv},
        tags=tags,
    )


def normalize_any(
    data: Any, default_tenant: str = "demoA", source_hint: str | None = None
) -> dict[str, Any]:
    if isinstance(data, str):
        stripped = data.strip()
        if stripped.startswith("{") or stripped.startswith("["):
            parsed = json.loads(stripped)
            if isinstance(parsed, list):
                raise ValueError("Use normalize_batch for list payloads")
            return normalize_dict(parsed, default_tenant)
        return normalize_syslog(stripped, default_tenant)

    if isinstance(data, dict):
        event = normalize_dict(data, default_tenant)
        if source_hint and event.get("source") == "api":
            event["source"] = source_hint
        return event

    raise ValueError(f"Unsupported payload type: {type(data)}")


def normalize_batch(
    items: list[Any], default_tenant: str = "demoA", source_hint: str | None = None
) -> list[dict[str, Any]]:
    return [normalize_any(item, default_tenant, source_hint) for item in items]


def _to_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
