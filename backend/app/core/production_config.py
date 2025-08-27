"""
Production-specific configuration overrides
"""
import os
from .config import Settings

class ProductionSettings(Settings):
    """Production environment settings with security hardening"""
    
    # Environment
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    
    # Database - Force PostgreSQL in production
    USE_SQLITE: bool = False
    
    @property 
    def database_url(self) -> str:
        """Production database must be PostgreSQL"""
        db_url = os.getenv(
            "DATABASE_URL", 
            "postgresql://postgres:secure_password_here@postgres:5432/crypto_analytics"
        )
        if "sqlite" in db_url.lower():
            raise ValueError("SQLite not allowed in production! Use PostgreSQL.")
        return db_url
    
    # Security - Strong defaults
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", 
        "MUST_BE_SET_IN_PRODUCTION_ENVIRONMENT_VARIABLES"
    )
    
    # CORS - Restrict to specific domains
    BACKEND_CORS_ORIGINS: list = [
        "https://crypto-analytics.yourdomain.com",
        "https://app.yourdomain.com"
        # Add your production domains here
    ]
    
    # JWT - Shorter expiration for security
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    
    # External APIs - Must be set via env vars
    TELEGRAM_API_ID: str = os.getenv("TELEGRAM_API_ID", "")
    TELEGRAM_API_HASH: str = os.getenv("TELEGRAM_API_HASH", "")
    
    # Stripe - Production keys
    STRIPE_PUBLISHABLE_KEY: str = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    
    # Redis - Production URL with auth
    REDIS_URL: str = os.getenv(
        "REDIS_URL", 
        "redis://:secure_redis_password@redis:6379/0"
    )
    
    # Email - Production SMTP
    EMAIL_SMTP_HOST: str = os.getenv("EMAIL_SMTP_HOST", "")
    EMAIL_SMTP_USERNAME: str = os.getenv("EMAIL_SMTP_USERNAME", "")
    EMAIL_SMTP_PASSWORD: str = os.getenv("EMAIL_SMTP_PASSWORD", "")
    
    # Rate limiting - More restrictive
    RATE_LIMIT_REQUESTS: int = 60  # Reduced from 100
    AUTH_RATE_LIMIT_REQUESTS: int = 3  # Reduced from 5
    
    # Logging - Production format
    class Config:
        case_sensitive = True
        
def get_production_settings() -> ProductionSettings:
    """Get production settings with validation"""
    settings = ProductionSettings()
    
    # Validate critical settings
    if settings.SECRET_KEY == "MUST_BE_SET_IN_PRODUCTION_ENVIRONMENT_VARIABLES":
        raise ValueError("SECRET_KEY must be set in production environment!")
    
    if not settings.TELEGRAM_API_ID or not settings.TELEGRAM_API_HASH:
        raise ValueError("Telegram API credentials must be set!")
        
    return settings
