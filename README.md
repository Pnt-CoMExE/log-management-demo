# Log Management Demo — Full-Stack Developer Intern Assignment

Demo multi-source Log Management platform with normalize → store → search → dashboard → alert, packaged as **Appliance** (Docker Compose) and **SaaS** (HTTPS).

## Links

| Item | URL |
|------|-----|
| **GitHub** | https://github.com/Pnt-CoMExE/log-management-demo |
| **SaaS (Cloudflare tunnel — live while PC on)** | https://merely-gonna-charlotte-continuity.trycloudflare.com |
| **SaaS persistent (Render/Fly)** | see [docs/setup_saas_persistent.md](docs/setup_saas_persistent.md) |
| Local UI | http://localhost:3080 |
| Local API docs | http://localhost:8000/docs |

Login: `admin` / `password`  
Viewers: `viewer` / `password` (tenant demoA), `viewer_b` / `password` (tenant demoB)

## Quick start (Appliance)

```bash
cp .env.example .env
docker compose up --build -d
```

## Persistent SaaS (laptop can be off)

Repo includes `Dockerfile.saas` + `render.yaml` + `fly.toml`.

**Fastest path — Render Blueprint:**  
https://dashboard.render.com/select-repo?type=blueprint  
→ connect `Pnt-CoMExE/log-management-demo` → Deploy Blueprint  
→ URL like `https://logmgr-saas.onrender.com`

Details: [Persistent SaaS setup](docs/setup_saas_persistent.md)

## Repository layout

```
backend/          FastAPI API + normalize + alerts + retention
frontend/         React dashboard
ingest/           UDP Syslog → API forwarder
samples/          Example logs + send scripts
docs/             Architecture & setup guides
tests/            Unit tests (normalize)
Dockerfile.saas   Single-image SaaS (UI + API)
render.yaml       Render Blueprint
fly.toml          Fly.io config
docker-compose.yml
```

## Docs

- [Architecture](docs/architecture.md)
- [Appliance setup](docs/setup_appliance.md)
- [SaaS tunnel setup](docs/setup_saas.md)
- [Persistent SaaS (Render/Fly)](docs/setup_saas_persistent.md)
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
| Appliance + SaaS | Compose + Cloudflare tunnel / Render / Fly |
| Retention 7 days | Scheduled purge |

## Tests

```bash
cd backend
pip install -r requirements.txt
cd ..
PYTHONPATH=backend python -m pytest tests -q
```
