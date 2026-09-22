# Backend (FastAPI)

Auth, ingest, search, dashboard aggregates, alerts, retention.

See root [README](../README.md) and [docs/TESTING.md](../docs/TESTING.md).

```bash
pip install -r requirements.txt
# with Postgres from docker compose
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
