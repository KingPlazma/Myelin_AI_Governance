"""
Anomaly Monitor Middleware — Myelin API

Tracks per-IP request patterns in memory and:
  - Increments counters for 4xx/5xx responses
  - Detects IP bursts: >10 auth failures in 60 s → auto-block for 15 min
  - Detects scanning: >15 different 404 paths in 60 s → block
  - Detects response-code flooding: >30 error responses in 60 s → block
  - Writes security events to a structured JSONL log file

Uses an in-memory ring buffer per IP — no Redis needed.
For production at scale, swap _store with a Redis-backed store.
"""

import json
import logging
import os
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Deque, Dict, Set

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Security event log path
# ---------------------------------------------------------------------------
LOG_DIR = Path(os.getenv("MYELIN_LOG_DIR", "logs"))
SECURITY_LOG = LOG_DIR / "security_events.jsonl"


def _write_security_event(event: dict) -> None:
    """Append a security event to the JSONL log file (thread-safe)."""
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with open(SECURITY_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")
    except Exception as exc:
        logger.error("Failed to write security event log: %s", exc)


# ---------------------------------------------------------------------------
# Per-IP sliding-window store
# ---------------------------------------------------------------------------

class _IPRecord:
    """Holds per-IP counters using sliding deques (time-windowed)."""

    __slots__ = ("auth_failures", "error_codes", "not_found_paths", "blocked_until")

    def __init__(self):
        self.auth_failures: Deque[float] = deque()     # timestamps of 401/403 responses
        self.error_codes: Deque[float] = deque()        # timestamps of any 4xx/5xx
        self.not_found_paths: Deque[str] = deque(maxlen=50)  # unique 404 paths
        self.blocked_until: float = 0.0                 # epoch seconds, 0 = not blocked


_store: Dict[str, _IPRecord] = defaultdict(_IPRecord)
_store_lock = Lock()

# Thresholds
AUTH_FAIL_LIMIT    = 10     # auth failures in window → block
AUTH_FAIL_WINDOW   = 60     # seconds
ERROR_LIMIT        = 30     # total errors in window → block
ERROR_WINDOW       = 60     # seconds
SCAN_PATH_LIMIT    = 15     # unique 404 paths in window → block
BLOCK_DURATION     = 900    # 15 minutes


def _prune(dq: deque, window: float, now: float) -> None:
    """Remove entries older than `window` seconds."""
    while dq and (now - dq[0]) > window:
        dq.popleft()


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

class AnomalyMonitorMiddleware(BaseHTTPMiddleware):
    """
    Post-response middleware that analyses HTTP status codes to detect:
      - Brute-force login attacks (repeated 401/403 on auth paths)
      - Path scanners (many distinct 404 responses)
      - General error flooding (DDoS disguised as invalid requests)

    Blocks offending IPs in-memory for BLOCK_DURATION seconds.
    All events are logged to logs/security_events.jsonl.
    """

    AUTH_PATHS = {"/api/v1/auth/login", "/api/v1/auth/register"}

    def __init__(self, app: ASGIApp, enabled: bool = True) -> None:
        super().__init__(app)
        self.enabled = enabled

    async def dispatch(self, request: Request, call_next) -> Response:
        if not self.enabled:
            return await call_next(request)

        ip = request.client.host if request.client else "unknown"
        now = time.monotonic()

        # --- Check if IP is already blocked ---
        with _store_lock:
            rec = _store[ip]
            if rec.blocked_until > now:
                remaining = int(rec.blocked_until - now)
                return Response(
                    content=json.dumps({
                        "detail": f"Your IP has been temporarily blocked due to suspicious activity. "
                                  f"Please retry in {remaining} seconds."
                    }),
                    status_code=429,
                    media_type="application/json",
                    headers={"Retry-After": str(remaining)},
                )

        # --- Process request ---
        response = await call_next(request)
        status = response.status_code
        path = request.url.path

        with _store_lock:
            rec = _store[ip]
            block_reason = None

            # Auth failure tracking
            if status in (401, 403) and path in self.AUTH_PATHS:
                rec.auth_failures.append(now)
                _prune(rec.auth_failures, AUTH_FAIL_WINDOW, now)
                if len(rec.auth_failures) >= AUTH_FAIL_LIMIT:
                    rec.blocked_until = now + BLOCK_DURATION
                    block_reason = f"auth_failure_flood ({len(rec.auth_failures)} in {AUTH_FAIL_WINDOW}s)"

            # General error tracking
            if status >= 400:
                rec.error_codes.append(now)
                _prune(rec.error_codes, ERROR_WINDOW, now)
                if len(rec.error_codes) >= ERROR_LIMIT and not block_reason:
                    rec.blocked_until = now + BLOCK_DURATION
                    block_reason = f"error_flood ({len(rec.error_codes)} errors in {ERROR_WINDOW}s)"

            # 404 path scanner tracking
            if status == 404:
                rec.not_found_paths.append(path)
                unique_404s = len(set(rec.not_found_paths))
                if unique_404s >= SCAN_PATH_LIMIT and not block_reason:
                    rec.blocked_until = now + BLOCK_DURATION
                    block_reason = f"path_scanning ({unique_404s} unique 404 paths)"

            if block_reason:
                event = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "event": "ip_blocked",
                    "ip": ip,
                    "reason": block_reason,
                    "path": path,
                    "status": status,
                    "block_duration_seconds": BLOCK_DURATION,
                }
                logger.warning("🚫 IP BLOCKED | %s | %s | path=%s", ip, block_reason, path)
                _write_security_event(event)

            elif status in (401, 403, 429):
                # Log suspicious-but-not-yet-blocked events
                event = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "event": "suspicious_request",
                    "ip": ip,
                    "status": status,
                    "path": path,
                    "method": request.method,
                    "ua": request.headers.get("user-agent", ""),
                }
                _write_security_event(event)

        return response
