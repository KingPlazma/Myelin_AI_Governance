"""
Rate Limiter — Myelin API
Uses slowapi (a Starlette/FastAPI wrapper around the limits library).

Key design decisions:
  1. Cloudflare-aware IP key function — reads CF-Connecting-IP first so the
     limiter sees genuine visitor IPs, not Cloudflare edge IPs.
  2. Tiered limits:
       - `/auth/*`            → 20 req/min  (brute-force resistant)
       - `/audit/*` (ML)      → 10 req/min  (heavy ML computation)
       - everything else      → 60 req/min  (general API)
  3. Custom 429 handler returns a structured JSON body that matches Myelin's
     standard error schema.

Usage in FastAPI route:
    from backend.middleware.rate_limiter import limiter, LIMIT_AUDIT, LIMIT_AUTH

    @app.post("/api/v1/audit/conversation")
    @limiter.limit(LIMIT_AUDIT)
    async def audit_conversation(request: Request, ...):
        ...

    # The route MUST accept `request: Request` for slowapi to inject the key.
"""

import logging
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Key function — Cloudflare-aware
# ---------------------------------------------------------------------------

def _get_real_ip(request: Request) -> str:
    """
    Resolve the genuine client IP considering the Cloudflare proxy layer.

    Priority order:
      1. CF-Connecting-IP  — set by Cloudflare (authoritative when CF is used)
      2. X-Forwarded-For   — first entry (set by load balancers / NGINX)
      3. request.client    — direct TCP peer (fallback for local dev)
    """
    cf_ip = request.headers.get("CF-Connecting-IP")
    if cf_ip:
        return cf_ip.strip()

    x_forwarded = request.headers.get("X-Forwarded-For")
    if x_forwarded:
        # X-Forwarded-For can be a comma-separated list; leftmost is client
        return x_forwarded.split(",")[0].strip()

    return get_remote_address(request)  # stdlib fallback


# ---------------------------------------------------------------------------
# Limiter instance (shared across the app)
# ---------------------------------------------------------------------------

limiter = Limiter(
    key_func=_get_real_ip,
    default_limits=["60/minute"],
    headers_enabled=True,          # adds X-RateLimit-* headers to responses
    swallow_errors=False,          # let 500s propagate normally
)

# ---------------------------------------------------------------------------
# Named limit strings (centralised — change here, applies everywhere)
# ---------------------------------------------------------------------------

#: Heavy ML audit endpoints — protect GPU/CPU from abuse
LIMIT_AUDIT: str = "10/minute"

#: Auth endpoints — prevent brute-force / credential stuffing
LIMIT_AUTH: str = "20/minute"

#: General API (rules CRUD, stats, health)
LIMIT_DEFAULT: str = "60/minute"

#: Batch endpoints — further restricted (each item = multiple ML calls)
LIMIT_BATCH: str = "5/minute"


# ---------------------------------------------------------------------------
# 429 Error handler (register on the FastAPI app)
# ---------------------------------------------------------------------------

async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Returns a structured JSON 429 response that matches Myelin's error schema.
    Includes Retry-After so clients can implement back-off.
    """
    logger.warning(
        "⚡ Rate limit exceeded | IP=%s | path=%s | limit=%s",
        _get_real_ip(request),
        request.url.path,
        exc.detail,
    )
    retry_after = getattr(exc, "retry_after", 60)
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Too many requests. Please slow down and retry after the indicated period.",
            "limit": str(exc.detail),
            "retry_after_seconds": retry_after,
        },
        headers={
            "Retry-After": str(retry_after),
            "X-RateLimit-Limit": str(exc.detail),
        },
    )
