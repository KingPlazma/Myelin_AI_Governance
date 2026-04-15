"""
Configuration settings for Myelin Backend
Loads environment variables and provides configuration constants
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "Myelin AI Governance API"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    API_KEY_PREFIX: str = "myelin_sk_"
    API_KEY_LENGTH: int = 32
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # legacy — kept for compatibility

    # -------------------------------------------------------------------------
    # JWT — Strict token expiration
    # -------------------------------------------------------------------------
    # Access token: short-lived (default 60 min). Never store in localStorage.
    JWT_ACCESS_EXPIRE_MINUTES: int = 60
    # Refresh token: long-lived (default 7 days). Store in httpOnly cookie.
    JWT_REFRESH_EXPIRE_MINUTES: int = 60 * 24 * 7   # 7 days
    # Algorithm — HS256 is standard; use RS256 when you have a PKI
    JWT_ALGORITHM: str = "HS256"

    # -------------------------------------------------------------------------
    # Bot Detection
    # -------------------------------------------------------------------------
    # Score (0-100) above which a request is classified as a bot and blocked.
    # Lower = more aggressive blocking. 50 is a balanced default.
    BOT_BLOCK_THRESHOLD: int = 50
    # Set True to log bot detections without actually blocking (tuning mode)
    BOT_DRY_RUN: bool = False

    # -------------------------------------------------------------------------
    # Anomaly Monitor
    # -------------------------------------------------------------------------
    ANOMALY_MONITOR_ENABLED: bool = True

    # -------------------------------------------------------------------------
    # Input Sanitizer
    # -------------------------------------------------------------------------
    INPUT_SANITIZER_ENABLED: bool = True
    
    # Firebase
    FIREBASE_PROJECT_ID: str = ""
    FIREBASE_PRIVATE_KEY: str = ""
    FIREBASE_CLIENT_EMAIL: str = ""
    FIREBASE_CREDENTIALS_JSON: str = ""
    
    # CORS — NEVER include "*" when allow_credentials=True (breaks the CORS spec).
    # In production set this to your actual frontend domain(s) via the environment
    # variable:  CORS_ORIGINS="https://app.myelin.com,https://dashboard.myelin.com"
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Explicit list of allowed HTTP methods for CORS (no wildcard in prod)
    CORS_ALLOW_METHODS: str = "GET,POST,PUT,DELETE,OPTIONS"

    # Allowed CORS headers — restrict to what the API actually uses
    CORS_ALLOW_HEADERS: str = (
        "Content-Type,Authorization,X-API-Key,X-Request-ID,Accept"
    )

    def get_cors_origins(self) -> list:
        """Convert CORS_ORIGINS string to list. Warns when wildcard is used."""
        origins = [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
        if "*" in origins:
            import logging
            logging.getLogger(__name__).warning(
                "⚠️  CORS_ORIGINS contains '*'. This is insecure in production "
                "and INCOMPATIBLE with allow_credentials=True. "
                "Set explicit origins in your .env file."
            )
        return origins

    def get_cors_allow_methods(self) -> list:
        return [m.strip() for m in self.CORS_ALLOW_METHODS.split(",") if m.strip()]

    def get_cors_allow_headers(self) -> list:
        return [h.strip() for h in self.CORS_ALLOW_HEADERS.split(",") if h.strip()]
    
    # -------------------------------------------------------------------------
    # Security — Trusted Hosts
    # -------------------------------------------------------------------------
    # Comma-separated list of hostnames the API accepts as valid Host headers.
    # HTTP Host Header attacks are rejected if the header doesn't match.
    # Include "localhost" and "127.0.0.1" for local development.
    # Production example: TRUSTED_HOSTS="api.myelin.com,myelin.com"
    TRUSTED_HOSTS: str = "localhost,127.0.0.1,0.0.0.0"

    def get_trusted_hosts(self) -> list:
        return [h.strip() for h in self.TRUSTED_HOSTS.split(",") if h.strip()]

    # -------------------------------------------------------------------------
    # Security — Cloudflare
    # -------------------------------------------------------------------------
    # Set to True when the API is behind Cloudflare (or any CDN that injects
    # CF-Connecting-IP).  This lets the rate-limiter and IP logging use the
    # real visitor IP rather than the Cloudflare edge node's IP.
    CLOUDFLARE_ENABLED: bool = True

    # -------------------------------------------------------------------------
    # Security — Payload Size
    # -------------------------------------------------------------------------
    # Maximum allowed request body in bytes.  2 MB is a generous upper bound
    # for text-based governance audits; ML arrays should never be this large.
    MAX_REQUEST_BODY_BYTES: int = 2_097_152  # 2 MB

    # -------------------------------------------------------------------------
    # Rate Limiting — per-tier (slowapi string format)
    # -------------------------------------------------------------------------
    # ML audit endpoints — expensive, strict limit
    RATE_LIMIT_AUDIT: str = "10/minute"
    # Auth registration/login — brute-force protection
    RATE_LIMIT_AUTH: str = "20/minute"
    # Batch endpoints — each item = multiple ML calls
    RATE_LIMIT_BATCH: str = "5/minute"
    # General API (rule management, stats, health)
    RATE_LIMIT_DEFAULT: str = "60/minute"
    # (legacy field kept for compatibility)
    DEFAULT_RATE_LIMIT_PER_MINUTE: int = 60

    # Rule Engine
    RULE_CACHE_TTL_SECONDS: int = 300  # 5 minutes
    MAX_CUSTOM_RULES_PER_ORG: int = 100
    
    # Logging
    LOG_LEVEL: str = "INFO"

    # Email Notifications
    EMAIL_ENABLED: bool = False
    EMAIL_SMTP_HOST: str = ""
    EMAIL_SMTP_PORT: int = 587
    EMAIL_SMTP_USERNAME: str = ""
    EMAIL_SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = ""
    EMAIL_USE_TLS: bool = True
    EMAIL_VERIFICATION_BASE_URL: str = "http://localhost:8000/api/v1/auth/verify-email"
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24

    # Public frontend demo controls
    PUBLIC_DEMO_KEY_ENABLED: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Export settings instance
settings = get_settings()
