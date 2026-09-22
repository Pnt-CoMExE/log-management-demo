# Setup — SaaS / Cloud (HTTPS)

Run the same appliance stack on a public VM/container host and terminate TLS with nginx.

## 1) Provision a VM

Example: Ubuntu 22.04 on any cloud (4 vCPU / 8 GB RAM). Open security group ports:

- `80`, `443` (HTTP/HTTPS)
- `514/udp` (optional public syslog; often keep private)
- `22` (SSH)

Install Docker:

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

## 2) Clone & configure

```bash
git clone <your-repo-url> logmgr
cd logmgr
cp .env.example .env
# edit SECRET_KEY and passwords before public demo
```

## 3) Generate TLS certificate (self-signed OK)

```bash
bash scripts/gen_self_signed_cert.sh
```

Creates:

- `nginx/certs/cert.pem`
- `nginx/certs/key.pem`

Browsers will warn on self-signed certs — document that examiners should proceed / accept the exception.

For production, replace with Let’s Encrypt / ACME certs pointing at your DNS name.

## 4) Start with SaaS profile

```bash
docker compose --profile saas up --build -d
```

This starts the normal stack **plus** `proxy` on `:443` / `:80` (HTTP→HTTPS redirect).

## 5) Share demo URL

- UI: `https://<public-ip-or-dns>/`
- API: `https://<public-ip-or-dns>/api/health`

Login: `admin` / `password` (change for real demos).

## Notes

- Frontend nginx already proxies `/api` to the backend inside the compose network; the SaaS proxy adds TLS in front.
- If you use a domain, set DNS A record to the VM and optionally swap self-signed for real certs under `nginx/certs/`.
- Keep Postgres port `5432` **not** published publicly in production (remove host port mapping from `docker-compose.yml`).
