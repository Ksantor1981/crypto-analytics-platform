# FastAPI main application

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import logging
import sys
import os
from pathlib import Path

# Добавляем текущую директорию в путь для импортов
sys.path.append(str(Path(__file__).parent))

# Обработка импортов с fallback
try:
    from .core.config import get_settings
    from .core.database import engine, Base
    from .api.endpoints import (
        channels, users, signals, subscriptions, 
        payments, ml_integration, telegram_integration, 
        trading, ml_predictions, backtesting, dashboard
    )
    from .core.middleware import SubscriptionLimitMiddleware
    from .core.scheduler import TradingScheduler
except ImportError as e:
    logging.warning(f"Import error: {e}")
    # Fallback для development
    try:
        from core.config import get_settings
        from core.database import engine, Base
        from api.endpoints import (
            channels, users, signals, subscriptions,
            payments, ml_integration, telegram_integration,
            trading, ml_predictions, backtesting, dashboard
        )
        from core.middleware import SubscriptionLimitMiddleware
        from core.scheduler import TradingScheduler
    except ImportError as fallback_error:
        logging.error(f"Fallback import failed: {fallback_error}")
        # Создаем заглушки для критически важных компонентов
        class MockSettings:
            PROJECT_NAME = "Crypto Analytics Platform"
            VERSION = "1.0.0"
            BACKEND_CORS_ORIGINS = ["http://localhost:3000", "http://frontend:3000"]
            ENVIRONMENT = "development"
            DEBUG = True
        
        def get_settings():
            return MockSettings()
            
        engine = None
        Base = None
        TradingScheduler = None
        SubscriptionLimitMiddleware = None

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/app/logs/backend.log') if os.path.exists('/app/logs') else logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

settings = get_settings()
trading_scheduler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    global trading_scheduler
    
    logger.info("Starting Crypto Analytics Platform...")
    
    try:
        # Создаем все таблицы (если база данных доступна)
        if engine and Base:
            try:
                Base.metadata.create_all(bind=engine)
                logger.info("Database tables created successfully")
            except Exception as db_error:
                logger.error(f"Database initialization failed: {db_error}")
        else:
            logger.warning("Database engine not available - running in limited mode")
        
        # Запускаем планировщик торговли (если доступен)
        if TradingScheduler:
            try:
                trading_scheduler = TradingScheduler()
                trading_scheduler.start()
                logger.info("Trading scheduler started")
            except Exception as scheduler_error:
                logger.error(f"Trading scheduler failed to start: {scheduler_error}")
        else:
            logger.warning("Trading scheduler not available")
        
        logger.info("Application startup completed")
        yield
        
    except Exception as e:
        logger.error(f"Critical error during application startup: {e}")
        # Не падаем, а продолжаем работу в ограниченном режиме
        yield
        
    finally:
        # Остановка приложения
        logger.info("Shutting down application...")
        try:
            if trading_scheduler is not None:
                trading_scheduler.stop()
                logger.info("Trading scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping trading scheduler: {e}")
        logger.info("Application shutdown completed")

# Создание FastAPI приложения
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Crypto Analytics Platform API - Advanced crypto signals analysis with ML",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    debug=getattr(settings, 'DEBUG', False)
)

# Настройка CORS - более либеральная для development
cors_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://frontend:3000",
    "http://localhost:3001",
    "http://localhost:8080"
]

# Добавляем настройки из конфига если они есть
if hasattr(settings, 'BACKEND_CORS_ORIGINS'):
    cors_origins.extend(settings.BACKEND_CORS_ORIGINS)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Добавляем middleware для доверенных хостов (только в продакшене)
if getattr(settings, 'ENVIRONMENT', 'development') == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=getattr(settings, 'BACKEND_CORS_ORIGINS', ["*"])
    )

# Добавляем middleware для ограничения подписок (если доступен)
if SubscriptionLimitMiddleware:
    app.add_middleware(SubscriptionLimitMiddleware)

# Middleware для обработки ошибок
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc) if getattr(settings, 'DEBUG', False) else "Something went wrong"
        }
    )

# Безопасное подключение роутеров
routers_config = [
    ("users", "/api/v1/users", "users"),
    ("channels", "/api/v1/channels", "channels"), 
    ("signals", "/api/v1/signals", "signals"),
    ("subscriptions", "/api/v1/subscriptions", "subscriptions"),
    ("payments", "/api/v1/payments", "payments"),
    ("ml_integration", "/api/v1/ml", "ml"),
    ("telegram_integration", "/api/v1/telegram", "telegram"),
    ("trading", "/api/v1/trading", "trading"),
    ("ml_predictions", "/api/v1/predictions", "predictions"),
    ("backtesting", "/api/v1/backtesting", "backtesting"),
    ("dashboard", "/api/v1/dashboard", "dashboard")
]

# Подключаем роутеры с обработкой ошибок
for router_name, prefix, tag in routers_config:
    try:
        # Пытаемся получить роутер из глобального пространства имен
        if router_name in globals():
            router_module = globals()[router_name]
            if hasattr(router_module, 'router'):
                app.include_router(
                    router_module.router, 
                    prefix=prefix, 
                    tags=[tag]
                )
                logger.info(f"Router {router_name} included successfully")
    except Exception as e:
        logger.warning(f"Failed to include router {router_name}: {e}")

@app.get("/")
async def root():
    """Корневой эндпоинт с информацией о системе"""
    return {
        "message": "🚀 Crypto Analytics Platform API",
        "version": settings.VERSION,
        "status": "running",
        "features": {
            "database": engine is not None,
            "ml_service": True,
            "trading_scheduler": trading_scheduler is not None,
            "cors_enabled": True
        },
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "api": "/api/v1"
        }
    }

@app.get("/health")
async def health_check():
    """Детальная проверка состояния API"""
    health_data = {
        "status": "healthy",
        "version": settings.VERSION,
        "timestamp": None,
        "services": {
            "api": "up",
            "database": "unknown",
            "redis": "unknown",
            "ml_service": "unknown"
        }
    }
    
    # Проверка подключения к базе данных
    if engine:
        try:
            from sqlalchemy import text
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            health_data["services"]["database"] = "up"
        except Exception as e:
            health_data["services"]["database"] = f"down: {str(e)}"
            logger.error(f"Database health check failed: {e}")
    
    # Добавляем timestamp
    from datetime import datetime
    health_data["timestamp"] = datetime.utcnow().isoformat()
    
    return health_data

@app.get("/api/v1/status")
async def api_status():
    """Статус API для мониторинга"""
    return {
        "api_version": "v1",
        "status": "operational", 
        "features": [
            "user_management",
            "channel_analytics", 
            "ml_predictions",
            "trading_signals",
            "payment_processing"
        ]
    }

# Простой эндпоинт для тестирования CORS
@app.get("/api/v1/test")
async def test_endpoint():
    """Тестовый эндпоинт для проверки подключения"""
    return {
        "message": "API connection successful! 🎉",
        "cors": "enabled",
        "timestamp": None
    }

# Простой тестовый эндпоинт
@app.get("/api/v1/test-simple")
async def test_simple():
    """Очень простой тестовый эндпоинт"""
    return {"message": "API работает!", "data": "test", "timestamp": "2025-08-23"}

# Простой эндпоинт для дашборда
@app.get("/api/v1/test-signals")
async def test_signals():
    """Простой эндпоинт для получения сигналов для дашборда"""
    try:
        from sqlalchemy.orm import Session
        from app.core.database import get_db
        from app.models.signal import Signal
        
        # Создаем сессию базы данных
        db = next(get_db())
        
        # Получаем сигналы
        signals = db.query(Signal).order_by(Signal.created_at.desc()).limit(10).all()
        
        # Конвертируем в простой формат
        result = []
        for signal in signals:
            signal_dict = {
                "id": signal.id,
                "asset": signal.asset,
                "symbol": signal.symbol,
                "direction": signal.direction,
                "entry_price": float(signal.entry_price) if signal.entry_price else None,
                "tp1_price": float(signal.tp1_price) if signal.tp1_price else None,
                "stop_loss": float(signal.stop_loss) if signal.stop_loss else None,
                "original_text": signal.original_text,
                "status": signal.status,
                "confidence_score": float(signal.confidence_score) if signal.confidence_score else None,
                "created_at": signal.created_at.isoformat() if signal.created_at else None,
                "channel_id": signal.channel_id,
                "channel_name": f"Channel {signal.channel_id}" if signal.channel_id else "Unknown"
            }
            result.append(signal_dict)
        
        return result
        
    except Exception as e:
        return {"error": str(e), "message": "Failed to get signals"}

@app.get("/api/v1/dashboard/channels")
async def dashboard_channels():
    """Простой эндпоинт для получения каналов для дашборда"""
    try:
        from sqlalchemy.orm import Session
        from app.core.database import get_db
        from app.models.channel import Channel
        
        # Создаем сессию базы данных
        db = next(get_db())
        
        # Получаем каналы
        channels = db.query(Channel).order_by(Channel.created_at.desc()).limit(10).all()
        
        # Конвертируем в простой формат
        result = []
        for channel in channels:
            channel_dict = {
                "id": channel.id,
                "name": channel.name,
                "username": channel.username,
                "description": channel.description,
                "platform": channel.platform,
                "is_active": channel.is_active,
                "is_verified": channel.is_verified,
                "subscribers_count": channel.subscribers_count,
                "category": channel.category,
                "priority": channel.priority,
                "expected_accuracy": channel.expected_accuracy,
                "status": channel.status,
                "created_at": channel.created_at.isoformat() if channel.created_at else None,
                "updated_at": channel.updated_at.isoformat() if channel.updated_at else None
            }
            result.append(channel_dict)
        
        return result
        
    except Exception as e:
        return {"error": str(e), "message": "Failed to get channels"}

# Заглушка для ML предсказаний если основной сервис недоступен
@app.post("/api/v1/predictions/test")
async def test_prediction():
    """Тестовое ML предсказание"""
    return {
        "prediction": "LONG",
        "confidence": 0.75,
        "message": "Test prediction - ML service integration",
        "features_analyzed": 42
    }

if __name__ == "__main__":
    logger.info("Starting server in development mode...")
    uvicorn.run(
        "main:app" if __name__ == "__main__" else "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )