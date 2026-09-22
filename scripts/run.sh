#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
docker compose up --build -d
echo ""
echo "UI:      http://localhost:3080"
echo "API:     http://localhost:8000/api/health"
echo "Syslog:  UDP localhost:514"
echo "Login:   admin / password"
