import os
import sys
import uvicorn
import httpx
import time
import logging
import asyncio
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
import json
from datetime import datetime
from slowapi.errors import RateLimitExceeded

from agent_core import get_agent_core

# Add backend to path for optional auth + notification integration
base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_path not in sys.path:
    sys.path.append(base_path)

# Import shared security middleware from backend
try:
    from backend.middleware.security_middleware import (
        CloudflareRealIPMiddleware,
        PayloadSizeLimitMiddleware,
        SecurityHeadersMiddleware,
    )
    from backend.middleware.rate_limiter import (
        limiter,
        rate_limit_exceeded_handler,
        LIMIT_AUDIT,
    )
    _BACKEND_MW_AVAILABLE = True
except ImportError:
    _BACKEND_MW_AVAILABLE = False
    logging.getLogger("MyelinProxyAgent").warning(
        "Backend middleware not found — security layers disabled. "
        "Run from the project root so backend/ is on PYTHONPATH."
    )

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MyelinProxyAgent")

app = FastAPI(
    title="Myelin Sentinel Agent Proxy",
    description="Drop-in 24/7 AI Governance Agent",
    version="1.0.0",
    docs_url=None,    # disabled in production (no interactive docs on proxy)
    redoc_url=None,
)

# ---------------------------------------------------------------------------
# Proxy security configuration (env vars with safe defaults)
# ---------------------------------------------------------------------------
# Comma-separated trusted hostnames (same pattern as backend settings)
PROXY_TRUSTED_HOSTS: str = os.getenv(
    "PROXY_TRUSTED_HOSTS", "localhost,127.0.0.1"
)
_TRUSTED_HOST_LIST = [h.strip() for h in PROXY_TRUSTED_HOSTS.split(",") if h.strip()]

# Allowed CORS origins for the proxy (who can call the OpenAI-compat endpoint)
PROXY_CORS_ORIGINS: str = os.getenv(
    "PROXY_CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
)
_CORS_ORIGIN_LIST = [o.strip() for o in PROXY_CORS_ORIGINS.split(",") if o.strip()]

# Max payload: 2 MB (LLM messages are text — anything bigger is suspicious)
PROXY_MAX_BODY_BYTES: int = int(os.getenv("PROXY_MAX_BODY_BYTES", str(2_097_152)))

# Cloudflare sits in front of the proxy too
PROXY_CLOUDFLARE_ENABLED: bool = (
    os.getenv("PROXY_CLOUDFLARE_ENABLED", "true").lower() == "true"
)

# ---------------------------------------------------------------------------
# Middleware stack
# ---------------------------------------------------------------------------
if _BACKEND_MW_AVAILABLE:
    # slowapi state
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

    # CF real-IP (outermost)
    app.add_middleware(
        CloudflareRealIPMiddleware,
        cloudflare_enabled=PROXY_CLOUDFLARE_ENABLED,
    )

# Trusted Host (always apply — pure starlette, no backend dep)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=_TRUSTED_HOST_LIST,
)

# CORS — explicit origins, no wildcard
app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGIN_LIST,
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key", "Accept"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "Retry-After"],
    max_age=600,
)

if _BACKEND_MW_AVAILABLE:
    # Payload size limit
    app.add_middleware(
        PayloadSizeLimitMiddleware,
        max_body_bytes=PROXY_MAX_BODY_BYTES,
    )
    # OWASP security headers
    app.add_middleware(SecurityHeadersMiddleware)

# Configuration
ALLOWED_TARGET_DOMAIN = os.getenv('ALLOWED_TARGET_DOMAIN', 'localhost:11434')
TARGET_LLM_URL = os.getenv('TARGET_LLM_URL', 'http://localhost:11434/v1/chat/completions')
if ALLOWED_TARGET_DOMAIN and ALLOWED_TARGET_DOMAIN not in TARGET_LLM_URL:
    raise ValueError('TARGET_LLM_URL must be within ALLOWED_TARGET_DOMAIN')
MYELIN_STRICT_MODE = os.getenv("MYELIN_STRICT_MODE", "true").lower() == "true"
AGENT_ALERT_EMAIL = os.getenv("AGENT_ALERT_EMAIL", "")
AGENT_ALERT_EMAIL_HEADER = os.getenv("AGENT_ALERT_EMAIL_HEADER", "X-User-Email")
AGENT_ALLOW_FALLBACK_EMAIL = os.getenv("AGENT_ALLOW_FALLBACK_EMAIL", "false").lower() == "true"


def _extract_api_key_from_headers(headers: Dict[str, str]) -> Optional[str]:
    """Extract API key from standard headers."""
    api_key = headers.get("x-api-key")
    if api_key:
        return api_key

    auth_header = headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.replace("Bearer ", "", 1)

    return None


async def _resolve_alert_email(raw_request: Request) -> Optional[str]:
    """Resolve alert recipient email, preferring verified user from API key."""
    headers = {k.lower(): v for k, v in raw_request.headers.items()}

    # 1) Try to resolve from authenticated API key (verified user)
    api_key = _extract_api_key_from_headers(headers)
    if api_key:
        try:
            from backend.services.auth_service import get_auth_service
            auth_context = await get_auth_service().validate_api_key(api_key)
            if auth_context and auth_context.get("user", {}).get("email"):
                return auth_context["user"]["email"]
        except Exception as exc:
            logger.warning(f"Could not resolve email from API key: {exc}")

    # 2) Optional fallback sources when explicitly enabled
    if AGENT_ALLOW_FALLBACK_EMAIL:
        header_email = raw_request.headers.get(AGENT_ALERT_EMAIL_HEADER)
        if header_email:
            return header_email

        if AGENT_ALERT_EMAIL:
            return AGENT_ALERT_EMAIL

    return None


def _schedule_agent_flag_email(recipient_email: Optional[str], report_data: Dict[str, Any], audit_type: str):
    """Schedule non-blocking flagged report email for agent workflow."""
    if not recipient_email:
        return

    try:
        from backend.services.notification_service import get_notification_service
        notification_service = get_notification_service()
        if not notification_service.has_flags(report_data):
            return

        asyncio.create_task(asyncio.to_thread(
            notification_service.send_audit_report_if_flagged,
            recipient_email,
            audit_type,
            report_data
        ))
    except Exception as exc:
        logger.warning(f"Failed to schedule agent alert email: {exc}")

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    stream: bool = False
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Myelin Sentinel Agent...")
    # Trigger engine load
    get_agent_core()
    logger.info("Myelin Agent Engine Ready.")

@app.get("/health")
async def health():
    return {"status": "active", "agent": "Myelin Sentinel"}

@app.post("/v1/chat/completions")
async def proxy_chat_completions(request: ChatCompletionRequest, raw_request: Request):
    """
    OpenAI-compatible proxy that runs 24/7 governance.
    """
    user_prompt = request.messages[-1].content
    logger.info(f"Intercepted Prompt: {user_prompt[:50]}...")
    alert_email = await _resolve_alert_email(raw_request)

    agent_core = get_agent_core()

    # 1. PRE-AUDIT (PROMPT DEFENSE)
    # Check if the user is asking for restricted things (e.g., prompt injection)
    prompt_audit = agent_core.audit_conversation(user_prompt, bot_response="")
    if prompt_audit["overall"]["decision"] == "BLOCK" and MYELIN_STRICT_MODE:
        _schedule_agent_flag_email(
            recipient_email=alert_email,
            report_data=prompt_audit,
            audit_type="agent_prompt"
        )
        logger.warning("🚩 BLOCKING MALICIOUS PROMPT")
        return {
            "id": "myelin-blocked-" + str(int(time.time())),
            "object": "chat.completion",
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": "I apologize, but your request violates governance policies and has been blocked by the Myelin Sentinel Agent."},
                "finish_reason": "content_filter"
            }]
        }

    # 2. CALL REAL LLM
    logger.info(f"Forwarding to target LLM: {TARGET_LLM_URL}")
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            # Reconstruct payload to preserve any extra params
            payload = request.model_dump()
            headers = {k: v for k, v in raw_request.headers.items() if k.lower() not in ["host", "content-length"]}
            
            response = await client.post(TARGET_LLM_URL, json=payload, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"Error from target LLM: {response.text}")
                raise HTTPException(status_code=response.status_code, detail="Error from downstream LLM")
            
            llm_result = response.json()
            bot_reply = llm_result["choices"][0]["message"]["content"]
            
        except Exception as e:
            logger.error(f"Failed to reach target LLM: {e}")
            raise HTTPException(status_code=502, detail="Target LLM unreachable")

    # 3. POST-AUDIT (RESPONSE DEFENSE & REMEDIATION)
    logger.info("Running Response Audit...")
    response_audit = agent_core.audit_conversation(user_prompt, bot_response=bot_reply)
    _schedule_agent_flag_email(
        recipient_email=alert_email,
        report_data=response_audit,
        audit_type="agent_response"
    )
    
    # 4. AGENTIC REMEDIATION
    remediated_reply = agent_core.remediate(bot_reply, response_audit)
    
    if remediated_reply != bot_reply:
        logger.info("✨ RESPONSE REMEDIATED BY AGENT")
        llm_result["choices"][0]["message"]["content"] = remediated_reply
        # Add Myelin headers for observability
        llm_result["myelin_audit"] = response_audit["overall"]

    # --- LOGGING FOR BACKGROUND OBSERVER ---
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "user_prompt": user_prompt,
        "bot_response": bot_reply,
        "remediated_response": remediated_reply if remediated_reply != bot_reply else None,
        "risk_score": response_audit.get("overall", {}).get("risk_score", 0),
        "audit_report": response_audit,
        "alert_email": alert_email
    }
    try:
        with open("agent_logs.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        logger.error(f"Failed to log conversation for observer: {e}")

    return llm_result

if __name__ == "__main__":
    # Bind to 127.0.0.1 so only NGINX / Cloudflare Tunnel reach the proxy
    # directly. Change to "0.0.0.0" ONLY behind a proper reverse proxy.
    debug_mode = os.getenv("AGENT_DEBUG", "false").lower() == "true"
    host = "0.0.0.0" if debug_mode else "127.0.0.1"
    logger.info(
        "Starting Myelin Proxy on %s:9000 | CF=%s | TrustedHosts=%s | MaxBody=%sKB",
        host,
        PROXY_CLOUDFLARE_ENABLED,
        PROXY_TRUSTED_HOSTS,
        PROXY_MAX_BODY_BYTES // 1024,
    )
    uvicorn.run(
        app,
        host=host,
        port=9000,
        timeout_keep_alive=30,   # Slowloris mitigation
    )


