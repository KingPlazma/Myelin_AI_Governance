import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Optional

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from config import get_settings
from operational_auth import require_operational_token
from provider_client import DownstreamLLMError
from schemas import ChatCompletionRequest, HealthResponse
from service import MyelinAgentService


base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_path not in sys.path:
    sys.path.append(base_path)


settings = get_settings()
logging.basicConfig(level=getattr(logging, settings.log_level, logging.INFO))
logger = logging.getLogger("MyelinProxyAgent")
agent_service = MyelinAgentService(settings)
ops_auth = require_operational_token(settings)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("Starting %s v%s", settings.service_name, settings.service_version)
    yield


app = FastAPI(
    title=settings.service_name,
    description="Production-oriented Myelin middleware for always-on chatbot governance.",
    version=settings.service_version,
    lifespan=lifespan
)


@app.exception_handler(DownstreamLLMError)
async def downstream_exception_handler(_request: Request, exc: DownstreamLLMError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.get("/")
async def root():
    return {
        "service": settings.service_name,
        "version": settings.service_version,
        "docs": "/docs",
        "health": "/health",
        "ready": "/ready",
        "incidents": "/incidents/recent"
    }


@app.get("/health", response_model=HealthResponse)
async def health():
    reachable = await agent_service.readiness()
    return HealthResponse(
        status="healthy" if reachable else "degraded",
        service=settings.service_name,
        version=settings.service_version,
        strict_mode=settings.strict_mode,
        downstream_reachable=reachable
    )


@app.get("/ready")
async def ready():
    reachable = await agent_service.readiness()
    if not reachable:
        raise HTTPException(status_code=503, detail="Downstream LLM is not reachable")
    return {"status": "ready"}


@app.get("/incidents/recent")
async def recent_incidents(
    limit: Optional[int] = Query(default=20, ge=1, le=100),
    _authorized: bool = Depends(ops_auth)
):
    return {
        "count": limit,
        "items": agent_service.recent_incidents(limit=limit or 20)
    }


@app.get("/metrics")
async def metrics(_authorized: bool = Depends(ops_auth)):
    return {
        "service": settings.service_name,
        "version": settings.service_version,
        "provider_type": settings.provider_type,
        "counters": agent_service.current_metrics()
    }


@app.post("/v1/chat/completions")
async def proxy_chat_completions(request: ChatCompletionRequest, raw_request: Request):
    headers = {key.lower(): value for key, value in raw_request.headers.items()}
    result = await agent_service.handle_chat_completion(request=request, raw_headers=headers)
    return result


if __name__ == "__main__":
    uvicorn.run("proxy_server:app", host=settings.host, port=settings.port)
