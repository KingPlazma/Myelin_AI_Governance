"""
Audit Log Models
Pydantic models for audit logging
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime


class AuditLogCreate(BaseModel):
    """Model for creating an audit log"""
    organization_id: str
    api_key_id: Optional[str] = None
    audit_type: str = Field(..., description="Type of audit (conversation, toxicity, etc.)")
    input_data: Dict[str, Any] = Field(..., description="Input data for the audit")
    output_data: Dict[str, Any] = Field(..., description="Output/result of the audit")
    triggered_rules: List[str] = Field(default=[], description="List of rule IDs that triggered")
    overall_decision: str = Field(..., description="Overall decision (ALLOW, BLOCK, WARN)")
    risk_level: str = Field(..., description="Risk level (LOW, MEDIUM, HIGH, CRITICAL)")


class AuditLog(AuditLogCreate):
    """Complete audit log model"""
    id: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AuditLogResponse(BaseModel):
    """Audit log response model"""
    id: str
    audit_type: str
    overall_decision: str
    risk_level: str
    triggered_rules: List[str]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AuditStatsResponse(BaseModel):
    """Audit statistics response"""
    total_audits: int
    blocked: int
    warned: int
    allowed: int
    block_rate: float

