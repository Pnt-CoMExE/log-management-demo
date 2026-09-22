# Log Management Demo

Centralized security log platform for the **Full-Stack Developer Intern** assignment: ingest multi-source events, normalize them, search/visualize, and alert — runnable as a local **Appliance** or cloud **SaaS**.

---

## What this product is for

Security teams (SOC / IT) receive logs from many systems — firewalls, cloud APIs, endpoints, identity — in different formats. Without a single place to land them, analysts cannot search or correlate incidents quickly.

**This demo** shows a compact Log Management console that:

1. **Ingests** events from multiple sources (Syslog, HTTP JSON, file batch, sample CrowdStrike / AWS / M365 / AD)
2. **Normalizes** every event into one common schema
3. **Stores** events so they can be filtered and searched by tenant, source, time, IP, user
4. **Visualizes** volume and Top-N on a dashboard
5. **Alerts** on a simple detection rule (failed-login burst from the same IP)
6. **Enforces** login + roles (Admin / Viewer) and tenant isolation

It is intentionally a **demo**, not a full SIEM — enough to prove full-stack design, data pipeline, security basics, and dual deployment modes.

---

## Live demos

| Environment | URL |
|-------------|-----|
| **SaaS (Render, HTTPS, PC can be off)** | https://logmgr-saas.onrender.com |
| **GitHub repository** | https://github.com/Pnt-CoMExE/log-management-demo |
| Local Appliance UI | http://localhost:3080 |
| Local API (OpenAPI) | http://localhost:8000/docs |

**Demo accounts**

| User | Password | Role | Tenant |
|------|----------|------|--------|
| `admin` | `password` | Admin (all tenants, can ingest) | demoA |
| `viewer` | `password` | Viewer (read-only) | demoA |
| `viewer_b` | `password` | Viewer (read-only) | demoB |

> Free Render instances may sleep after idle; the first request can take ~30–60 seconds.

---

## Quick start (Appliance)

```bash
cp .env.example .env
docker compose up --build -d
```

Then open http://localhost:3080 — see **[docs/TESTING.md](docs/TESTING.md)** for the full acceptance checklist.

---

## Repository structure

```text
.
├── README.md                 # This file
├── docker-compose.yml        # Appliance stack
├── Dockerfile.saas           # Single image (UI + API) for cloud
├── render.yaml / fly.toml    # Cloud deploy configs
├── Makefile
├── .env.example
│
├── backend/                  # FastAPI — auth, ingest, search, alerts
├── frontend/                 # React operations console
├── ingest/                   # UDP Syslog → API forwarder
├── samples/                  # Example logs + send scripts
├── tests/                    # Unit tests
├── nginx/                    # Optional TLS reverse proxy (VM SaaS)
├── scripts/                  # Helper scripts
│
└── docs/
    ├── README.md             # Documentation index
    ├── PURPOSE.md            # Product purpose (Thai + EN)
    ├── TESTING.md            # How to test / acceptance checklist
    ├── LINKS.md              # Live URLs
    ├── architecture.md       # Design & data flow
    ├── assignment/           # Original assignment PDF
    ├── api/                  # Postman collection
    └── deploy/               # Appliance & SaaS setup guides
```

---

## Documentation

| Doc | Description |
|-----|-------------|
| [Purpose](docs/PURPOSE.md) | Why this website exists |
| [How to test](docs/TESTING.md) | Step-by-step verification |
| [Demo script (TH)](docs/DEMO_SCRIPT_TH.md) | Thai speaking script for video/interview |
| [Architecture](docs/architecture.md) | Components & tenant model |
| [Appliance deploy](docs/deploy/appliance.md) | Docker Compose on one host |
| [SaaS on Render](docs/deploy/saas-render.md) | Persistent HTTPS |
| [SaaS tunnel](docs/deploy/saas-tunnel.md) | Cloudflare quick tunnel |
| [Postman](docs/api/postman_collection.json) | API collection |
| [Assignment PDF](docs/assignment/FullStack_Developer_Intern_Assignment_TH.pdf) | Original brief |

---

## Feature coverage

| Requirement | Implementation |
|-------------|----------------|
| ≥4 ingest sources | Syslog, HTTP JSON, file batch, CS / AWS / M365 / AD samples |
| ≥2 protocols | UDP Syslog + HTTP |
| Normalization | Shared schema in `backend/app/services/normalize.py` |
| Storage & search | PostgreSQL + filtered search API |
| Dashboard | Top IP / User / EventType, timeline, filters |
| Alert | Failed login burst (same IP, 5 minutes) |
| AuthZ | Admin / Viewer + tenant isolation |
| Appliance + SaaS | Docker Compose + Render HTTPS |
| Retention 7 days | Scheduled purge job |

---

## License / notice

Built as an internship selection demo. Demo credentials are intentionally weak — change `SECRET_KEY` and passwords before any real-world use.
