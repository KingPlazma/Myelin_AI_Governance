"""
User Models
Pydantic models for user data validation
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """User role in organization"""
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"


class UserBase(BaseModel):
    """Base user model"""
    email: EmailStr = Field(..., description="User email address")
    full_name: Optional[str] = Field(None, max_length=255, description="User full name")
    role: UserRole = Field(default=UserRole.DEVELOPER, description="User role")


class UserCreate(UserBase):
    """Model for creating a user"""
    password: str = Field(..., min_length=8, description="User password (min 8 characters)")
    organization_name: str = Field(..., min_length=1, description="Organization name")


class UserLogin(BaseModel):
    """Model for user login"""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Model for updating a user"""
    full_name: Optional[str] = Field(None, max_length=255)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class User(UserBase):
    """Complete user model"""
    id: str
    organization_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    """User response model (without sensitive data)"""
    id: str
    email: str
    email_verified: bool = False
    full_name: Optional[str]
    role: str
    organization_id: str
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UserWithToken(UserResponse):
    """User response with authentication token"""
    access_token: str
    token_type: str = "bearer"

