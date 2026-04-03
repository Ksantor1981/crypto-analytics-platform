from pydantic_settings import BaseSettings
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import os

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
    
    # Database - PostgreSQL (primary) or SQLite (fallback)
    DATABASE_URL: str = Field(
        default="postgresql://crypto_analytics_user@localhost:5432/crypto_analytics",
        description="Database URL; пароль только через .env (не храните креды в коде)",
    )
    USE_SQLITE: bool = False
    
    @property
    def database_url(self) -> str:
        """Returns database URL — PostgreSQL by default, SQLite if USE_SQLITE=true"""
        if self.USE_SQLITE:
            url = self.DATABASE_URL or ""
            if "sqlite" in url:
                return self.DATABASE_URL
            return "sqlite:///./crypto_analytics.db"
        return self.DATABASE_URL
    
    # JWT
    SECRET_KEY: str = Field(
        default="",
        description="Secret key for JWT tokens. Generate with: openssl rand -hex 32"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ]
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Monitoring
    SENTRY_DSN: str = ""
    
    # Redis
    REDIS_URL: str = "redis://localhost:6380/0"
    
    # External APIs
    TELEGRAM_API_ID: Optional[str] = None
    TELEGRAM_API_HASH: Optional[str] = None
    TELEGRAM_SESSION_NAME: Optional[str] = None
    # Имена хостов через запятую для TrustedHostMiddleware в production (не URL)
    TRUSTED_HOSTS: Optional[str] = None
    # При False — не вызывать _seed_demo_data при старте (Docker / только реальные каналы из БД)
    AUTO_SEED_DEMO_CHANNELS: bool = True

    # Канонический data plane: dual-write raw_events + message_versions (см. docs/DATA_PLANE_MIGRATION.md)
    SHADOW_PIPELINE_ENABLED: bool = False

    # C1: сбор без Telegram — при False периодический сбор только Reddit/seed
    COLLECT_TELEGRAM: bool = True
    # Scheduler mode:
    # - "asyncio": run periodic background loops inside backend process
    # - "celery": disable in-process loops; rely on celery worker/beat
    SCHEDULER_MODE: str = "asyncio"
    # Один прогон run_collection / CLI: после Telegram подтянуть Reddit (дубли с periodic_reddit отсекаются дедупом)
    COLLECT_REDDIT_IN_RUN_COLLECTION: bool = True
    # Лимит постов t.me/s: base + (priority-1)*step, capped
    TELEGRAM_POSTS_BASE_LIMIT: int = 20
    TELEGRAM_POSTS_PRIORITY_STEP: int = 5
    TELEGRAM_POSTS_MAX_LIMIT: int = 80
    # Подробный лог воронки парсинга (posts → parsed → saved / skip)
    COLLECT_LOG_PARSE_FUNNEL: bool = True
    
    # ML Service (A6: опциональная версия модели для A/B — передаётся в заголовке в ML service)
    ML_SERVICE_URL: str = "http://localhost:8001"
    ML_MODEL_VERSION: Optional[str] = None
    # Устойчивость вызовов ML (backend → ml-service)
    ML_HTTP_RETRIES: int = 2
    ML_CIRCUIT_FAILURE_THRESHOLD: int = 5
    ML_CIRCUIT_OPEN_SECONDS: int = 60
    # Readiness: по умолчанию достаточно БД; для K8s можно потребовать Redis/ML
    READINESS_REQUIRE_REDIS: bool = False
    READINESS_REQUIRE_ML: bool = False
    
    # Stripe
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    # Enables a deterministic "fake Stripe" flow for CI/E2E.
    # When enabled, /stripe/create-checkout will return a mock checkout URL
    # that completes the subscription without calling Stripe APIs.
    STRIPE_MOCK_MODE: bool = False
    
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
        default="",
        description="32-byte encryption key for trading API credentials"
    )
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600
    AUTH_RATE_LIMIT_REQUESTS: int = 5
    AUTH_RATE_LIMIT_WINDOW: int = 900
    
    model_config = ConfigDict(case_sensitive=True)

def get_settings() -> Settings:
    return Settings()


def database_url_for_host(db_url: str) -> str:
    """
    Для запуска на хосте (не в Docker): подменить хост postgres на localhost,
    порт 543 → 5432, добавить имя БД если нет.
    """
    if "@postgres" not in db_url and "@postgres:" not in db_url:
        return db_url
    try:
        from urllib.parse import urlparse, urlunparse
        p = urlparse(db_url)
        if p.port in (None, 543):
            netloc = f"{p.hostname or 'localhost'}:5432" if p.username else "localhost:5432"
        else:
            netloc = f"{p.hostname or 'localhost'}:{p.port}"
        if p.username:
            netloc = f"{p.username}:{p.password or ''}@{netloc}" if p.password else f"{p.username}@{netloc}"
        path = p.path if p.path and p.path != "/" else "/crypto_analytics"
        new_url = urlunparse((
            p.scheme,
            netloc.replace("postgres:", "localhost:").replace("@postgres", "@localhost"),
            path, p.params, p.query, p.fragment,
        ))
        return new_url
    except Exception:
        return db_url


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
