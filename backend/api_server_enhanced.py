"""
Enhanced MYELIN API Server with Custom Rules Support
FastAPI server integrating authentication, custom rules, and enhanced auditing
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uvicorn
import sys
import os
import logging
import asyncio
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# Add paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config.settings import settings
from backend.config.database import get_db
from backend.enhanced_orchestrator import get_enhanced_orchestrator
from backend.middleware.auth_middleware import validate_api_key, get_api_key_from_request
from backend.middleware.security_middleware import (
    CloudflareRealIPMiddleware,
    PayloadSizeLimitMiddleware,
    SecurityHeadersMiddleware,
)
from backend.middleware.rate_limiter import (
    limiter,
    rate_limit_exceeded_handler,
    LIMIT_AUDIT,
    LIMIT_AUTH,
    LIMIT_BATCH,
    LIMIT_DEFAULT,
)
from backend.middleware.bot_detection import BotDetectionMiddleware
from backend.middleware.input_sanitizer import RequestSanitizerMiddleware
from backend.middleware.anomaly_monitor import AnomalyMonitorMiddleware
from backend.services.notification_service import get_notification_service

# Import routers
from backend.api.auth import router as auth_router, api_keys_router
from backend.api.rules import router as rules_router
from backend.api.audit import router as audit_router
from backend.api.public import router as public_router

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="AI Governance and Alignment Auditor with Custom Rules Support",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ============================================================================
# SECURITY MIDDLEWARE STACK
# Middleware is applied in REVERSE registration order by Starlette, so the
# first middleware registered is the OUTERMOST layer (runs first on request,
# last on response). Stack order here, outermost -> innermost:
#
#   1. CloudflareRealIPMiddleware  — rewrite client IP from CF-Connecting-IP
#   2. TrustedHostMiddleware       — reject invalid Host headers
#   3. CORSMiddleware              — enforce origin policy
#   4. PayloadSizeLimitMiddleware  — reject oversized bodies
#   5. SecurityHeadersMiddleware   — add OWASP headers to every response
#   6. slowapi (via state)         — per-route rate limiting
# ============================================================================

# --- slowapi limiter state (must be set before any route decorator runs) ---
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# 1. Cloudflare Real-IP (outermost — must run before rate limiter key lookup)
app.add_middleware(
    CloudflareRealIPMiddleware,
    cloudflare_enabled=settings.CLOUDFLARE_ENABLED,
)

# 2. Trusted Host — reject requests with forged/unexpected Host headers
#    IMPORTANT: add your production domain to TRUSTED_HOSTS in .env
#    e.g. TRUSTED_HOSTS="api.myelin.com,localhost,127.0.0.1"
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.get_trusted_hosts(),
)

# 3. CORS — restrict cross-origin access
#    NEVER use allow_origins=["*"] with allow_credentials=True — it is
#    both insecure and rejected by all modern browsers.
#    When behind Cloudflare, the Origin header is preserved as-is so
#    exact domain matching works correctly.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=settings.get_cors_allow_methods(),
    allow_headers=settings.get_cors_allow_headers(),
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "Retry-After"],
    max_age=600,   # preflight cache 10 min
)

# 4. Payload size limit — prevent OOM from massive JSON bodies
app.add_middleware(
    PayloadSizeLimitMiddleware,
    max_body_bytes=settings.MAX_REQUEST_BODY_BYTES,
)

# 5. Security headers — OWASP hardening on every response
app.add_middleware(SecurityHeadersMiddleware)

# 6. Bot detection — blocks scrapers, scanners, known bad UAs, honeypot hits
app.add_middleware(
    BotDetectionMiddleware,
    block_threshold=settings.BOT_BLOCK_THRESHOLD,
    dry_run=settings.BOT_DRY_RUN,
)

# 7. Input sanitizer — strips XSS, CSS injection, SQL fragments from JSON bodies
app.add_middleware(
    RequestSanitizerMiddleware,
    enabled=settings.INPUT_SANITIZER_ENABLED,
)

# 8. Anomaly monitor — tracks per-IP error patterns, blocks brute-force / scanners
app.add_middleware(
    AnomalyMonitorMiddleware,
    enabled=settings.ANOMALY_MONITOR_ENABLED,
)

# Global orchestrator instance
orchestrator = None


def _schedule_flagged_report_email(user_email: Optional[str], audit_type: str, result: Dict[str, Any]):
    """Schedule flagged-report email delivery in the background if needed."""
    if not user_email:
        return

    notification_service = get_notification_service()
    if not notification_service.has_flags(result):
        return

    asyncio.create_task(asyncio.to_thread(
        notification_service.send_audit_report_if_flagged,
        user_email,
        audit_type,
        result
    ))


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global orchestrator
    orchestrator = get_enhanced_orchestrator()
    
    db = get_db()
    if db.is_connected():
        logger.info("✅ Database connected")
    else:
        logger.warning("⚠️  Database not connected - custom rules features will be disabled")
    
    logger.info("✅ Enhanced MYELIN API Server initialized")


# ============================================================================
# REQUEST/RESPONSE MODELS (from original api_server.py)
# ============================================================================

class ConversationAuditRequest(BaseModel):
    """Request model for conversation audit"""
    user_input: str = Field(..., description="User's message/query")
    bot_response: str = Field(..., description="AI-generated response")
    source_text: Optional[str] = Field(None, description="Optional source text for factual verification")


class ToxicityAuditRequest(BaseModel):
    """Request model for toxicity audit"""
    user_input: str = Field(..., description="User's message")
    bot_response: str = Field(..., description="AI's response")


class GovernanceAuditRequest(BaseModel):
    """Request model for governance audit"""
    user_input: str = Field(..., description="User's message")
    bot_response: str = Field(..., description="AI's response")


class BiasAuditRequest(BaseModel):
    """Request model for bias audit"""
    user_input: str = Field(..., description="User's message")
    bot_response: str = Field(..., description="AI's response")


# ============================================================================
# INCLUDE ROUTERS
# ============================================================================

app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(api_keys_router, prefix=settings.API_V1_PREFIX)
app.include_router(rules_router, prefix=settings.API_V1_PREFIX)
app.include_router(audit_router, prefix=settings.API_V1_PREFIX)
app.include_router(public_router, prefix=settings.API_V1_PREFIX)


# Website assets will be mounted at the very end of the file to avoid route shadowing.


# ============================================================================
# ROOT ENDPOINTS
# ============================================================================

@app.get("/status")
async def root():
    """API status endpoint (moved from root)"""
    db = get_db()
    
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "AI Governance and Alignment Auditor with Custom Rules",
        "features": {
            "default_rules": "100+ built-in rules across 5 pillars",
            "custom_rules": "Organization-specific custom rules",
            "authentication": "API key-based authentication",
            "audit_logging": "Complete audit history and statistics"
        },
        "pillars": ["fairness", "factual", "toxicity", "governance", "bias"],
        "endpoints": {
            "auth": f"{settings.API_V1_PREFIX}/auth",
            "api_keys": f"{settings.API_V1_PREFIX}/api-keys",
            "custom_rules": f"{settings.API_V1_PREFIX}/rules/custom",
            "audit": f"{settings.API_V1_PREFIX}/audit",
            "health": "/health",
            "docs": "/docs",
            "website": "/"
        },
        "database_connected": db.is_connected()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db = get_db()
    
    return {
        "status": "healthy",
        "orchestrator": "initialized" if orchestrator else "not initialized",
        "database": "connected" if db.is_connected() else "disconnected"
    }


# ============================================================================
# ENHANCED AUDIT ENDPOINTS (with custom rules)
# ============================================================================

@app.post(f"{settings.API_V1_PREFIX}/audit/conversation", tags=["Comprehensive Audit"])
@limiter.limit(LIMIT_AUDIT)
async def audit_conversation(request_data: ConversationAuditRequest, request: Request):
    """
    Run comprehensive audit on a conversation (all applicable pillars)
    
    **With API Key**: Includes custom rules + audit logging
    **Without API Key**: Default rules only
    
    This endpoint runs:
    - Toxicity check (default + custom rules)
    - Governance compliance check (default + custom rules)
    - Bias detection (default + custom rules)
    - Factual consistency check (default rules)
    
    Returns an overall risk assessment and decision.
    """
    try:
        # Try to get API key (optional for this endpoint)
        api_key = await get_api_key_from_request(request)
        
        if api_key:
            # Authenticated request - use custom rules
            from backend.services.auth_service import get_auth_service
            auth_service = get_auth_service()
            auth_context = await auth_service.validate_api_key(api_key)
            
            if auth_context:
                result = await orchestrator.audit_conversation_with_custom_rules(
                    user_input=request_data.user_input,
                    bot_response=request_data.bot_response,
                    source_text=request_data.source_text,
                    organization_id=auth_context["organization"]["id"],
                    api_key_id=auth_context["api_key"]["id"]
                )
                result["custom_rules_enabled"] = True
                _schedule_flagged_report_email(
                    user_email=auth_context["user"].get("email"),
                    audit_type="conversation",
                    result=result
                )
                return result
        
        # Unauthenticated request - default rules only
        result = orchestrator.audit_conversation(
            user_input=request_data.user_input,
            bot_response=request_data.bot_response,
            source_text=request_data.source_text
        )
        result["custom_rules_enabled"] = False
        return result
        
    except Exception as e:
        logger.error(f"Error in conversation audit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post(f"{settings.API_V1_PREFIX}/audit/toxicity", tags=["Toxicity Pillar"])
@limiter.limit(LIMIT_AUDIT)
async def audit_toxicity(request_data: ToxicityAuditRequest, request: Request):
    """
    Run toxicity audit on conversation
    
    **With API Key**: Includes custom toxicity rules
    **Without API Key**: Default rules only
    """
    try:
        api_key = await get_api_key_from_request(request)
        
        if api_key:
            from backend.services.auth_service import get_auth_service
            auth_service = get_auth_service()
            auth_context = await auth_service.validate_api_key(api_key)
            
            if auth_context:
                result = await orchestrator.audit_toxicity_with_custom_rules(
                    user_input=request_data.user_input,
                    bot_response=request_data.bot_response,
                    organization_id=auth_context["organization"]["id"],
                    api_key_id=auth_context["api_key"]["id"]
                )
                result["custom_rules_enabled"] = True
                _schedule_flagged_report_email(
                    user_email=auth_context["user"].get("email"),
                    audit_type="toxicity",
                    result=result
                )
                return result
        
        result = orchestrator.audit_toxicity(
            user_input=request_data.user_input,
            bot_response=request_data.bot_response
        )
        result["custom_rules_enabled"] = False
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(f"{settings.API_V1_PREFIX}/audit/governance", tags=["Governance Pillar"])
@limiter.limit(LIMIT_AUDIT)
async def audit_governance(request_data: GovernanceAuditRequest, request: Request):
    """
    Run governance compliance audit
    
    **With API Key**: Includes custom governance rules
    **Without API Key**: Default rules only
    """
    try:
        api_key = await get_api_key_from_request(request)
        
        if api_key:
            from backend.services.auth_service import get_auth_service
            auth_service = get_auth_service()
            auth_context = await auth_service.validate_api_key(api_key)
            
            if auth_context:
                result = orchestrator.audit_governance(
                    user_input=request_data.user_input,
                    bot_response=request_data.bot_response
                )
                result["custom_rules_enabled"] = True
                _schedule_flagged_report_email(
                    user_email=auth_context["user"].get("email"),
                    audit_type="governance",
                    result=result
                )
                return result
        
        result = orchestrator.audit_governance(
            user_input=request_data.user_input,
            bot_response=request_data.bot_response
        )
        result["custom_rules_enabled"] = False
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(f"{settings.API_V1_PREFIX}/audit/bias", tags=["Bias Pillar"])
@limiter.limit(LIMIT_AUDIT)
async def audit_bias(request_data: BiasAuditRequest, request: Request):
    """
    Run bias detection audit
    
    **With API Key**: Includes custom bias rules
    **Without API Key**: Default rules only
    """
    try:
        api_key = await get_api_key_from_request(request)
        
        if api_key:
            from backend.services.auth_service import get_auth_service
            auth_service = get_auth_service()
            auth_context = await auth_service.validate_api_key(api_key)
            
            if auth_context:
                result = orchestrator.audit_bias(
                    user_input=request_data.user_input,
                    bot_response=request_data.bot_response
                )
                result["custom_rules_enabled"] = True
                _schedule_flagged_report_email(
                    user_email=auth_context["user"].get("email"),
                    audit_type="bias",
                    result=result
                )
                return result
        
        result = orchestrator.audit_bias(
            user_input=request_data.user_input,
            bot_response=request_data.bot_response
        )
        result["custom_rules_enabled"] = False
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# BATCH ENDPOINTS
# ============================================================================

@app.post(f"{settings.API_V1_PREFIX}/audit/batch/conversations", tags=["Batch Operations"])
@limiter.limit(LIMIT_BATCH)
async def batch_audit_conversations(requests: List[ConversationAuditRequest], request: Request):
    """
    Run batch conversation audits
    
    Process multiple conversations in a single request.
    """
    try:
        api_key = await get_api_key_from_request(request)
        auth_context = None
        
        if api_key:
            from backend.services.auth_service import get_auth_service
            auth_service = get_auth_service()
            auth_context = await auth_service.validate_api_key(api_key)
        
        results = []
        for req in requests:
            if auth_context:
                result = await orchestrator.audit_conversation_with_custom_rules(
                    user_input=req.user_input,
                    bot_response=req.bot_response,
                    source_text=req.source_text,
                    organization_id=auth_context["organization"]["id"],
                    api_key_id=auth_context["api_key"]["id"]
                )
                _schedule_flagged_report_email(
                    user_email=auth_context["user"].get("email"),
                    audit_type="batch_conversation",
                    result=result
                )
            else:
                result = orchestrator.audit_conversation(
                    user_input=req.user_input,
                    bot_response=req.bot_response,
                    source_text=req.source_text
                )
            results.append(result)
        
        return {
            "batch_size": len(results),
            "custom_rules_enabled": auth_context is not None,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# ============================================================================
# STATIC FILES (WEBSITE) - MOUNTED LAST
# ============================================================================
frontend_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
    "frontend", "site", "web"
)

if os.path.exists(frontend_dir):
    # Simple root mount that worked previously for UI
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="site")
    logger.info(f"✅ Production Website mounted at root from: {frontend_dir}")
else:
    logger.warning(f"⚠️ Frontend directory not found at: {frontend_dir}")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print(f" {settings.APP_NAME} ".center(80, "="))
    print("="*80)
    print(f"\nStarting server on http://{settings.API_HOST}:{settings.API_PORT}")
    print(f"API Documentation: http://localhost:{settings.API_PORT}/docs (DEBUG only)")
    print(f"\nSecurity layers active:")
    print(f"   ✓ Cloudflare real-IP extraction (CLOUDFLARE_ENABLED={settings.CLOUDFLARE_ENABLED})")
    print(f"   ✓ Trusted Host protection ({settings.TRUSTED_HOSTS})")
    print(f"   ✓ CORS restricted to: {settings.CORS_ORIGINS}")
    print(f"   ✓ Payload size limit: {settings.MAX_REQUEST_BODY_BYTES // 1024} KB")
    print(f"   ✓ Rate limits — Audit:{settings.RATE_LIMIT_AUDIT} | Auth:{settings.RATE_LIMIT_AUTH} | Batch:{settings.RATE_LIMIT_BATCH}")
    print(f"   ✓ OWASP security headers\n")

    # Bind to 127.0.0.1 in production so only NGINX/Cloudflare Tunnel can
    # reach Uvicorn directly — never expose Uvicorn to 0.0.0.0 in production.
    host = settings.API_HOST if settings.DEBUG else "127.0.0.1"

    uvicorn.run(
        "api_server_enhanced:app",
        host=host,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        # Limit keep-alive to reduce Slowloris attack surface
        timeout_keep_alive=30,
    )
