import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import alerts, auth, events, ingest
from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.schemas import HealthResponse
from app.services.events import purge_old_events, run_all_alert_rules
from app.services.seed import seed

logger = logging.getLogger("logmgr")
settings = get_settings()
scheduler = BackgroundScheduler()


def _retention_job() -> None:
    db = SessionLocal()
    try:
        deleted = purge_old_events(db, settings.retention_days)
        logger.info("Retention purge deleted %s events", deleted)
    finally:
        db.close()


def _alert_job() -> None:
    db = SessionLocal()
    try:
        alerts_created = run_all_alert_rules(db)
        if alerts_created:
            logger.info("Created %s alerts", len(alerts_created))
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed(db, with_samples=True)
    finally:
        db.close()

    scheduler.add_job(_retention_job, "interval", hours=6, id="retention")
    scheduler.add_job(_alert_job, "interval", minutes=1, id="alerts")
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(ingest.router, prefix="/api")
app.include_router(events.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", app=settings.app_name)


# Alias for assignment sample: POST /ingest
app.include_router(ingest.router, prefix="", include_in_schema=False)

# Production SaaS: serve built React UI from the same origin
_static = Path(settings.static_dir or os.getenv("STATIC_DIR", "")).expanduser()
if _static.is_dir() and (_static / "index.html").exists():
    assets = _static / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str) -> FileResponse:
        candidate = _static / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_static / "index.html")
