"""
Authentication Middleware
Validates API keys for protected endpoints
"""

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import logging

from backend.services.auth_service import get_auth_service

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


async def get_api_key_from_request(request: Request) -> Optional[str]:
    """Extract API key from request headers"""
    
    # Try X-API-Key header first
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return api_key
    
    # Try Authorization header (Bearer token)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.replace("Bearer ", "")
    
    return None


async def validate_api_key(request: Request) -> Dict[str, Any]:
    """
    Validate API key and return authentication context
    Raises HTTPException if invalid
    """
    api_key = await get_api_key_from_request(request)
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Provide via X-API-Key header or Authorization: Bearer <key>",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    auth_service = get_auth_service()
    auth_context = await auth_service.validate_api_key(api_key)
    
    if not auth_context:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Add auth context to request state
    request.state.auth = auth_context
    
    return auth_context


async def get_current_organization(request: Request) -> Dict[str, Any]:
    """Get current organization from request state"""
    if not hasattr(request.state, "auth"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    return request.state.auth["organization"]


async def get_current_user(request: Request) -> Dict[str, Any]:
    """Get current user from request state"""
    if not hasattr(request.state, "auth"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    return request.state.auth["user"]
