# Persistent SaaS deploy (HTTPS stays up when laptop is off)

This project can run as a **single container** (`Dockerfile.saas`) that serves both the React UI and FastAPI API, plus a managed Postgres.

## Option 1 — Render (recommended, free tier)

1. Open: https://dashboard.render.com/select-repo?type=blueprint  
2. Connect GitHub and select `Pnt-CoMExE/log-management-demo`  
3. Confirm Blueprint from `render.yaml` → **Deploy Blueprint**  
4. Wait for `logmgr-saas` + `logmgr-db` to become Live  
5. Public URL: **https://logmgr-saas.onrender.com** (already deployed)

Login: `admin` / `password`

**Notes**

- Free web services may sleep after idle; first request can take ~30–60s to wake  
- Free Postgres on Render expires after ~30 days — fine for the assignment window  
- Region set to `singapore` in `render.yaml`

## Option 2 — Fly.io

```powershell
# once
& "$env:USERPROFILE\.fly\bin\flyctl.exe" auth login

# create app + postgres + deploy
& "$env:USERPROFILE\.fly\bin\flyctl.exe" apps create logmgr-saas-pnt --org personal
& "$env:USERPROFILE\.fly\bin\flyctl.exe" postgres create --name logmgr-db-pnt --region sin --initial-cluster-size 1 --vm-size shared-cpu-1x --volume-size 1
& "$env:USERPROFILE\.fly\bin\flyctl.exe" postgres attach logmgr-db-pnt -a logmgr-saas-pnt
& "$env:USERPROFILE\.fly\bin\flyctl.exe" secrets set SECRET_KEY="$(New-Guid)" -a logmgr-saas-pnt
& "$env:USERPROFILE\.fly\bin\flyctl.exe" deploy -a logmgr-saas-pnt
```

HTTPS URL: `https://logmgr-saas-pnt.fly.dev`

## Local one-image smoke test

```powershell
docker build -f Dockerfile.saas -t logmgr-saas .
docker run --rm -p 8000:8000 -e DATABASE_URL=postgresql+psycopg2://logmgr:logmgr@host.docker.internal:5432/logmgr logmgr-saas
```
