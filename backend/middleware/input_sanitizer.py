"""
Input Sanitizer Middleware — Myelin API
Strips XSS payloads, HTML injection, CSS injection, SQL fragments,
and prompt-injection patterns from all incoming string fields before
they reach the ML pipeline or the database.

Layers:
  1. RequestSanitizerMiddleware  — inspects raw JSON body, cleans strings
  2. sanitize_string()           — reusable per-field sanitizer
  3. INJECTION_PATTERNS          — compiled regex catalogue of known attack patterns
"""

import re
import json
import logging
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Compiled attack-pattern catalogue
# ---------------------------------------------------------------------------

_XSS_PATTERNS = [
    re.compile(r"<\s*script[\s\S]*?>[\s\S]*?<\s*/\s*script\s*>", re.IGNORECASE),
    re.compile(r"<\s*script[^>]*>", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"vbscript\s*:", re.IGNORECASE),
    re.compile(r"on\w+\s*=\s*[\"']?[^\"'>]*[\"']?", re.IGNORECASE),   # onerror=, onload=, etc.
    re.compile(r"<\s*iframe[\s\S]*?>", re.IGNORECASE),
    re.compile(r"<\s*object[\s\S]*?>", re.IGNORECASE),
    re.compile(r"<\s*embed[\s\S]*?>", re.IGNORECASE),
    re.compile(r"<\s*img[^>]+src\s*=\s*[\"']?\s*javascript:", re.IGNORECASE),
    re.compile(r"eval\s*\(", re.IGNORECASE),
    re.compile(r"expression\s*\(", re.IGNORECASE),          # CSS expression()
    re.compile(r"data\s*:\s*text/html", re.IGNORECASE),     # data URI XSS
    re.compile(r"&#x?\d+;", re.IGNORECASE),                 # HTML entity encoding of < >
]

_SQL_PATTERNS = [
    re.compile(r"(--|#|/\*|\*/)", re.IGNORECASE),           # SQL comment starters
    re.compile(r"\b(DROP|ALTER|TRUNCATE|DELETE|INSERT|UPDATE|EXEC|EXECUTE)\b", re.IGNORECASE),
    re.compile(r"\bUNION\b.{0,20}\bSELECT\b", re.IGNORECASE),
    re.compile(r"\bOR\b\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+", re.IGNORECASE),  # OR 1=1
    re.compile(r"'\s*;\s*--", re.IGNORECASE),
]

_PROMPT_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions?", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?previous", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(?:a|an)\s+\w+", re.IGNORECASE),
    re.compile(r"act\s+as\s+(?:a|an|if)\s+", re.IGNORECASE),
    re.compile(r"jailbreak", re.IGNORECASE),
    re.compile(r"DAN\s+mode", re.IGNORECASE),               # Do Anything Now jailbreak
    re.compile(r"system\s*:\s*you\s+are", re.IGNORECASE),
    re.compile(r"\[INST\]|\[\/INST\]|\<\|im_start\|\>", re.IGNORECASE),  # LLM special tokens
]

_CSS_INJECTION_PATTERNS = [
    re.compile(r"url\s*\(\s*[\"']?javascript:", re.IGNORECASE),
    re.compile(r"-moz-binding\s*:", re.IGNORECASE),
    re.compile(r"@import\s+url", re.IGNORECASE),
    re.compile(r"behavior\s*:\s*url", re.IGNORECASE),
]

# Fields whose content comes from the ML audit payload — more permissive
ML_TEXT_FIELDS = {"user_input", "bot_response", "source_text", "test_input", "test_response"}


# ---------------------------------------------------------------------------
# Core sanitizer function
# ---------------------------------------------------------------------------

def sanitize_string(value: str, field_name: str = "", strict: bool = False) -> str:
    """
    Clean a string value against known injection patterns.

    For ML text fields (user_input, bot_response, etc.) we only strip the most
    dangerous structural attacks (XSS, script tags) and flag prompt injection in
    logs — we do NOT strip the text itself, as that would corrupt audit data.

    For all other fields (names, emails, rule names, etc.) we run full strict
    sanitization.
    """
    if not isinstance(value, str):
        return value

    is_ml_field = field_name in ML_TEXT_FIELDS

    # --- XSS: always strip script/event-handler injections ---
    cleaned = value
    for pattern in _XSS_PATTERNS:
        cleaned = pattern.sub("", cleaned)

    # --- CSS injection ---
    for pattern in _CSS_INJECTION_PATTERNS:
        cleaned = pattern.sub("", cleaned)

    if not is_ml_field:
        # --- SQL injection (only for non-ML fields; ML text may contain SQL keywords) ---
        for pattern in _SQL_PATTERNS:
            if pattern.search(cleaned):
                logger.warning(
                    "🚨 Possible SQL injection detected in field '%s': %.80s",
                    field_name, cleaned
                )
                # Replace dangerous construct rather than the whole value
                cleaned = pattern.sub("[FILTERED]", cleaned)

    # --- Prompt injection: log and flag but preserve for ML analysis ---
    for pattern in _PROMPT_INJECTION_PATTERNS:
        if pattern.search(cleaned):
            logger.warning(
                "⚠️  Prompt-injection pattern detected in field '%s': %.80s",
                field_name, cleaned
            )
            # For ML fields keep the text (the ML will handle it); for others strip it
            if not is_ml_field:
                cleaned = pattern.sub("[FILTERED]", cleaned)

    return cleaned


def _sanitize_recursive(obj: Any, depth: int = 0) -> Any:
    """Recursively sanitize all strings in a JSON-decoded object."""
    if depth > 10:  # prevent stack overflow on deeply nested payloads
        return obj
    if isinstance(obj, str):
        return sanitize_string(obj)
    if isinstance(obj, dict):
        return {k: _sanitize_recursive(sanitize_string(v, k) if isinstance(v, str) else v, depth + 1)
                for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_recursive(item, depth + 1) for item in obj]
    return obj


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

class RequestSanitizerMiddleware(BaseHTTPMiddleware):
    """
    Middleware that sanitizes every incoming JSON request body.

    Only runs on POST/PUT/PATCH requests that declare Content-Type: application/json.
    GET requests (query params) are sanitized at the route level via Pydantic validators.

    If the body fails JSON parsing after sanitization the request is passed through
    unchanged (FastAPI's own JSON parser will handle the error).
    """

    SANITIZE_METHODS = {"POST", "PUT", "PATCH"}

    def __init__(self, app: ASGIApp, enabled: bool = True) -> None:
        super().__init__(app)
        self.enabled = enabled

    async def dispatch(self, request: Request, call_next) -> Response:
        if not self.enabled:
            return await call_next(request)

        if request.method not in self.SANITIZE_METHODS:
            return await call_next(request)

        content_type = request.headers.get("content-type", "")
        if "application/json" not in content_type:
            return await call_next(request)

        # Read + parse body
        try:
            raw_body = await request.body()
            if not raw_body:
                return await call_next(request)

            data = json.loads(raw_body)
            sanitized = _sanitize_recursive(data)
            sanitized_body = json.dumps(sanitized).encode("utf-8")

            # Patch body back onto the request scope
            request._body = sanitized_body  # type: ignore[attr-defined]

        except (json.JSONDecodeError, Exception):
            # Body is not valid JSON — let FastAPI's validator handle it
            pass

        return await call_next(request)
