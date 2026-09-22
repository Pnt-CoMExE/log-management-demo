# Start SaaS-style public HTTPS URL via Cloudflare Quick Tunnel
# Prerequisite: docker compose stack running (UI on :3080)
# Note: the trycloudflare.com URL changes every time you restart this script.

$ErrorActionPreference = "Stop"
$ui = "http://localhost:3080"

try {
  $null = Invoke-WebRequest $ui -UseBasicParsing -TimeoutSec 5
} catch {
  Write-Host "UI not reachable at $ui — start stack first:"
  Write-Host "  docker compose up --build -d"
  exit 1
}

Write-Host "Exposing $ui as public HTTPS (Ctrl+C to stop)..."
cloudflared tunnel --url $ui
