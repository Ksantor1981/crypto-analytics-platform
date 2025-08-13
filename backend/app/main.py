# FastAPI main application

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging

from .core.config import get_settings
from .core.database import engine, Base
from .api.endpoints import channels, users, signals, subscriptions, payments, ml_integration, telegram_integration, trading, ml_predictions
from app.core.middleware import SubscriptionLimitMiddleware
from app.core.scheduler import TradingScheduler

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

trading_scheduler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Запуск приложения
    global trading_scheduler
    
    try:
        # Создаем все таблицы
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Start trading scheduler
        trading_scheduler = TradingScheduler()
        trading_scheduler.start()
        logger.info("Trading scheduler started")
        
        yield
        
    except Exception as e:
        logger.error(f"Error during application startup: {e}")
        raise
        
    finally:
        # Остановка приложения
        try:
            if trading_scheduler is not None:
                trading_scheduler.stop()
                logger.info("Trading scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping trading scheduler: {e}")

# Создание FastAPI приложения с lifespan
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Crypto Analytics Platform API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
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

# Подключение роутеров
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(channels.router, prefix="/api/v1/channels", tags=["channels"])
app.include_router(signals.router, prefix="/api/v1/signals", tags=["signals"])
app.include_router(subscriptions.router, prefix="/api/v1/subscriptions", tags=["subscriptions"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["payments"])
app.include_router(ml_integration.router, prefix="/api/v1/ml", tags=["ml"])
app.include_router(telegram_integration.router, prefix="/api/v1/telegram", tags=["telegram"])
app.include_router(trading.router, prefix="/api/v1/trading", tags=["trading"])
app.include_router(ml_predictions.router, prefix="/api/v1/signal-predictions", tags=["Signal Predictions"])

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