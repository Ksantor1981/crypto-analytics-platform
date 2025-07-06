from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"))

class Settings(BaseSettings):
    """
    Application settings
    """
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Crypto Analytics Platform"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://crypto_user:crypto_password@localhost:5432/crypto_analytics")
    
    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey")
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
    
    class Config:
        env_file = "../.env"
        case_sensitive = True
        extra = "ignore"  # Игнорировать дополнительные поля

# Создаем экземпляр настроек
settings = Settings() 