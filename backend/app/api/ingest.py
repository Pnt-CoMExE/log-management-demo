import json
from typing import Any

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.core.database import get_db
from app.models import User
from app.schemas import IngestResponse
from app.services.events import insert_events, run_all_alert_rules
from app.services.normalize import normalize_any, normalize_batch, normalize_syslog

router = APIRouter(prefix="/ingest", tags=["ingest"])


def _resolve_tenant(
    user: User,
    body_tenant: str | None,
    x_tenant: str | None,
) -> str:
    if user.role == "admin":
        return body_tenant or x_tenant or user.tenant
    # viewer cannot ingest by default — admin only for write
    raise HTTPException(status_code=403, detail="Ingest requires admin")


@router.post("", response_model=IngestResponse)
@router.post("/", response_model=IngestResponse, include_in_schema=False)
async def ingest_json(
    payload: dict[str, Any] | list[dict[str, Any]],
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
    x_tenant: str | None = Header(default=None, alias="X-Tenant"),
) -> IngestResponse:
    default_tenant = x_tenant or user.tenant
    if isinstance(payload, list):
        normalized = normalize_batch(payload, default_tenant)
    else:
        if user.role != "admin":
            raise HTTPException(status_code=403, detail="Admin only")
        # force tenant for non-admin would apply here; admin may set in body
        if "tenant" not in payload and x_tenant:
            payload = {**payload, "tenant": x_tenant}
        elif "tenant" not in payload:
            payload = {**payload, "tenant": user.tenant}
        normalized = [normalize_any(payload, default_tenant)]

    events = insert_events(db, normalized)
    run_all_alert_rules(db)
    return IngestResponse(
        accepted=len(events),
        normalized=[
            {
                "id": e.id,
                "tenant": e.tenant,
                "source": e.source,
                "event_type": e.event_type,
                "src_ip": e.src_ip,
            }
            for e in events
        ],
    )


@router.post("/syslog", response_model=IngestResponse)
async def ingest_syslog_line(
    body: dict[str, Any],
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
    x_tenant: str | None = Header(default=None, alias="X-Tenant"),
) -> IngestResponse:
    line = body.get("message") or body.get("line") or ""
    tenant = body.get("tenant") or x_tenant or user.tenant
    if not line:
        raise HTTPException(status_code=400, detail="message required")
    normalized = [normalize_syslog(str(line), tenant)]
    events = insert_events(db, normalized)
    run_all_alert_rules(db)
    return IngestResponse(accepted=len(events), normalized=[{"id": e.id} for e in events])


@router.post("/file", response_model=IngestResponse)
async def ingest_file(
    file: UploadFile = File(...),
    tenant: str = Form("demoA"),
    source_hint: str | None = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> IngestResponse:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    raw = (await file.read()).decode("utf-8", errors="replace")
    name = (file.filename or "").lower()
    items: list[Any] = []

    if name.endswith(".json"):
        data = json.loads(raw)
        items = data if isinstance(data, list) else [data]
    elif name.endswith(".ndjson") or name.endswith(".jsonl"):
        for line in raw.splitlines():
            line = line.strip()
            if line:
                items.append(json.loads(line))
    else:
        # treat as syslog / text lines
        for line in raw.splitlines():
            line = line.strip()
            if line:
                items.append(line)

    normalized = []
    for item in items:
        if isinstance(item, str):
            normalized.append(normalize_syslog(item, tenant))
        else:
            if source_hint and "source" not in item:
                item = {**item, "source": source_hint}
            if "tenant" not in item:
                item = {**item, "tenant": tenant}
            normalized.append(normalize_any(item, tenant, source_hint))

    events = insert_events(db, normalized)
    run_all_alert_rules(db)
    return IngestResponse(accepted=len(events), normalized=[{"id": e.id} for e in events])
