# Ingest

UDP Syslog listener that authenticates to the backend and posts `/api/ingest/syslog`.

```bash
pip install -r requirements.txt
BACKEND_URL=http://localhost:8000 SYSLOG_PORT=5514 python syslog_server.py
```
