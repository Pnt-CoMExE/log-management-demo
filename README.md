# Log Management Demo — Full-Stack Developer Intern Assignment

Demo multi-source Log Management platform with normalize → store → search → dashboard → alert, packaged as **Appliance** (Docker Compose) and **SaaS** (HTTPS public URL).

## Links

| Item | URL |
|------|-----|
| **GitHub** | https://github.com/Pnt-CoMExE/log-management-demo |
| **SaaS demo (HTTPS)** | https://merely-gonna-charlotte-continuity.trycloudflare.com |
| Local UI | http://localhost:3080 |
| Local API docs | http://localhost:8000/docs |

Login: `admin` / `password`  
Viewers: `viewer` / `password` (tenant demoA), `viewer_b` / `password` (tenant demoB)

> **SaaS note:** The public URL is a Cloudflare Quick Tunnel to this machine’s Docker stack. It stays up while `cloudflared` + `docker compose` are running. To recreate after restart: `.\scripts\start_saas_tunnel.ps1` (URL will change).

## Quick start (Appliance)

```bash
cp .env.example .env
docker compose up --build -d
```

## Repository layout

```
backend/          FastAPI API + normalize + alerts + retention
frontend/         React dashboard
ingest/           UDP Syslog → API forwarder
samples/          Example logs + send scripts
docs/             Architecture & setup guides
tests/            Unit tests (normalize)
docker-compose.yml
```

## Docs

- [Architecture](docs/architecture.md)
- [Appliance setup](docs/setup_appliance.md)
- [SaaS setup](docs/setup_saas.md)
- [Postman collection](docs/postman_collection.json)

## Features mapped to assignment

| Requirement | Implementation |
|-------------|----------------|
| ≥4 ingest sources | Syslog, HTTP JSON, file batch, sample CS/AWS/M365/AD |
| ≥2 protocols | UDP Syslog + HTTP |
| Normalization | Central schema in `backend/app/services/normalize.py` |
| Storage & search | PostgreSQL + filters/API |
| Dashboard | Top IP/User/EventType, timeline, filters |
| Alert | Failed login burst (same IP, 5 min) |
| AuthZ | Admin / Viewer + tenant isolation |
| Appliance + SaaS | Compose + Cloudflare HTTPS tunnel |
| Retention 7 days | Scheduled purge |

## Tests

```bash
cd backend
pip install -r requirements.txt
cd ..
PYTHONPATH=backend python -m pytest tests -q
```
