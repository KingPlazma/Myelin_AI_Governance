"""
Security Middleware for Myelin API
Provides multiple independent protection layers:
  1. CloudflareRealIPMiddleware  — extracts the true client IP from CF-Connecting-IP
  2. PayloadSizeLimitMiddleware  — rejects request bodies larger than configured limit
  3. SecurityHeadersMiddleware   — adds OWASP-recommended response security headers
"""

import logging
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1. Cloudflare Real-IP Middleware
# ---------------------------------------------------------------------------

class CloudflareRealIPMiddleware(BaseHTTPMiddleware):
    """
    When the application sits behind Cloudflare, every inbound TCP connection
    originates from a Cloudflare edge node, not the actual browser.
    Cloudflare injects the real visitor IP as 'CF-Connecting-IP'.

    This middleware rewrites request.client so that downstream code (including
    slowapi's rate-limiter key functions) sees the genuine visitor IP.

    SECURITY NOTE: Only trust CF-Connecting-IP when behind Cloudflare.
    If running without Cloudflare (e.g. local dev) set
    CLOUDFLARE_ENABLED=false in .env otherwise a spoofed header will be used.
    """

    def __init__(self, app: ASGIApp, cloudflare_enabled: bool = True) -> None:
        super().__init__(app)
        self.cloudflare_enabled = cloudflare_enabled

    async def dispatch(self, request: Request, call_next) -> Response:
        if self.cloudflare_enabled:
            cf_ip = request.headers.get("CF-Connecting-IP")
            if cf_ip:
                # Starlette stores client as (host, port) tuple on the scope
                request.scope["client"] = (cf_ip, 0)

        return await call_next(request)


# ---------------------------------------------------------------------------
# 2. Payload Size Limit Middleware
# ---------------------------------------------------------------------------

class PayloadSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Guard against memory-exhaustion / OOM attacks caused by oversized JSON
    payloads being passed to the ML pipeline.

    Strategy (two-pass):
      a. Read Content-Length header — if present and too large, reject early
         without reading the body at all (fast path).
      b. If Content-Length is absent (chunked / streaming), read body up to
         the limit + 1 byte. If the read exceeds the limit, reject.

    Default limit: 2 MB (2_097_152 bytes).
    """

    def __init__(self, app: ASGIApp, max_body_bytes: int = 2_097_152) -> None:
        super().__init__(app)
        self.max_body_bytes = max_body_bytes

    async def dispatch(self, request: Request, call_next) -> Response:
        # Fast-path: reject via Content-Length header before reading body
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > self.max_body_bytes:
                    logger.warning(
                        "🚫 Payload rejected — Content-Length %s > limit %s | IP=%s",
                        content_length,
                        self.max_body_bytes,
                        _get_client_ip(request),
                    )
                    return JSONResponse(
                        status_code=413,
                        content={
                            "detail": (
                                f"Request body too large. "
                                f"Maximum allowed size is "
                                f"{self.max_body_bytes // (1024 * 1024)} MB."
                            )
                        },
                    )
            except ValueError:
                pass  # malformed Content-Length — let the body read catch it

        # Slow-path: stream and enforce limit for chunked bodies
        body_chunks = []
        bytes_read = 0
        async for chunk in request.stream():
            bytes_read += len(chunk)
            if bytes_read > self.max_body_bytes:
                logger.warning(
                    "🚫 Payload rejected — streamed body > limit %s | IP=%s",
                    self.max_body_bytes,
                    _get_client_ip(request),
                )
                return JSONResponse(
                    status_code=413,
                    content={
                        "detail": (
                            f"Request body too large. "
                            f"Maximum allowed size is "
                            f"{self.max_body_bytes // (1024 * 1024)} MB."
                        )
                    },
                )
            body_chunks.append(chunk)

        # Re-attach the buffered body so the route handler can read it normally
        body = b"".join(body_chunks)
        request._body = body  # type: ignore[attr-defined]

        return await call_next(request)


# ---------------------------------------------------------------------------
# 3. Security Headers Middleware
# ---------------------------------------------------------------------------

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds OWASP-recommended HTTP security headers to every response.
    These protect against clickjacking, MIME-sniffing, XSS reflection,
    and information leakage.

    Headers added:
      - X-Content-Type-Options: nosniff
      - X-Frame-Options: DENY
      - X-XSS-Protection: 1; mode=block
      - Referrer-Policy: strict-origin-when-cross-origin
      - Permissions-Policy: camera=(), microphone=(), geolocation=()
      - Content-Security-Policy: (strict API policy — no inline scripts)
      - Strict-Transport-Security: max-age=31536000; includeSubDomains
      - Cache-Control: no-store (prevents sensitive audit data caching)
      - Server: (redacted — removes framework fingerprint)
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # --- Anti-fingerprinting ---
        response.headers["Server"] = "Myelin"

        # --- Clickjacking protection ---
        response.headers["X-Frame-Options"] = "DENY"

        # --- MIME sniffing protection ---
        response.headers["X-Content-Type-Options"] = "nosniff"

        # --- Legacy XSS filter for old browsers ---
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # --- Referrer leakage prevention ---
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # --- Browser feature/sensor restrictions ---
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )

        # --- Strict CSP for a pure API (no HTML rendering) ---
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; frame-ancestors 'none'"
        )

        # --- HSTS: instruct browsers to always use HTTPS ---
        # Only set on HTTPS responses; harmless on HTTP in development
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )

        # --- Prevent caching of sensitive API responses ---
        if request.url.path not in ("/health", "/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"

        return response


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_client_ip(request: Request) -> str:
    """Return the best-guess real client IP for logging."""
    if request.client:
        return request.client.host
    return "unknown"
