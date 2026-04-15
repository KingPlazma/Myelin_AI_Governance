"""
JWT Service — Myelin API

Implements strict JWT (JSON Web Token) authentication with:
  - Short-lived access tokens  (default: 60 minutes)
  - Longer-lived refresh tokens (default: 7 days)
  - Token type enforcement  (access vs refresh — prevents refresh-as-access abuse)
  - Issued-at + not-before claims (prevents backdated tokens)
  - All tokens signed with HS256 using SECRET_KEY

Token payload structure:
  {
    "sub":   "<user_id>",
    "email": "<user@example.com>",
    "org":   "<organization_id>",
    "role":  "<admin|developer|viewer>",
    "type":  "access" | "refresh",
    "iat":   <issued-at epoch>,
    "nbf":   <not-before epoch>,
    "exp":   <expiry epoch>,
    "jti":   "<unique token id>"   ← for future revocation list
  }
"""

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional

import jwt
from fastapi import HTTPException, status

from backend.config.settings import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ALGORITHM = "HS256"

TOKEN_TYPE_ACCESS  = "access"
TOKEN_TYPE_REFRESH = "refresh"


# ---------------------------------------------------------------------------
# JWT Service
# ---------------------------------------------------------------------------

class JWTService:
    """Creates, validates, and refreshes JWT tokens."""

    def __init__(self):
        if settings.SECRET_KEY == "your-secret-key-change-in-production":
            logger.warning(
                "🔴 SECRET_KEY is still the default placeholder. "
                "JWT tokens are NOT SECURE. Set a real SECRET_KEY in .env"
            )

    # ------------------------------------------------------------------
    # Token creation
    # ------------------------------------------------------------------

    def create_access_token(self, user: Dict[str, Any]) -> str:
        """Create a short-lived access token (default 60 min)."""
        return self._create_token(user, TOKEN_TYPE_ACCESS, settings.JWT_ACCESS_EXPIRE_MINUTES)

    def create_refresh_token(self, user: Dict[str, Any]) -> str:
        """Create a long-lived refresh token (default 7 days)."""
        return self._create_token(user, TOKEN_TYPE_REFRESH, settings.JWT_REFRESH_EXPIRE_MINUTES)

    def _create_token(self, user: Dict[str, Any], token_type: str, expire_minutes: int) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub":   str(user["id"]),
            "email": user.get("email", ""),
            "org":   str(user.get("organization_id", "")),
            "role":  user.get("role", "developer"),
            "type":  token_type,
            "iat":   now,
            "nbf":   now,                                       # not valid before now
            "exp":   now + timedelta(minutes=expire_minutes),
            "jti":   secrets.token_hex(16),                     # unique token id
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)

    # ------------------------------------------------------------------
    # Token validation
    # ------------------------------------------------------------------

    def verify_access_token(self, token: str) -> Dict[str, Any]:
        """
        Validate an access token. Raises HTTPException on any failure.
        Returns the decoded claims dict.
        """
        return self._verify_token(token, expected_type=TOKEN_TYPE_ACCESS)

    def verify_refresh_token(self, token: str) -> Dict[str, Any]:
        """Validate a refresh token. Returns decoded claims."""
        return self._verify_token(token, expected_type=TOKEN_TYPE_REFRESH)

    def _verify_token(self, token: str, expected_type: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[ALGORITHM],
                options={
                    "require": ["exp", "iat", "nbf", "sub", "type", "jti"],
                    "verify_exp": True,
                    "verify_nbf": True,
                    "verify_iat": True,
                },
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.ImmatureSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is not yet valid.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError as exc:
            logger.warning("🔐 Invalid JWT: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Enforce token type (prevent refresh token being used as access token)
        if payload.get("type") != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected '{expected_type}'.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return payload

    # ------------------------------------------------------------------
    # Refresh flow
    # ------------------------------------------------------------------

    def rotate_tokens(self, refresh_token: str, user: Dict[str, Any]) -> Dict[str, str]:
        """
        Validate a refresh token and issue a fresh access + refresh token pair.
        The old refresh token is implicitly invalidated client-side on receipt of the new one.

        For production: add the old jti to a Redis revocation list.
        """
        self.verify_refresh_token(refresh_token)   # raises on invalid/expired
        return {
            "access_token":  self.create_access_token(user),
            "refresh_token": self.create_refresh_token(user),
            "token_type":    "bearer",
            "expires_in":    settings.JWT_ACCESS_EXPIRE_MINUTES * 60,  # seconds
        }

    def decode_unverified(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode token WITHOUT verifying signature (for logging/debugging only)."""
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except Exception:
            return None


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_jwt_service: Optional[JWTService] = None


def get_jwt_service() -> JWTService:
    global _jwt_service
    if _jwt_service is None:
        _jwt_service = JWTService()
    return _jwt_service
