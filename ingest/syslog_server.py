"""UDP Syslog receiver (port 514) that forwards normalized lines to the backend API."""

from __future__ import annotations

import asyncio
import logging
import os

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("syslog-ingest")

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")
ADMIN_USER = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASSWORD", "password")
SYSLOG_HOST = os.getenv("SYSLOG_HOST", "0.0.0.0")
SYSLOG_PORT = int(os.getenv("SYSLOG_PORT", "514"))
DEFAULT_TENANT = os.getenv("DEFAULT_TENANT", "demoA")


class SyslogProtocol(asyncio.DatagramProtocol):
    def __init__(self, queue: asyncio.Queue[str]):
        self.queue = queue

    def datagram_received(self, data: bytes, addr):  # type: ignore[override]
        try:
            message = data.decode("utf-8", errors="replace").strip()
        except Exception:
            return
        if message:
            log.info("Syslog from %s: %s", addr[0], message[:120])
            self.queue.put_nowait(message)

    def error_received(self, exc):  # type: ignore[override]
        log.error("Syslog error: %s", exc)


async def get_token(client: httpx.AsyncClient) -> str:
    r = await client.post(
        f"{BACKEND_URL}/api/auth/login",
        json={"username": ADMIN_USER, "password": ADMIN_PASS},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()["access_token"]


async def forward_loop(queue: asyncio.Queue[str]) -> None:
    async with httpx.AsyncClient() as client:
        token: str | None = None
        while True:
            message = await queue.get()
            for attempt in range(3):
                try:
                    if not token:
                        token = await get_token(client)
                    r = await client.post(
                        f"{BACKEND_URL}/api/ingest/syslog",
                        headers={"Authorization": f"Bearer {token}"},
                        json={"message": message, "tenant": DEFAULT_TENANT},
                        timeout=10,
                    )
                    if r.status_code == 401:
                        token = None
                        continue
                    r.raise_for_status()
                    break
                except Exception as exc:
                    log.warning("Forward failed (%s): %s", attempt + 1, exc)
                    await asyncio.sleep(1)
            else:
                log.error("Dropped syslog message after retries")


async def main() -> None:
    # Wait for backend
    for i in range(60):
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(f"{BACKEND_URL}/api/health", timeout=3)
                if r.status_code == 200:
                    break
        except Exception:
            pass
        await asyncio.sleep(2)
    else:
        log.error("Backend not ready; starting anyway")

    queue: asyncio.Queue[str] = asyncio.Queue()
    loop = asyncio.get_running_loop()
    transport, _ = await loop.create_datagram_endpoint(
        lambda: SyslogProtocol(queue),
        local_addr=(SYSLOG_HOST, SYSLOG_PORT),
    )
    log.info("Listening UDP syslog on %s:%s", SYSLOG_HOST, SYSLOG_PORT)
    worker = asyncio.create_task(forward_loop(queue))
    try:
        await worker
    finally:
        transport.close()


if __name__ == "__main__":
    # Prefer asyncio UDP; fall back note for privileged port
    try:
        asyncio.run(main())
    except PermissionError:
        log.error("Permission denied binding port %s — run as root or use 5514", SYSLOG_PORT)
        raise
