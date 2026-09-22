# Backend

FastAPI service for auth, ingest, search, dashboard, and alerts.

```bash
pip install -r requirements.txt
export DATABASE_URL=postgresql+psycopg2://logmgr:logmgr@localhost:5432/logmgr
uvicorn app.main:app --reload --app-dir .
```

Or run via Docker Compose from repo root.
