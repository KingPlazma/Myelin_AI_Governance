"""
Authentication API Endpoints
Handles user registration, login, and API key management
"""

from fastapi import APIRouter, HTTPException, status, Depends, Request
from typing import List
from pydantic import BaseModel, EmailStr

from backend.models.user import UserCreate, UserLogin, UserResponse, UserWithToken
from backend.models.api_key import APIKeyCreate, APIKeyResponse, APIKeyWithSecret, APIKeyUpdate
from backend.services.auth_service import get_auth_service
from backend.middleware.auth_middleware import validate_api_key, get_current_user, get_current_organization

router = APIRouter(prefix="/auth", tags=["Authentication"])
api_keys_router = APIRouter(prefix="/api-keys", tags=["API Keys"])


class ResendVerificationRequest(BaseModel):
    """Request model for verification email resend."""
    email: EmailStr


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@router.post("/register", response_model=UserWithToken, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """
    Register a new user and organization
    
    Creates a new organization and admin user account.
    Returns user data with access token.
    """
    auth_service = get_auth_service()
    
    user, organization = await auth_service.register_user(user_data)
    
    # Generate initial API key
    api_key, api_key_record = await auth_service.create_api_key(
        user_id=user["id"],
        organization_id=organization["id"],
        key_data=APIKeyCreate(name="Default API Key")
    )
    
    return UserWithToken(
        id=user["id"],
        email=user["email"],
        email_verified=user.get("email_verified", False),
        full_name=user.get("full_name"),
        role=user["role"],
        organization_id=user["organization_id"],
        is_active=user["is_active"],
        created_at=user["created_at"],
        access_token=api_key,
        token_type="bearer"
    )


@router.post("/login", response_model=UserWithToken)
async def login(login_data: UserLogin):
    """
    Login with email and password
    
    Returns user data with access token (API key).
    """
    auth_service = get_auth_service()
    
    user = await auth_service.login_user(login_data)
    
    # Get user's API keys
    from backend.config.database import get_db
    db = get_db()
    api_keys = await db.list_api_keys(user["organization_id"])
    
    # Get first active API key or create new one
    active_key = None
    for key in api_keys:
        if key.get("is_active") and key.get("user_id") == user["id"]:
            active_key = key
            break
    
    if not active_key:
        # Create new API key
        api_key, api_key_record = await auth_service.create_api_key(
            user_id=user["id"],
            organization_id=user["organization_id"],
            key_data=APIKeyCreate(name="Login API Key")
        )
        access_token = api_key
    else:
        # Return existing key prefix (full key not available)
        access_token = active_key["key_prefix"] + "..." 
    
    return UserWithToken(
        id=user["id"],
        email=user["email"],
        email_verified=user.get("email_verified", False),
        full_name=user.get("full_name"),
        role=user["role"],
        organization_id=user["organization_id"],
        is_active=user["is_active"],
        created_at=user["created_at"],
        access_token=access_token,
        token_type="bearer"
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(request: Request, auth_context = Depends(validate_api_key)):
    """
    Get current authenticated user information
    
    Requires valid API key in X-API-Key header or Authorization: Bearer header.
    """
    user = auth_context["user"]
    
    return UserResponse(
        id=user["id"],
        email=user["email"],
        email_verified=user.get("email_verified", False),
        full_name=user.get("full_name"),
        role=user["role"],
        organization_id=user["organization_id"],
        is_active=user["is_active"],
        created_at=user["created_at"]
    )


@router.get("/verify-email")
async def verify_email(token: str):
    """
    Verify user email using a token sent to the registered email address.
    """
    auth_service = get_auth_service()
    user = await auth_service.verify_user_email(token)

    return {
        "message": "Email verified successfully",
        "user_id": user["id"],
        "email": user["email"],
        "email_verified": user.get("email_verified", True)
    }


@router.post("/resend-verification")
async def resend_verification_email(payload: ResendVerificationRequest):
    """
    Resend email verification link for users who have not verified yet.
    """
    auth_service = get_auth_service()
    return await auth_service.resend_verification_email(str(payload.email))


# ============================================================================
# API KEY MANAGEMENT ENDPOINTS
# ============================================================================

@api_keys_router.post("", response_model=APIKeyWithSecret, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: APIKeyCreate,
    request: Request,
    auth_context = Depends(validate_api_key)
):
    """
    Generate a new API key
    
    The full API key is only shown once. Save it securely!
    """
    auth_service = get_auth_service()
    user = auth_context["user"]
    organization = auth_context["organization"]
    
    api_key, api_key_record = await auth_service.create_api_key(
        user_id=user["id"],
        organization_id=organization["id"],
        key_data=key_data
    )
    
    return APIKeyWithSecret(
        id=api_key_record["id"],
        key_prefix=api_key_record["key_prefix"],
        name=api_key_record.get("name"),
        created_at=api_key_record["created_at"],
        last_used_at=api_key_record.get("last_used_at"),
        expires_at=api_key_record.get("expires_at"),
        is_active=api_key_record["is_active"],
        rate_limit_per_minute=api_key_record["rate_limit_per_minute"],
        api_key=api_key
    )


@api_keys_router.get("", response_model=List[APIKeyResponse])
async def list_api_keys(request: Request, auth_context = Depends(validate_api_key)):
    """
    List all API keys for the organization
    """
    from backend.config.database import get_db
    db = get_db()
    organization = auth_context["organization"]
    
    api_keys = await db.list_api_keys(organization["id"])
    
    return [
        APIKeyResponse(
            id=key["id"],
            key_prefix=key["key_prefix"],
            name=key.get("name"),
            created_at=key["created_at"],
            last_used_at=key.get("last_used_at"),
            expires_at=key.get("expires_at"),
            is_active=key["is_active"],
            rate_limit_per_minute=key["rate_limit_per_minute"]
        )
        for key in api_keys
    ]


@api_keys_router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: str,
    request: Request,
    auth_context = Depends(validate_api_key)
):
    """
    Revoke an API key
    """
    from backend.config.database import get_db
    db = get_db()
    organization = auth_context["organization"]
    
    await db.revoke_api_key(key_id, organization["id"])


@api_keys_router.patch("/{key_id}", response_model=APIKeyResponse)
async def update_api_key(
    key_id: str,
    update_data: APIKeyUpdate,
    request: Request,
    auth_context = Depends(validate_api_key)
):
    """
    Update an API key settings
    """
    from backend.config.database import get_db
    db = get_db()
    organization = auth_context["organization"]
    
    # Get existing key
    existing_keys = await db.list_api_keys(organization["id"])
    existing_key = next((k for k in existing_keys if k["id"] == key_id), None)
    
    if not existing_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    # Update key
    update_dict = update_data.model_dump(exclude_unset=True)
    # Note: Supabase update method would be needed here
    # For now, return existing key
    
    return APIKeyResponse(
        id=existing_key["id"],
        key_prefix=existing_key["key_prefix"],
        name=update_data.name if update_data.name else existing_key.get("name"),
        created_at=existing_key["created_at"],
        last_used_at=existing_key.get("last_used_at"),
        expires_at=existing_key.get("expires_at"),
        is_active=update_data.is_active if update_data.is_active is not None else existing_key["is_active"],
        rate_limit_per_minute=update_data.rate_limit_per_minute if update_data.rate_limit_per_minute else existing_key["rate_limit_per_minute"]
    )
