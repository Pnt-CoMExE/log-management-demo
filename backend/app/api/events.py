from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import User
from app.schemas import DashboardSummary, EventOut, SearchResponse
from app.services.events import dashboard_summary, search_events

router = APIRouter(tags=["events"])


@router.get("/events/search", response_model=SearchResponse)
def events_search(
    tenant: str | None = None,
    source: str | None = None,
    event_type: str | None = None,
    src_ip: str | None = None,
    user: str | None = None,
    q: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> SearchResponse:
    total, items = search_events(
        db,
        role=current.role,
        user_tenant=current.tenant,
        tenant=tenant,
        source=source,
        event_type=event_type,
        src_ip=src_ip,
        user=user,
        q=q,
        start=start,
        end=end,
        limit=limit,
        offset=offset,
    )
    return SearchResponse(total=total, items=[EventOut.model_validate(i) for i in items])


@router.get("/dashboard/summary", response_model=DashboardSummary)
def get_dashboard(
    tenant: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> DashboardSummary:
    data = dashboard_summary(
        db,
        role=current.role,
        user_tenant=current.tenant,
        tenant=tenant,
        start=start,
        end=end,
    )
    return DashboardSummary(**data)
