
from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Crypto Analytics Platform"
    VERSION: str = "1.0.0"
    
    # Database - Поддержка PostgreSQL и SQLite
    DATABASE_URL: str = "postgresql://postgres:postgres123@localhost:5432/crypto_analytics"
    USE_SQLITE: bool = True  # Переключаемся на SQLite для стабильной локальной разработки
    
    @property
    def database_url(self) -> str:
        """Возвращает URL базы данных в зависимости от настроек"""
        if self.USE_SQLITE or "sqlite" in self.DATABASE_URL.lower():
            return "sqlite:///./crypto_analytics.db"
        return self.DATABASE_URL
    
    # JWT
    SECRET_KEY: str = "crypto-analytics-secret-key-2024-development"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # External APIs
    TELEGRAM_API_ID: Optional[str] = None
    TELEGRAM_API_HASH: Optional[str] = None
    TELEGRAM_SESSION_NAME: Optional[str] = None
    
    # ML Service
    ML_SERVICE_URL: str = "http://localhost:8001"
    
    # Stripe - ДОБАВЛЯЕМ НЕДОСТАЮЩИЕ ПОЛЯ
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    
    # JWT Refresh tokens
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600
    AUTH_RATE_LIMIT_REQUESTS: int = 5
    AUTH_RATE_LIMIT_WINDOW: int = 900
    
    class Config:
        case_sensitive = True

def get_settings() -> Settings:
    return Settings()
