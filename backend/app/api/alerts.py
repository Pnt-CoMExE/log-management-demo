from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.core.database import get_db
from app.models import Alert, AlertRule, User
from app.schemas import AlertOut, AlertRuleCreate, AlertRuleOut
from app.services.events import run_all_alert_rules

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertOut])
def list_alerts(
    tenant: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> list[AlertOut]:
    stmt = select(Alert).order_by(desc(Alert.created_at)).limit(limit)
    if current.role == "admin":
        if tenant:
            stmt = stmt.where(Alert.tenant == tenant)
    else:
        stmt = stmt.where(Alert.tenant == current.tenant)
    rows = db.scalars(stmt).all()
    return [AlertOut.model_validate(r) for r in rows]


@router.get("/rules", response_model=list[AlertRuleOut])
def list_rules(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> list[AlertRuleOut]:
    rows = db.scalars(select(AlertRule).order_by(AlertRule.id)).all()
    return [AlertRuleOut.model_validate(r) for r in rows]


@router.post("/rules", response_model=AlertRuleOut)
def create_rule(
    body: AlertRuleCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> AlertRuleOut:
    rule = AlertRule(**body.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return AlertRuleOut.model_validate(rule)


@router.post("/evaluate", response_model=list[AlertOut])
def evaluate_now(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[AlertOut]:
    alerts = run_all_alert_rules(db)
    return [AlertOut.model_validate(a) for a in alerts]


@router.patch("/{alert_id}/ack", response_model=AlertOut)
def ack_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> AlertOut:
    alert = db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    if current.role != "admin" and alert.tenant != current.tenant:
        raise HTTPException(status_code=403, detail="Forbidden")
    alert.status = "acked"
    db.commit()
    db.refresh(alert)
    return AlertOut.model_validate(alert)
