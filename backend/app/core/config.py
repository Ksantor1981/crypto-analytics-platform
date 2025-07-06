from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"))

def validate_required_env_vars():
    """Validate that all required environment variables are set"""
    required_vars = {
        "SECRET_KEY": "JWT secret key for token signing",
        "DATABASE_URL": "Database connection URL"
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing_vars.append(f"{var} ({description})")
    
    if missing_vars:
        raise ValueError(
            f"Missing required environment variables:\n" +
            "\n".join(f"  - {var}" for var in missing_vars) +
            "\n\nPlease set these environment variables before starting the application."
        )

class Settings(BaseSettings):
    """
    Application settings
    """
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Crypto Analytics Platform"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    
    # JWT - No fallback for security
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # External APIs
    TELEGRAM_API_ID: Optional[str] = os.getenv("TELEGRAM_API_ID")
    TELEGRAM_API_HASH: Optional[str] = os.getenv("TELEGRAM_API_HASH")
    TELEGRAM_SESSION_NAME: Optional[str] = os.getenv("TELEGRAM_SESSION_NAME")
    
    # ML Service
    ML_SERVICE_URL: str = os.getenv("ML_SERVICE_URL", "http://ml-service:8001")
    
    # Stripe
    STRIPE_PUBLISHABLE_KEY: Optional[str] = os.getenv("STRIPE_PUBLISHABLE_KEY")
    STRIPE_SECRET_KEY: Optional[str] = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET: Optional[str] = os.getenv("STRIPE_WEBHOOK_SECRET")
    
    # JWT Refresh tokens
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))  # 1 hour
    AUTH_RATE_LIMIT_REQUESTS: int = int(os.getenv("AUTH_RATE_LIMIT_REQUESTS", "5"))
    AUTH_RATE_LIMIT_WINDOW: int = int(os.getenv("AUTH_RATE_LIMIT_WINDOW", "900"))  # 15 minutes
    
    class Config:
        env_file = "../.env"
        case_sensitive = True
        extra = "ignore"  # Игнорировать дополнительные поля

# Validate required environment variables
validate_required_env_vars()

# Создаем экземпляр настроек
settings = Settings()

def get_settings() -> Settings:
    """Получить настройки приложения"""
    return settings 