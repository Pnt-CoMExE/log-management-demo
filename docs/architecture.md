# Architecture — Log Management Demo

## Overview

Demo log management platform that ingests multi-source security events, normalizes them into a central schema, stores them in PostgreSQL, exposes search/dashboard/alert APIs, and ships as:

- **Appliance**: single-host Docker Compose (UI + API + Syslog UDP + Postgres)
- **SaaS**: same stack behind an HTTPS reverse proxy (self-signed cert supported)

```
                    ┌──────────────┐
   Syslog UDP 514──►│ ingest       │──HTTP──┐
                    │ (UDP→API)    │        │
                    └──────────────┘        │
                                            ▼
   HTTP JSON ──────►┌──────────────────────────────┐
   File upload ────►│ backend (FastAPI)            │
                    │  /api/ingest  /api/events    │
                    │  /api/dashboard /api/alerts  │
                    │  AuthN JWT + RBAC            │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │ PostgreSQL 16                │
                    │ events | alerts | users      │
                    │ GIN on tags/raw JSONB        │
                    └──────────────────────────────┘
                                   ▲
   Browser ────────► frontend (React) ──/api proxy─┘
```

## Tech choices

| Layer | Choice | Why |
|-------|--------|-----|
| Ingest | Custom FastAPI + UDP syslog forwarder | Meets 2+ protocols with minimal ops |
| Storage | PostgreSQL + JSONB/GIN | Simple appliance footprint; searchable |
| Backend | FastAPI | Fast to build, typed, OpenAPI for Postman |
| UI | React + Vite + Recharts | Clear dashboard for Top N / Timeline |
| Packaging | Docker Compose | One-command appliance |

## Data flow

1. **Ingest** accepts Syslog (UDP→`/api/ingest/syslog`), HTTP JSON (`POST /api/ingest`), or file batch (`POST /api/ingest/file`).
2. **Normalize** maps vendor-specific fields → central schema (`@timestamp`, `tenant`, `source`, `src_ip`, …, `raw`, `_tags`).
3. **Store** inserts into `events` with indexes on tenant/time/source/IP/user.
4. **Alert engine** (every 1 min + on ingest) evaluates `failed_login_burst`: ≥N failures from same `src_ip` within W minutes.
5. **Retention** job deletes events older than `RETENTION_DAYS` (default 7).

## Tenant model

- Each event has a `tenant` string (`demoA`, `demoB`, …).
- JWT claims include `role` + `tenant`.
- **Admin**: can query all tenants (optional `?tenant=` filter) and ingest.
- **Viewer**: read-only, hard-filtered to their own tenant (cannot see other tenants’ events/alerts).

This is **logical multi-tenant** (shared table + row filter). Nice-to-have physical separation (schema/index per tenant) is not required for the demo.

## Sources covered

| Source | How |
|--------|-----|
| Firewall / Network | Syslog UDP + sample `.log` upload |
| API | `POST /api/ingest` JSON |
| CrowdStrike / AWS / M365 / AD | Sample JSON files + normalize mapping |

## Security

- Password hashing: bcrypt
- Auth: JWT Bearer
- RBAC: `admin` / `viewer`
- SaaS: TLS termination at nginx (self-signed OK for demo)
