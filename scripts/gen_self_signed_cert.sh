#!/usr/bin/env bash
# Generate self-signed TLS cert for SaaS demo
set -euo pipefail
DIR="$(cd "$(dirname "$0")/../nginx/certs" && pwd)"
mkdir -p "$DIR"
openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
  -keyout "$DIR/key.pem" \
  -out "$DIR/cert.pem" \
  -subj "/CN=logmgr-demo/O=Intern Demo/C=TH"
echo "Wrote $DIR/cert.pem and key.pem"
