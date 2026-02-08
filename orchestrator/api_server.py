"""
MYELIN API Server
FastAPI-based REST API for AI Governance and Alignment Auditing
"""

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uvicorn
import sys
import os

# Add orchestrator to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from myelin_orchestrator import get_orchestrator

# Initialize FastAPI app
app = FastAPI(
    title="MYELIN API",
    description="AI Governance and Alignment Auditor - Unified API for Fairness, Factual Check, Toxicity, and Governance pillars",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator
orchestrator = None

@app.on_event("startup")
async def startup_event():
    """Initialize the orchestrator on startup"""
    global orchestrator
    orchestrator = get_orchestrator()
    print("✅ MYELIN Orchestrator initialized")


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ConversationAuditRequest(BaseModel):
    """Request model for conversation audit"""
    user_input: str = Field(..., description="User's message/query")
    bot_response: str = Field(..., description="AI-generated response")
    source_text: Optional[str] = Field(None, description="Optional source text for factual verification")
    
    class Config:
        schema_extra = {
            "example": {
                "user_input": "What is the capital of France?",
                "bot_response": "The capital of France is Paris, a beautiful city known for its art and culture.",
                "source_text": "Paris is the capital and most populous city of France."
            }
        }


class MLModelAuditRequest(BaseModel):
    """Request model for ML model fairness audit"""
    y_true: List[int] = Field(..., description="Ground truth labels (0 or 1)")
    y_pred: List[int] = Field(..., description="Model predictions (0 or 1)")
    sensitive: List[int] = Field(..., description="Sensitive attribute (0=privileged, 1=unprivileged)")
    
    class Config:
        schema_extra = {
            "example": {
                "y_true": [1, 1, 1, 1, 0, 0, 0, 0],
                "y_pred": [1, 1, 0, 1, 1, 0, 0, 0],
                "sensitive": [0, 0, 0, 0, 1, 1, 1, 1]
            }
        }


class ToxicityAuditRequest(BaseModel):
    """Request model for toxicity audit"""
    user_input: str = Field(..., description="User's message")
    bot_response: str = Field(..., description="AI's response")
    
    class Config:
        schema_extra = {
            "example": {
                "user_input": "Hello, how are you?",
                "bot_response": "I'm doing well, thank you for asking!"
            }
        }


class FactualAuditRequest(BaseModel):
    """Request model for factual consistency audit"""
    model_output: str = Field(..., description="AI-generated text to verify")
    source_text: Optional[str] = Field(None, description="Optional source/reference text")
    
    class Config:
        schema_extra = {
            "example": {
                "model_output": "The Eiffel Tower is 324 meters tall.",
                "source_text": "The Eiffel Tower is 330 meters tall including antennas."
            }
        }


class GovernanceAuditRequest(BaseModel):
    """Request model for governance audit"""
    user_input: str = Field(..., description="User's message")
    bot_response: str = Field(..., description="AI's response")
    
    class Config:
        schema_extra = {
            "example": {
                "user_input": "Can you help me with this?",
                "bot_response": "Of course! I'd be happy to help you."
            }
        }


class BiasAuditRequest(BaseModel):
    """Request model for bias audit"""
    user_input: str = Field(..., description="User's message")
    bot_response: str = Field(..., description="AI's response")
    
    class Config:
        schema_extra = {
            "example": {
                "user_input": "I am Jamal, can you help me?",
                "bot_response": "Of course! I'd be happy to assist you."
            }
        }


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "service": "MYELIN API",
        "version": "1.0.0",
        "description": "AI Governance and Alignment Auditor",
        "pillars": ["fairness", "factual", "toxicity", "governance", "bias"],
        "endpoints": {
            "comprehensive": "/api/v1/audit/conversation",
            "fairness": "/api/v1/audit/fairness",
            "factual": "/api/v1/audit/factual",
            "toxicity": "/api/v1/audit/toxicity",
            "governance": "/api/v1/audit/governance",
            "bias": "/api/v1/audit/bias"
        },
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "orchestrator": "initialized" if orchestrator else "not initialized"
    }


@app.post("/api/v1/audit/conversation", tags=["Comprehensive Audit"])
async def audit_conversation(request: ConversationAuditRequest):
    """
    Run comprehensive audit on a conversation (all applicable pillars)
    
    This endpoint runs:
    - Toxicity check
    - Governance compliance check
    - Factual consistency check
    
    Returns an overall risk assessment and decision.
    """
    try:
        result = orchestrator.audit_conversation(
            user_input=request.user_input,
            bot_response=request.bot_response,
            source_text=request.source_text
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/audit/fairness", tags=["Fairness Pillar"])
async def audit_fairness(request: MLModelAuditRequest):
    """
    Run fairness audit on ML model predictions
    
    Analyzes model predictions for bias and fairness across different groups.
    """
    try:
        result = orchestrator.audit_ml_model(
            y_true=request.y_true,
            y_pred=request.y_pred,
            sensitive=request.sensitive
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/audit/factual", tags=["Factual Check Pillar"])
async def audit_factual(request: FactualAuditRequest):
    """
    Run factual consistency check on AI-generated content
    
    Verifies factual accuracy and detects hallucinations.
    """
    try:
        result = orchestrator.audit_factual(
            model_output=request.model_output,
            source_text=request.source_text
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/audit/toxicity", tags=["Toxicity Pillar"])
async def audit_toxicity(request: ToxicityAuditRequest):
    """
    Run toxicity audit on conversation
    
    Detects toxic, harmful, and unsafe content.
    """
    try:
        result = orchestrator.audit_toxicity(
            user_input=request.user_input,
            bot_response=request.bot_response
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/audit/governance", tags=["Governance Pillar"])
async def audit_governance(request: GovernanceAuditRequest):
    """
    Run governance compliance audit
    
    Checks for policy violations and compliance issues.
    """
    try:
        result = orchestrator.audit_governance(
            user_input=request.user_input,
            bot_response=request.bot_response
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/audit/bias", tags=["Bias Pillar"])
async def audit_bias(request: BiasAuditRequest):
    """
    Run bias detection audit
    
    Detects biased responses based on names, demographics, or other sensitive attributes.
    """
    try:
        result = orchestrator.audit_bias(
            user_input=request.user_input,
            bot_response=request.bot_response
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# BATCH ENDPOINTS
# ============================================================================

@app.post("/api/v1/audit/batch/conversations", tags=["Batch Operations"])
async def batch_audit_conversations(requests: List[ConversationAuditRequest]):
    """
    Run batch conversation audits
    
    Process multiple conversations in a single request.
    """
    try:
        results = []
        for req in requests:
            result = orchestrator.audit_conversation(
                user_input=req.user_input,
                bot_response=req.bot_response,
                source_text=req.source_text
            )
            results.append(result)
        
        return {
            "batch_size": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print(" MYELIN API SERVER ".center(80, "="))
    print("="*80)
    print("\n🚀 Starting server on http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("📖 ReDoc: http://localhost:8000/redoc\n")
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
