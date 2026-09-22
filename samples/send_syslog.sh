#!/usr/bin/env bash
# Send sample syslog lines to local UDP 514 (or 5514)
set -euo pipefail
HOST="${1:-127.0.0.1}"
PORT="${2:-514}"

send() {
  local msg="$1"
  if command -v nc >/dev/null 2>&1; then
    printf '%s\n' "$msg" | nc -u -w1 "$HOST" "$PORT"
  else
    python - <<PY
import socket
s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.sendto("""$msg""".encode(), ("$HOST", int("$PORT")))
s.close()
PY
  fi
  echo "sent: $msg"
}

send '<134>Aug 20 12:44:56 fw01 vendor=demo product=ngfw action=deny src=10.0.1.10 dst=8.8.8.8 spt=5353 dpt=53 proto=udp msg=DNS_blocked policy=Block-DNS'
send '<190>Aug 20 13:01:02 r1 if=ge-0/0/1 event=link-down mac=aa:bb:cc:dd:ee:ff reason=carrier-loss'
echo "Done. Check UI within ~1 minute."
