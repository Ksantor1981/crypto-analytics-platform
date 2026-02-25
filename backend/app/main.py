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
        trading, ml_predictions, backtesting, dashboard,
        user_sources, feedback, analytics
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


def _seed_demo_data(db_engine):
    """Seed database with demo data if empty"""
    from sqlalchemy.orm import Session
    try:
        with Session(db_engine) as session:
            from app.models.channel import Channel
            from app.models.signal import Signal
            if session.query(Channel).count() > 0:
                return
            demo_channels = [
                Channel(
                    username="cryptomaster", name="CryptoMaster",
                    url="https://t.me/cryptomaster", platform="telegram",
                    description="Leading crypto signals channel with high accuracy",
                    category="premium", signals_count=342, successful_signals=268,
                    accuracy=78.5, average_roi=15.3, subscribers_count=12500,
                    is_active=True, is_verified=True, status="active",
                ),
                Channel(
                    username="binancekillers", name="BinanceKillers",
                    url="https://t.me/binancekillers", platform="telegram",
                    description="Professional crypto trading signals",
                    category="premium", signals_count=256, successful_signals=210,
                    accuracy=82.1, average_roi=22.7, subscribers_count=8900,
                    is_active=True, is_verified=True, status="active",
                ),
                Channel(
                    username="cryptosignals", name="CryptoSignals",
                    url="https://t.me/cryptosignals", platform="telegram",
                    description="Daily crypto signals and market analysis",
                    category="general", signals_count=189, successful_signals=124,
                    accuracy=65.6, average_roi=8.4, subscribers_count=5200,
                    is_active=True, is_verified=False, status="active",
                ),
                Channel(
                    username="r_cryptocurrency", name="r/CryptoCurrency",
                    url="https://reddit.com/r/CryptoCurrency", platform="reddit",
                    description="Reddit's largest crypto community",
                    category="community", signals_count=95, successful_signals=61,
                    accuracy=64.2, average_roi=5.1, subscribers_count=6700000,
                    is_active=True, is_verified=False, status="active",
                ),
                Channel(
                    username="whale_alert", name="Whale Alert",
                    url="https://t.me/whale_alert_io", platform="telegram",
                    description="Tracking large crypto transactions",
                    category="analytics", signals_count=520, successful_signals=312,
                    accuracy=60.0, average_roi=3.2, subscribers_count=45000,
                    is_active=True, is_verified=True, status="active",
                ),
            ]
            for ch in demo_channels:
                session.add(ch)
            session.commit()

            channels = session.query(Channel).all()
            demo_signals = [
                Signal(channel_id=channels[0].id, asset="BTC/USDT", symbol="BTCUSDT",
                       direction="LONG", entry_price=43250.0, tp1_price=45000.0,
                       stop_loss=42000.0, status="TP1_HIT", confidence_score=0.85,
                       original_text="BTC long entry 43250, TP 45000, SL 42000",
                       profit_loss_absolute=4.05),
                Signal(channel_id=channels[0].id, asset="ETH/USDT", symbol="ETHUSDT",
                       direction="LONG", entry_price=2680.0, tp1_price=2850.0,
                       stop_loss=2600.0, status="PENDING", confidence_score=0.72,
                       original_text="ETH long 2680, target 2850"),
                Signal(channel_id=channels[1].id, asset="BTC/USDT", symbol="BTCUSDT",
                       direction="SHORT", entry_price=44500.0, tp1_price=42000.0,
                       stop_loss=45500.0, status="SL_HIT", confidence_score=0.68,
                       original_text="BTC short from 44500",
                       profit_loss_absolute=-2.25),
                Signal(channel_id=channels[1].id, asset="SOL/USDT", symbol="SOLUSDT",
                       direction="LONG", entry_price=98.5, tp1_price=115.0,
                       stop_loss=92.0, status="TP2_HIT", confidence_score=0.91,
                       original_text="SOL breakout long 98.5",
                       profit_loss_absolute=16.75),
                Signal(channel_id=channels[2].id, asset="BNB/USDT", symbol="BNBUSDT",
                       direction="LONG", entry_price=315.0, tp1_price=340.0,
                       stop_loss=305.0, status="ENTRY_HIT", confidence_score=0.65,
                       original_text="BNB long entry 315"),
                Signal(channel_id=channels[3].id, asset="ADA/USDT", symbol="ADAUSDT",
                       direction="LONG", entry_price=0.45, tp1_price=0.55,
                       stop_loss=0.40, status="TP1_HIT", confidence_score=0.78,
                       original_text="ADA looks bullish, entry 0.45",
                       profit_loss_absolute=22.22),
            ]
            for sig in demo_signals:
                session.add(sig)
            session.commit()
            logger.info(f"Seeded {len(demo_channels)} channels and {len(demo_signals)} signals")
    except Exception as e:
        logger.warning(f"Seed data error (non-critical): {e}")


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
                _seed_demo_data(engine)
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
    ("user_sources", "/api/v1", "user_sources"),
    ("trading", "/api/v1/trading", "trading"),
    ("ml_predictions", "/api/v1/predictions", "predictions"),
    ("backtesting", "/api/v1/backtesting", "backtesting"),
    ("dashboard", "/api/v1/dashboard", "dashboard"),
    ("feedback", "/api/v1/feedback", "feedback"),
    ("analytics", "/api/v1/analytics", "analytics"),
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