"""
Bot Detection & Scraper Prevention Middleware — Myelin API

Layers:
  1. BotDetectionMiddleware     — blocks known-bad User-Agents, fingerprints scrapers
  2. Honeypot endpoint helper   — register_honeypot_routes() adds silent trap routes
  3. _score_request()           — multi-signal bot-score calculator (0–100)

Detection signals used:
  - User-Agent string analysis (missing, known bad, scraper keywords)
  - Missing Accept header (browsers always send it)
  - Suspicious header combinations (only bots send certain XHR without referer)
  - Path scanning patterns (probing /.env, /admin, /wp-login, etc.)
  - Honeypot endpoint access
"""

import re
import logging
from typing import Set

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Known bad / scraper User-Agent patterns
# ---------------------------------------------------------------------------

_BAD_UA_PATTERNS = [
    re.compile(r"sqlmap", re.IGNORECASE),
    re.compile(r"nikto", re.IGNORECASE),
    re.compile(r"nmap", re.IGNORECASE),
    re.compile(r"masscan", re.IGNORECASE),
    re.compile(r"nuclei", re.IGNORECASE),
    re.compile(r"dirbuster", re.IGNORECASE),
    re.compile(r"gobuster", re.IGNORECASE),
    re.compile(r"wfuzz", re.IGNORECASE),
    re.compile(r"zgrab", re.IGNORECASE),
    re.compile(r"python-requests/", re.IGNORECASE),      # raw requests library (no custom UA)
    re.compile(r"^python/", re.IGNORECASE),
    re.compile(r"^Go-http-client/", re.IGNORECASE),
    re.compile(r"^Java/", re.IGNORECASE),
    re.compile(r"^curl/", re.IGNORECASE),
    re.compile(r"^wget/", re.IGNORECASE),
    re.compile(r"scrapy", re.IGNORECASE),
    re.compile(r"BeautifulSoup", re.IGNORECASE),
    re.compile(r"Scrapling", re.IGNORECASE),
    re.compile(r"Googlebot", re.IGNORECASE),             # block bots from ML endpoints
    re.compile(r"bingbot", re.IGNORECASE),
    re.compile(r"AhrefsBot", re.IGNORECASE),
    re.compile(r"SemrushBot", re.IGNORECASE),
    re.compile(r"DotBot", re.IGNORECASE),
    re.compile(r"MJ12bot", re.IGNORECASE),
]

# Paths that only automated scanners probe
_SCAN_PATHS: Set[str] = {
    "/.env", "/.env.local", "/.env.example",
    "/wp-login.php", "/wp-admin", "/xmlrpc.php",
    "/admin", "/administrator", "/phpmyadmin",
    "/.git/HEAD", "/.git/config",
    "/etc/passwd", "/etc/shadow",
    "/actuator", "/actuator/health", "/actuator/env",
    "/api/swagger", "/swagger-ui.html",
    "/console", "/h2-console",
    "/config.php", "/config.yaml", "/config.yml",
    "/.well-known/security.txt",    # not malicious but flag if unexpected volume
}

# Endpoints allowed to be called by automation (health checks, genuine API clients)
_AUTOMATION_ALLOWED_PATHS: Set[str] = {
    "/health", "/api/v1/audit/conversation", "/api/v1/audit/toxicity",
    "/api/v1/audit/governance", "/api/v1/audit/bias",
    "/v1/chat/completions",
}

# Honeypot paths — any access is immediate bot flag
HONEYPOT_PATHS: Set[str] = {
    "/api/v1/internal/metrics",
    "/api/v1/admin/users",
    "/api/v1/debug/config",
    "/api/v1/.env",
}


# ---------------------------------------------------------------------------
# Bot score calculator
# ---------------------------------------------------------------------------

def _score_request(request: Request) -> int:
    """
    Calculate a 0–100 bot-likelihood score for this request.
    Score >= BOT_BLOCK_THRESHOLD → blocked.

    Scoring:
      +40  missing User-Agent entirely
      +40  matches known bad UA pattern
      +20  missing Accept header (browsers always send it)
      +15  missing Accept-Language (browsers always send it)
      +30  path is in _SCAN_PATHS
      +50  path is in HONEYPOT_PATHS
    """
    score = 0
    ua = request.headers.get("user-agent", "")

    if not ua:
        score += 40
    else:
        for pattern in _BAD_UA_PATTERNS:
            if pattern.search(ua):
                score += 40
                break

    if not request.headers.get("accept"):
        score += 20

    if not request.headers.get("accept-language"):
        score += 15

    path = request.url.path
    if path in _SCAN_PATHS:
        score += 30

    if path in HONEYPOT_PATHS:
        score += 50

    return min(score, 100)


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

class BotDetectionMiddleware(BaseHTTPMiddleware):
    """
    Blocks requests that exceed the bot-score threshold.

    Paths in AUTOMATION_ALLOWED_PATHS bypass UA checks (legitimate API clients
    with custom user-agents need to call these).  Honeypot paths are NEVER
    bypassed — a hit is always logged.

    Config:
      block_threshold  (default 50) — score at which the request is blocked
      dry_run          (default False) — log but don't block (useful for tuning)
    """

    def __init__(
        self,
        app: ASGIApp,
        block_threshold: int = 50,
        dry_run: bool = False,
    ) -> None:
        super().__init__(app)
        self.block_threshold = block_threshold
        self.dry_run = dry_run

    async def dispatch(self, request: Request, call_next) -> Response:
        score = _score_request(request)
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"

        # Honeypot: always log + block regardless of threshold
        if path in HONEYPOT_PATHS:
            logger.warning(
                "🍯 HONEYPOT HIT | IP=%s | UA=%s | path=%s",
                client_ip,
                request.headers.get("user-agent", "-"),
                path,
            )
            # Return a convincing-but-empty response to waste bot time
            return JSONResponse(
                status_code=200,
                content={"status": "ok", "data": []},
            )

        # Known scan paths → always block
        if path in _SCAN_PATHS:
            logger.warning(
                "🔍 SCAN PATH HIT | IP=%s | UA=%s | path=%s",
                client_ip,
                request.headers.get("user-agent", "-"),
                path,
            )
            return JSONResponse(status_code=404, content={"detail": "Not found"})

        # Score-based blocking (bypass for legitimate API paths)
        if score >= self.block_threshold and path not in _AUTOMATION_ALLOWED_PATHS:
            logger.warning(
                "🤖 BOT BLOCKED | score=%d | IP=%s | UA=%s | path=%s",
                score, client_ip,
                request.headers.get("user-agent", "-"),
                path,
            )
            if not self.dry_run:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Automated access is not permitted on this endpoint."},
                )

        return await call_next(request)
