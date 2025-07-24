# FastAPI main application

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import uvicorn
import logging

from .core.config import get_settings
from .core.database import engine, Base
from .api.endpoints import channels, users, signals, subscriptions, payments, ml_integration, telegram_integration, trading
from app.core.middleware import SubscriptionLimitMiddleware
from app.core.scheduler import email_scheduler, trading_scheduler

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

# Создание FastAPI приложения
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Crypto Analytics Platform API",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Добавляем middleware для доверенных хостов (только в продакшене)
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.BACKEND_CORS_ORIGINS
    )

# Добавляем middleware для ограничения подписок
app.add_middleware(SubscriptionLimitMiddleware)

# Создание таблиц при запуске
@app.on_event("startup")
async def startup_event():
    """Создание таблиц базы данных при запуске приложения"""
    try:
        # Создаем все таблицы
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Start email scheduler
        email_scheduler.start()
        logger.info("Email scheduler started")
        
        # Start trading scheduler
        trading_scheduler.start()
        logger.info("Trading scheduler started")
        
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    try:
        # Stop email scheduler
        email_scheduler.stop()
        logger.info("Email scheduler stopped")
        # Stop trading scheduler
        trading_scheduler.stop()
        logger.info("Trading scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping email scheduler: {e}")

# Подключение роутеров
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(channels.router, prefix="/api/v1/channels", tags=["channels"])
app.include_router(signals.router, prefix="/api/v1/signals", tags=["signals"])
app.include_router(subscriptions.router, prefix="/api/v1/subscriptions", tags=["subscriptions"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["payments"])
app.include_router(ml_integration.router, prefix="/api/v1/ml", tags=["ml"])
app.include_router(telegram_integration.router, prefix="/api/v1/telegram", tags=["telegram"])
app.include_router(trading.router, prefix="/api/v1/trading", tags=["trading"])

@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "message": "Crypto Analytics Platform API",
        "version": settings.VERSION,
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Проверка состояния API"""
    return {
        "status": "healthy",
        "version": settings.VERSION
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 