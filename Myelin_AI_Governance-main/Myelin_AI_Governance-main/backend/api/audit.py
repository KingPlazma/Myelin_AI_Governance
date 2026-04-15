"""
Enhanced Audit API Endpoints
Audit endpoints with custom rules integration
"""

from fastapi import APIRouter, Depends, Request
from typing import List

from backend.models.audit_log import AuditLogResponse, AuditStatsResponse
from backend.services.audit_service import get_audit_service
from backend.middleware.auth_middleware import validate_api_key

router = APIRouter(prefix="/audit", tags=["Audit History"])


@router.get("/history", response_model=List[AuditLogResponse])
async def get_audit_history(
    limit: int = 100,
    offset: int = 0,
    request: Request = None,
    auth_context = Depends(validate_api_key)
):
    """
    Get audit history for the organization
    
    Returns paginated list of past audits.
    """
    audit_service = get_audit_service()
    organization = auth_context["organization"]
    
    logs = await audit_service.get_audit_history(
        organization_id=organization["id"],
        limit=limit,
        offset=offset
    )
    
    return [
        AuditLogResponse(
            id=log["id"],
            audit_type=log["audit_type"],
            overall_decision=log["overall_decision"],
            risk_level=log["risk_level"],
            triggered_rules=log.get("triggered_rules", []),
            created_at=log["created_at"]
        )
        for log in logs
    ]


@router.get("/stats", response_model=AuditStatsResponse)
async def get_audit_stats(
    request: Request,
    auth_context = Depends(validate_api_key)
):
    """
    Get audit statistics for the organization
    
    Returns aggregated statistics about audits.
    """
    audit_service = get_audit_service()
    organization = auth_context["organization"]
    
    stats = await audit_service.get_audit_stats(organization["id"])
    
    return AuditStatsResponse(**stats)
