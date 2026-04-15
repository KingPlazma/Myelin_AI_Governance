"""
Configuration settings for Myelin Backend.
Loads environment variables and provides configuration constants.
"""

from functools import lru_cache
import logging
import os

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "Myelin AI Governance API"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    ENABLE_DOCS: bool = True
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    API_KEY_PREFIX: str = "myelin_sk_"
    API_KEY_LENGTH: int = 32
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # legacy compatibility

    # JWT
    JWT_ACCESS_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_EXPIRE_MINUTES: int = 60 * 24 * 7
    JWT_ALGORITHM: str = "HS256"

    # Bot/anomaly protection
    BOT_BLOCK_THRESHOLD: int = 50
    BOT_DRY_RUN: bool = False
    ANOMALY_MONITOR_ENABLED: bool = True
    INPUT_SANITIZER_ENABLED: bool = True
    
    # Firebase
    FIREBASE_PROJECT_ID: str = ""
    FIREBASE_PRIVATE_KEY: str = ""
    FIREBASE_CLIENT_EMAIL: str = ""
    FIREBASE_CREDENTIALS_JSON: str = ""
    FIREBASE_DATABASE_ID: str = "(default)"
    
    # CORS
    CORS_ORIGINS: str = (
        "http://localhost:3000,"
        "http://127.0.0.1:3000,"
        "http://localhost:4173,"
        "http://127.0.0.1:4173,"
        "http://localhost:5500,"
        "http://127.0.0.1:5500,"
        "http://localhost:5501,"
        "http://127.0.0.1:5501"
    )
    CORS_ALLOW_METHODS: str = "GET,POST,PUT,DELETE,OPTIONS"
    CORS_ALLOW_HEADERS: str = "Content-Type,Authorization,X-API-Key,X-Request-ID,Accept"

    def get_cors_origins(self) -> list:
        """Convert CORS_ORIGINS string to list and warn on wildcard usage."""
        origins = [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        if "*" in origins:
            logging.getLogger(__name__).warning(
                "CORS_ORIGINS contains '*'. Avoid this in production when credentials are enabled."
            )
        return origins

    def get_cors_allow_methods(self) -> list:
        return [method.strip() for method in self.CORS_ALLOW_METHODS.split(",") if method.strip()]

    def get_cors_allow_headers(self) -> list:
        return [header.strip() for header in self.CORS_ALLOW_HEADERS.split(",") if header.strip()]

    # Network hardening
    TRUSTED_HOSTS: str = "localhost,127.0.0.1,0.0.0.0"

    def get_trusted_hosts(self) -> list:
        return [host.strip() for host in self.TRUSTED_HOSTS.split(",") if host.strip()]

    CLOUDFLARE_ENABLED: bool = True
    MAX_REQUEST_BODY_BYTES: int = 2_097_152

    # Rate limiting
    RATE_LIMIT_AUDIT: str = "10/minute"
    RATE_LIMIT_AUTH: str = "20/minute"
    RATE_LIMIT_BATCH: str = "5/minute"
    RATE_LIMIT_DEFAULT: str = "60/minute"
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

    @field_validator(
        "DEBUG",
        "ENABLE_DOCS",
        "BOT_DRY_RUN",
        "ANOMALY_MONITOR_ENABLED",
        "INPUT_SANITIZER_ENABLED",
        "EMAIL_ENABLED",
        "EMAIL_USE_TLS",
        "PUBLIC_DEMO_KEY_ENABLED",
        mode="before",
    )
    @classmethod
    def _coerce_bool(cls, value):
        if isinstance(value, bool) or value is None:
            return value
        normalized = str(value).strip().lower()
        if normalized in {"1", "true", "yes", "on", "debug", "development"}:
            return True
        if normalized in {"0", "false", "no", "off", "release", "production", ""}:
            return False
        return value
    
    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Export settings instance
settings = get_settings()
