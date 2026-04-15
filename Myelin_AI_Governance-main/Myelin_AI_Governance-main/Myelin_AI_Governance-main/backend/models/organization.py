"""
Organization Models
Pydantic models for organization data validation
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class OrganizationTier(str, Enum):
    """Organization tier/plan"""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class OrganizationBase(BaseModel):
    """Base organization model"""
    name: str = Field(..., min_length=1, max_length=255, description="Organization name")
    tier: OrganizationTier = Field(default=OrganizationTier.FREE, description="Organization tier")


class OrganizationCreate(OrganizationBase):
    """Model for creating an organization"""
    pass


class OrganizationUpdate(BaseModel):
    """Model for updating an organization"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    tier: Optional[OrganizationTier] = None
    is_active: Optional[bool] = None


class Organization(OrganizationBase):
    """Complete organization model"""
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class OrganizationResponse(BaseModel):
    """Organization response model"""
    id: str
    name: str
    tier: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
