"""
Authentication Service
Handles user authentication, API key generation, and validation
"""

import secrets
import hashlib
import bcrypt
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
import logging
import asyncio

from backend.config.database import get_db
from backend.config.settings import settings
from backend.models.user import UserCreate, UserLogin
from backend.models.api_key import APIKeyCreate
from backend.services.notification_service import get_notification_service

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication and authorization service"""
    
    def __init__(self):
        self.db = get_db()
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate a new API key"""
        random_part = secrets.token_urlsafe(settings.API_KEY_LENGTH)
        return f"{settings.API_KEY_PREFIX}{random_part}"
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash an API key for storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @staticmethod
    def get_api_key_prefix(api_key: str) -> str:
        """Get the display prefix of an API key"""
        return api_key[:20] if len(api_key) >= 20 else api_key

    @staticmethod
    def hash_verification_token(token: str) -> str:
        """Hash email verification token for secure storage."""
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def generate_verification_token() -> str:
        """Generate email verification token."""
        return secrets.token_urlsafe(32)
    
    async def register_user(self, user_data: UserCreate) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Register a new user and organization
        Returns: (user, organization)
        """
        # Check if user already exists
        existing_user = await self.db.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Check if organization exists
        existing_org = await self.db.get_organization_by_name(user_data.organization_name)
        if existing_org:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization name already taken"
            )
        
        # Create organization
        organization = await self.db.create_organization(
            name=user_data.organization_name,
            tier="free"
        )
        
        # Hash password
        password_hash = self.hash_password(user_data.password)
        
        # Create user
        user = await self.db.create_user(
            email=user_data.email,
            password_hash=password_hash,
            organization_id=organization["id"],
            full_name=user_data.full_name,
            role=user_data.role
        )

        # Generate and send verification token
        await self._issue_and_send_verification_email(user)

        # Ensure response reflects unverified state
        user["email_verified"] = False
        
        logger.info(f"✅ New user registered: {user_data.email} (org: {user_data.organization_name})")
        
        return user, organization
    
    async def login_user(self, login_data: UserLogin) -> Dict[str, Any]:
        """
        Authenticate a user
        Returns: user data
        """
        # Get user by email
        user = await self.db.get_user_by_email(login_data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not self.verify_password(login_data.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Require verified email before allowing login
        if not user.get("email_verified", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email not verified. Please verify your email before logging in."
            )
        
        # Check if user is active
        if not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        logger.info(f"✅ User logged in: {login_data.email}")
        
        return user
    
    async def create_api_key(self, user_id: str, organization_id: str, 
                            key_data: APIKeyCreate) -> Tuple[str, Dict[str, Any]]:
        """
        Create a new API key for a user
        Returns: (full_api_key, api_key_record)
        """
        # Generate API key
        api_key = self.generate_api_key()
        key_hash = self.hash_api_key(api_key)
        key_prefix = self.get_api_key_prefix(api_key)
        
        # Calculate expiration
        expires_at = None
        if key_data.expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=key_data.expires_in_days)
        
        # Create API key record
        api_key_record = await self.db.create_api_key(
            organization_id=organization_id,
            user_id=user_id,
            key_hash=key_hash,
            key_prefix=key_prefix,
            name=key_data.name,
            rate_limit_per_minute=key_data.rate_limit_per_minute
        )
        
        logger.info(f"✅ API key created for user {user_id}: {key_prefix}...")
        
        return api_key, api_key_record
    
    async def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """
        Validate an API key and return associated data
        Returns: {api_key_record, user, organization} or None
        """
        if not api_key or not api_key.startswith(settings.API_KEY_PREFIX):
            return None
        
        # Hash the provided key
        key_hash = self.hash_api_key(api_key)
        
        # Get API key record
        api_key_record = await self.db.get_api_key_by_hash(key_hash)
        if not api_key_record:
            return None
        
        # Check if key is active
        if not api_key_record.get("is_active", False):
            return None
        
        # Check expiration
        if api_key_record.get("expires_at"):
            expires_at = api_key_record["expires_at"]
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > expires_at:
                return None
        
        # Get user and organization
        user = await self.db.get_user(api_key_record["user_id"])
        organization = await self.db.get_organization(api_key_record["organization_id"])

        # Require verified user account for API key usage
        if not user or not user.get("email_verified", False):
            return None
        
        # Update last used timestamp
        await self.db.update_api_key_last_used(api_key_record["id"])
        
        return {
            "api_key": api_key_record,
            "user": user,
            "organization": organization
        }

    async def resend_verification_email(self, email: str) -> Dict[str, Any]:
        """Regenerate verification token and resend verification email for unverified users."""
        user = await self.db.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if user.get("email_verified", False):
            return {
                "message": "Email is already verified",
                "email": email,
                "resent": False
            }

        await self._issue_and_send_verification_email(user)
        return {
            "message": "Verification email sent",
            "email": email,
            "resent": True
        }

    async def verify_user_email(self, token: str) -> Dict[str, Any]:
        """Verify user email using verification token and return user record."""
        if not token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification token is required"
            )

        token_hash = self.hash_verification_token(token)
        user = await self.db.get_user_by_email_verification_token_hash(token_hash)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token"
            )

        expires_at = user.get("email_verification_expires_at")
        if expires_at:
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > expires_at:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Verification token has expired"
                )

        await self.db.mark_user_email_verified(user["id"])
        updated_user = await self.db.get_user(user["id"])
        logger.info(f"✅ User email verified: {updated_user['email']}")
        return updated_user

    async def _issue_and_send_verification_email(self, user: Dict[str, Any]):
        """Create verification token for a user and send email asynchronously."""
        verification_token = self.generate_verification_token()
        verification_token_hash = self.hash_verification_token(verification_token)
        expires_at = datetime.utcnow() + timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS)

        await self.db.set_user_email_verification_token(
            user_id=user["id"],
            token_hash=verification_token_hash,
            expires_at=expires_at
        )

        verification_url = f"{settings.EMAIL_VERIFICATION_BASE_URL}?token={verification_token}"
        notification_service = get_notification_service()
        asyncio.create_task(asyncio.to_thread(
            notification_service.send_verification_email,
            user["email"],
            user.get("full_name") or "",
            verification_url
        ))


# Global auth service instance
auth_service = AuthService()


def get_auth_service() -> AuthService:
    """Get auth service instance"""
    return auth_service
