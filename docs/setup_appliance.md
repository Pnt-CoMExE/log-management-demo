# Setup — Appliance (Docker Compose)

## Requirements

- Docker Engine 24+ / Docker Desktop
- Recommended host: Ubuntu 22.04+, 4 vCPU, 8 GB RAM, 40 GB disk
- Open ports: `3080` (UI), `8000` (API), `514/udp` (Syslog), `5432` (Postgres, optional)

## Quick start (1 command)

```bash
cp .env.example .env
docker compose up --build -d
```

Or:

```bash
bash scripts/run.sh
```

On Windows (PowerShell):

```powershell
Copy-Item .env.example .env
docker compose up --build -d
```

Wait ~1–2 minutes for healthchecks, then open:

| Service | URL |
|---------|-----|
| UI | http://localhost:3080 |
| API health | http://localhost:8000/api/health |
| OpenAPI | http://localhost:8000/docs |

### Demo accounts

| User | Password | Role | Tenant |
|------|----------|------|--------|
| `admin` | `password` | admin | demoA |
| `viewer` | `password` | viewer | demoA |
| `viewer_b` | `password` | viewer | demoB |

## Acceptance checks

### 1) Syslog → UI (< 1 minute)

Linux/macOS:

```bash
bash samples/send_syslog.sh 127.0.0.1 514
```

Windows:

```powershell
.\samples\send_syslog.ps1 -HostName 127.0.0.1 -Port 514
```

If binding UDP 514 fails on the host, change compose mapping to `"5514:514/udp"` and send to port `5514`.

### 2) HTTP JSON ingest

```bash
python samples/post_logs.py --base http://localhost:8000
```

Or curl:

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"password"}' | jq -r .access_token)

curl -s -X POST http://localhost:8000/api/ingest \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"tenant":"demoA","source":"api","event_type":"app_login_failed","user":"alice","ip":"203.0.113.7","@timestamp":"2025-08-20T07:20:00Z"}'
```

### 3) File batch (AWS / M365 / AD)

In UI → **Ingest** → upload `samples/aws_cloudtrail.json` (set source hint), or:

```bash
python samples/post_logs.py --base http://localhost:8000 --file samples/batch_mixed.json
```

### 4) Alert rule

```bash
python samples/post_logs.py --base http://localhost:8000 --burst
curl -X POST http://localhost:8000/api/alerts/evaluate -H "Authorization: Bearer $TOKEN"
```

Then open UI → **Alerts**.

### 5) RBAC

1. Login as `viewer` → only `demoA` events.
2. Login as `viewer_b` → only `demoB` events.
3. Login as `admin` → filter All / demoA / demoB.

## Stop

```bash
docker compose down
```

Data persists in the `pgdata` volume. To wipe:

```bash
docker compose down -v
```
