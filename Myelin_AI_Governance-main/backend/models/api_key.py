"""
API Key Models
Pydantic models for API key management
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class APIKeyCreate(BaseModel):
    """Model for creating an API key"""
    name: Optional[str] = Field(None, max_length=255, description="Friendly name for the API key")
    rate_limit_per_minute: int = Field(default=60, ge=1, le=1000, description="Rate limit per minute")
    expires_in_days: Optional[int] = Field(None, ge=1, le=365, description="Expiration in days (optional)")


class APIKeyUpdate(BaseModel):
    """Model for updating an API key"""
    name: Optional[str] = Field(None, max_length=255)
    rate_limit_per_minute: Optional[int] = Field(None, ge=1, le=1000)
    is_active: Optional[bool] = None


class APIKey(BaseModel):
    """Complete API key model"""
    id: str
    organization_id: str
    user_id: str
    key_prefix: str
    name: Optional[str]
    created_at: datetime
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    is_active: bool
    rate_limit_per_minute: int
    
    class Config:
        from_attributes = True


class APIKeyResponse(BaseModel):
    """API key response model (without sensitive data)"""
    id: str
    key_prefix: str
    name: Optional[str]
    created_at: datetime
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    is_active: bool
    rate_limit_per_minute: int
    
    class Config:
        from_attributes = True


class APIKeyWithSecret(APIKeyResponse):
    """API key response with full key (only shown once)"""
    api_key: str = Field(..., description="Full API key - save this, it won't be shown again!")
