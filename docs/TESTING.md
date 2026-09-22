# How to test / วิธีทดสอบ

Use either the **cloud SaaS** or the **local Appliance**. Both expose the same UI and API behavior.

| Mode | Base URL |
|------|----------|
| SaaS (recommended for examiners) | https://logmgr-saas.onrender.com |
| Local Appliance UI | http://localhost:3080 |
| Local API | http://localhost:8000 |

> First hit on free Render may take 30–60s (cold start).

---

## 0) Unit tests (developer)

```bash
pip install -r backend/requirements.txt
PYTHONPATH=backend python -m pytest tests -q
```

Expected: all tests pass.

---

## 1) Login & RBAC

1. Open the UI URL.
2. Sign in as `admin` / `password` → should see events from **demoA** and **demoB** (filter “All tenants”).
3. Logout → sign in as `viewer` / `password` → only **demoA**.
4. Logout → sign in as `viewer_b` / `password` → only **demoB**.
5. As viewer, open **Ingest** tab → should be read-only / blocked.

---

## 2) Dashboard

As `admin`:

1. Open **Dashboard**.
2. Confirm: total events, Timeline chart, Top IP / User / EventType, By source.
3. Change **Tenant** filter (`demoA` / `demoB` / All) and **Source** filter — charts/tables update.

---

## 3) HTTP JSON ingest

### From UI

1. Login as `admin` → **Ingest**.
2. Click **Send JSON** (sample failed-login payload).
3. Open **Events** → new row appears (may take a few seconds; click **Refresh**).

### From CLI (local or against SaaS)

```bash
python samples/post_logs.py --base https://logmgr-saas.onrender.com
```

Or with curl (local):

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"password"}' | jq -r .access_token)

curl -s -X POST http://localhost:8000/api/ingest \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"tenant":"demoA","source":"api","event_type":"app_login_failed","user":"alice","ip":"203.0.113.7","@timestamp":"2025-08-20T07:20:00Z"}'
```

---

## 4) File batch (AWS / M365 / AD samples)

1. As `admin` → **Ingest** → upload one of:
   - `samples/aws_cloudtrail.json` (source hint: `aws`)
   - `samples/m365_audit.json` (source hint: `m365`)
   - `samples/ad_4625.json` (source hint: `ad`)
   - `samples/batch_mixed.json`
2. Confirm events appear with correct `source` / `tenant`.

CLI:

```bash
python samples/post_logs.py --base https://logmgr-saas.onrender.com --file samples/batch_mixed.json
```

---

## 5) Syslog (Appliance only — needs local Docker)

UDP Syslog is available on the local stack (`514/udp`), not on Render SaaS.

```powershell
# Windows
.\samples\send_syslog.ps1 -HostName 127.0.0.1 -Port 514
```

```bash
# Linux / macOS
bash samples/send_syslog.sh 127.0.0.1 514
```

Within ~1 minute, firewall/network events should appear in the UI (`source=firewall` or `network`).

---

## 6) Alert rule (failed login burst)

```bash
python samples/post_logs.py --base https://logmgr-saas.onrender.com --burst
```

Then either wait up to ~1 minute, or call:

```bash
curl -X POST https://logmgr-saas.onrender.com/api/alerts/evaluate \
  -H "Authorization: Bearer $TOKEN"
```

Open UI → **Alerts** → expect something like  
`Failed login burst from 203.0.113.7`.

---

## 7) Search API

```bash
curl -s "https://logmgr-saas.onrender.com/api/events/search?source=api&limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

Or use [Postman collection](api/postman_collection.json)  
Import → set `base` + paste token from `/api/auth/login`.

---

## 8) Health / HTTPS

```bash
curl -s https://logmgr-saas.onrender.com/api/health
# {"status":"ok","app":"Log Management Demo"}
```

Browser should show a valid HTTPS padlock on the SaaS URL.

---

## Acceptance checklist (assignment)

- [ ] Appliance starts with Docker Compose (or SaaS URL opens)
- [ ] Syslog sample visible in UI within 1 minute *(Appliance)*
- [ ] `POST /ingest` JSON searchable
- [ ] Sample AWS / M365 / AD files normalize correctly
- [ ] Dashboard Top-N + Timeline + tenant/source/time filters work
- [ ] Alert rule fires and shows in Alerts
- [ ] Viewer sees only own tenant
- [ ] SaaS reachable over HTTPS

---

## Start / stop local stack

```bash
docker compose up --build -d    # start
docker compose logs -f          # logs
docker compose down             # stop
```

Windows one-liner scripts: `scripts/run.sh`, `samples/send_syslog.ps1`, `samples/post_logs.py`.
