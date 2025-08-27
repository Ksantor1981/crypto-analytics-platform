from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from pydantic import BaseModel, Field

class RedisConfig(BaseModel):
    """Redis configuration"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    socket_timeout: int = 30
    socket_connect_timeout: int = 30
    socket_keepalive: bool = True
    socket_keepalive_options: dict = {}
    health_check_interval: int = 30
    max_connections: int = 10

class TelegramConfig(BaseModel):
    """Telegram configuration"""
    api_id: Optional[str] = None
    api_hash: Optional[str] = None
    session_name: str = "crypto_analytics_session"
    channels: List[str] = []
    flood_sleep_threshold: int = 60
    request_delay: float = 1.0
    max_list_size: int = 100

class ProcessingConfig(BaseModel):
    """Signal processing configuration"""
    collection_interval_seconds: int = 60
    batch_processing_interval_seconds: int = 30
    batch_size: int = 100
    signal_retention_days: int = 30
    max_concurrent_processors: int = 5
    retry_attempts: int = 3
    retry_delay_seconds: int = 5
    timeout_seconds: int = 300

class MarketDataConfig(BaseModel):
    """Market data configuration"""
    update_interval_seconds: int = 300
    api_timeout_seconds: int = 30
    tracked_symbols: List[str] = [
        "bitcoin", "ethereum", "binancecoin", "cardano", "solana",
        "ripple", "polkadot", "dogecoin", "avalanche-2", "chainlink"
    ]
    data_retention_days: int = 90
    max_api_calls_per_minute: int = 50
    cache_duration_seconds: int = 60

class LoggingConfig(BaseModel):
    """Logging configuration"""
    level: str = "INFO"
    file_enabled: bool = True
    file_path: str = "logs/crypto_analytics.log"
    max_file_size_mb: int = 100
    backup_count: int = 5
    include_trace_id: bool = True
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    json_format: bool = False

class Settings(BaseSettings):
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Crypto Analytics Platform"
    VERSION: str = "1.0.0"
    
    # Database - Поддержка PostgreSQL и SQLite
    DATABASE_URL: str = Field(
        default="postgresql://postgres:password@localhost:5433/crypto_analytics",
        description="Database connection URL"
    )
    USE_SQLITE: bool = True  # Используем SQLite для простоты
    
    @property
    def database_url(self) -> str:
        """Возвращает URL базы данных в зависимости от настроек"""
        if self.USE_SQLITE or "sqlite" in self.DATABASE_URL.lower():
            return "sqlite:///./crypto_analytics.db"
        return self.DATABASE_URL
    
    # JWT
    SECRET_KEY: str = Field(
        default="CHANGE_THIS_SECRET_KEY_IN_PRODUCTION_USE_OPENSSL_RAND_HEX_32",
        description="Secret key for JWT tokens. Generate with: openssl rand -hex 32"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Redis
    REDIS_URL: str = "redis://localhost:6380/0"
    
    # External APIs
    TELEGRAM_API_ID: Optional[str] = None
    TELEGRAM_API_HASH: Optional[str] = None
    TELEGRAM_SESSION_NAME: Optional[str] = None
    
    # ML Service
    ML_SERVICE_URL: str = "http://localhost:8001"
    
    # Stripe
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    
    # Email Configuration
    EMAIL_SMTP_HOST: Optional[str] = None
    EMAIL_SMTP_PORT: int = 587
    EMAIL_SMTP_USERNAME: Optional[str] = None
    EMAIL_SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM_ADDRESS: str = "noreply@crypto-analytics.com"
    EMAIL_FROM_NAME: str = "Crypto Analytics Platform"
    EMAIL_USE_TLS: bool = True
    EMAIL_USE_SSL: bool = False
    
    # Alternative: SendGrid (if SMTP not available)
    SENDGRID_API_KEY: Optional[str] = None
    SENDGRID_FROM_EMAIL: str = "noreply@crypto-analytics.com"
    SENDGRID_FROM_NAME: str = "Crypto Analytics Platform"
    
    # JWT Refresh tokens
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # Trading Encryption
    TRADING_ENCRYPTION_KEY: str = Field(
        default="YourSecretKey32BytesLongForDevOnly123",
        description="32-byte encryption key for trading API credentials"
    )
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600
    AUTH_RATE_LIMIT_REQUESTS: int = 5
    AUTH_RATE_LIMIT_WINDOW: int = 900
    
    class Config:
        case_sensitive = True

def get_settings() -> Settings:
    return Settings()

# Создаем экземпляры конфигураций для импорта в тестах
settings = get_settings()
redis_config = RedisConfig()
telegram_config = TelegramConfig(
    api_id=settings.TELEGRAM_API_ID,
    api_hash=settings.TELEGRAM_API_HASH,
    session_name=settings.TELEGRAM_SESSION_NAME or "crypto_analytics_session"
)
processing_config = ProcessingConfig()
market_data_config = MarketDataConfig()
logging_config = LoggingConfig()
