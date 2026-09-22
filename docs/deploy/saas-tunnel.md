# Setup — SaaS / Cloud (HTTPS)

Two supported ways to give examiners a public HTTPS URL.

## Option A (used for this demo): Cloudflare Quick Tunnel

Exposes the local Appliance UI (`http://localhost:3080`) as a public `https://*.trycloudflare.com` URL. No cloud VM required.

### Prerequisites

1. Stack running: `docker compose up --build -d`
2. `cloudflared` installed (`winget install --id Cloudflare.cloudflared`)

### Start tunnel

```powershell
.\scripts\start_saas_tunnel.ps1
```

Copy the printed `https://….trycloudflare.com` URL into the README / submission form.

### Current demo URL

https://merely-gonna-charlotte-continuity.trycloudflare.com

Login: `admin` / `password`

**Caveats**

- URL changes every time the tunnel process restarts
- Requires this PC + Docker to stay online during the interview/demo window
- Quick tunnels are for demos/testing (not production SLA)

---

## Option B: Public VM + TLS reverse proxy

Run the same appliance stack on a public VM/container host and terminate TLS with nginx.

### 1) Provision a VM

Example: Ubuntu 22.04 on any cloud (4 vCPU / 8 GB RAM). Open security group ports:

- `80`, `443` (HTTP/HTTPS)
- `514/udp` (optional public syslog; often keep private)
- `22` (SSH)

Install Docker:

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

### 2) Clone & configure

```bash
git clone https://github.com/Pnt-CoMExE/log-management-demo.git logmgr
cd logmgr
cp .env.example .env
# edit SECRET_KEY and passwords before public demo
```

### 3) Generate TLS certificate (self-signed OK)

```bash
bash scripts/gen_self_signed_cert.sh
```

Creates:

- `nginx/certs/cert.pem`
- `nginx/certs/key.pem`

Browsers will warn on self-signed certs — document that examiners should proceed / accept the exception.

For production, replace with Let’s Encrypt / ACME certs pointing at your DNS name.

### 4) Start with SaaS profile

```bash
docker compose --profile saas up --build -d
```

This starts the normal stack **plus** `proxy` on `:443` / `:80` (HTTP→HTTPS redirect).

### 5) Share demo URL

- UI: `https://<public-ip-or-dns>/`
- API: `https://<public-ip-or-dns>/api/health`

Login: `admin` / `password` (change for real demos).

## Notes

- Frontend nginx already proxies `/api` to the backend inside the compose network; the SaaS proxy (Option B) adds TLS in front.
- Keep Postgres port `5432` **not** published publicly in production (remove host port mapping from `docker-compose.yml`).
