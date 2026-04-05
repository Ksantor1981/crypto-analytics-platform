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

# Sentry error tracking
try:
    import sentry_sdk
    sentry_dsn = os.getenv("SENTRY_DSN", "")
    if sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn,
            traces_sample_rate=0.3,
            profiles_sample_rate=0.1,
            environment=os.getenv("ENVIRONMENT", "development"),
            send_default_pii=False,
        )
        logging.getLogger(__name__).info("Sentry initialized")
except ImportError:
    pass

# Добавляем текущую директорию в путь для импортов
sys.path.append(str(Path(__file__).parent))

# Initialize structured logging
try:
    from app.core.logging_config import setup_logging
    setup_logging(json_format=os.getenv("ENVIRONMENT") == "production")
except Exception:
    pass

# Обработка импортов с fallback
try:
    from .core.config import get_settings
    from .core.database import engine, Base
    from .api.endpoints import (
        channels, users, signals, subscriptions,
        payments, ml_integration, telegram_integration,
        trading, ml_predictions, backtesting, dashboard,
        user_sources, feedback, analytics, collect, export_signals, export as export_endpoints,
        stripe_checkout, custom_alerts, review_labels, extractions, extraction_decisions,
        normalized_signals,
        signal_relations,
        execution_models,
        signal_outcomes,
        shadow_divergence,
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
            trading, ml_predictions, backtesting, dashboard,             review_labels, extractions,
            extraction_decisions,
            normalized_signals,
        )
        from core.middleware import SubscriptionLimitMiddleware
        from core.scheduler import TradingScheduler
    except ImportError as fallback_error:
        logging.error(f"Fallback import failed: {fallback_error}")
        engine = None
        Base = None
        TradingScheduler = None
        SubscriptionLimitMiddleware = None

# Structured logging (structlog) — JSON в production
try:
    from app.core.logging_config import setup_logging, get_logger
    _env = os.getenv("ENVIRONMENT", "development")
    _use_json = os.getenv("LOG_JSON", "true" if _env == "production" else "false").lower() == "true"
    setup_logging(json_format=_use_json, level=os.getenv("LOG_LEVEL", "INFO"))
    logger = get_logger(__name__)
except ImportError:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

settings = get_settings()
trading_scheduler = None

# OpenAPI UI: в проде можно отключить через OPENAPI_DOCS_ENABLED=false
_OPENAPI_DOCS = bool(getattr(settings, "OPENAPI_DOCS_ENABLED", True))
_OPENAPI_DOCS_URL = "/docs" if _OPENAPI_DOCS else None
_OPENAPI_REDOC_URL = "/redoc" if _OPENAPI_DOCS else None


def _scheduler_mode() -> str:
    mode = str(getattr(settings, "SCHEDULER_MODE", "asyncio") or "asyncio").strip().lower()
    return mode if mode in ("asyncio", "celery") else "asyncio"


def _seed_demo_data(db_engine):
    """Seed database with demo data if empty (отключается AUTO_SEED_DEMO_CHANNELS=false)."""
    if not getattr(settings, "AUTO_SEED_DEMO_CHANNELS", True):
        logger.info("AUTO_SEED_DEMO_CHANNELS=false — пропуск автосида каналов")
        return
    from sqlalchemy.orm import Session
    try:
        with Session(db_engine) as session:
            from app.models.channel import Channel
            from app.models.signal import Signal
            if session.query(Channel).count() > 0:
                return
            channels_data = [
                ("Wolf_of_Trading_singals", "Wolf of Trading Signals", "premium", "Premium trading signals"),
                ("CryptoCapoTG", "Crypto Capo", "premium", "Technical analysis & signals"),
                ("bitcoin_signals", "Bitcoin Signals", "signals", "Bitcoin trading signals"),
                ("binance_signals", "Binance Signals", "signals", "Binance trading signals"),
                ("cryptosignals", "Crypto Signals", "signals", "Daily crypto signals"),
                ("crypto", "Crypto", "general", "General crypto channel"),
                ("price", "Price", "analysis", "Price analysis & alerts"),
                ("UniversalCryptoSignals", "Universal Crypto Signals", "signals", "Universal crypto trading signals"),
                ("CryptoSignalsWorld", "Crypto Signals World", "signals", "Worldwide crypto signals"),
                ("CryptoClassics", "Crypto Classics", "analysis", "Classic technical analysis"),
                ("binancekillers", "Binance Killers", "signals", "Trading signals for Binance"),
                ("Crypto_Futures_Signals", "Crypto Futures Signals", "signals", "Futures trading signals"),
                ("TradingViewIdeas", "TradingView Ideas", "analysis", "Trading ideas & analysis"),
                ("Crypto_Inner_Circler", "Crypto Inner Circle", "signals", "Trading insights & signals"),
                ("io_altsignals", "Altsignals.io", "signals", "Altcoin signals"),
                ("fatpigsignals", "Fat Pig Signals", "signals", "Trading signals"),
                ("learn2trade", "Learn2Trade", "signals", "Education & signals"),
                ("Signals_BTC_ETH", "Signals BTC & ETH", "signals", "Bitcoin & Ethereum signals"),
                ("TTcoin_crypto", "TTcoin Cryptocurrency", "analysis", "Crypto analysis"),
                ("WhaleCharts", "WhaleCharts", "analysis", "Whale tracking & charts"),
                ("signalsbitcoinandethereum", "Bitcoin & Ethereum Signals", "signals", "BTC & ETH signals"),
                ("crypto_analytics", "Crypto Analytics", "analysis", "Crypto analytics channel"),
                ("BybitSignals", "Bybit Signals", "signals", "Bybit exchange trading signals"),
                ("CoinCodex", "CoinCodex", "analysis", "Crypto market analysis and signals"),
                ("CryptoBullSignals", "Crypto Bull Signals", "signals", "Bullish crypto trading signals"),
                ("defi_trading", "DeFi Trading", "signals", "DeFi trading signals"),
                ("futures_signals", "Futures Signals", "signals", "Crypto futures signals"),
                ("CryptoSignalsPro", "Crypto Signals Pro", "signals", "Pro trading signals"),
                ("AltcoinSignals", "Altcoin Signals", "signals", "Altcoin trading signals"),
                ("SatoshiSignals", "Satoshi Signals", "signals", "Bitcoin-focused signals"),
                ("SolanaSignals", "Solana Signals", "signals", "Solana ecosystem signals"),
                ("DeFiSignals", "DeFi Signals", "signals", "DeFi protocols signals"),
                ("WhaleAlertSignals", "Whale Alert", "analysis", "Whale movements & alerts"),
                ("TradingSignalsBTC", "Trading Signals BTC", "signals", "BTC spot & futures"),
                ("CryptoAlertsChannel", "Crypto Alerts", "signals", "Real-time crypto alerts"),
                ("SignalCryptoPro", "Signal Crypto Pro", "signals", "Professional signals"),
                ("BitgetSignals", "Bitget Signals", "signals", "Bitget exchange signals"),
                ("OKXSignals", "OKX Signals", "signals", "OKX trading signals"),
                ("KucoinSignals", "KuCoin Signals", "signals", "KuCoin trading signals"),
                ("MemecoinSignals", "Memecoin Signals", "signals", "Meme coin signals"),
                ("Layer2Signals", "Layer 2 Signals", "signals", "L2 ecosystem signals"),
                ("AISignalsCrypto", "AI Crypto Signals", "signals", "AI-powered signals"),
                ("CryptoScoutSignals", "Crypto Scout", "signals", "Scouting & signals"),
                ("TradingAlertsPro", "Trading Alerts Pro", "signals", "Pro alert channel"),
                ("CryptoKingsSignals", "Crypto Kings", "signals", "Premium signals"),
                ("SmartMoneyCrypto", "Smart Money Crypto", "analysis", "Smart money flows"),
            ]
            demo_channels = [
                Channel(
                    username=uname, name=name,
                    url=f"https://t.me/{uname}", platform="telegram",
                    description=desc, category=cat,
                    signals_count=0, is_active=True, status="active",
                )
                for uname, name, cat, desc in channels_data
            ]
            for ch in demo_channels:
                session.add(ch)
            session.commit()

            session.commit()
            logger.info(f"Seeded {len(demo_channels)} real Telegram channels")
    except Exception as e:
        logger.warning(f"Seed data error (non-critical): {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения (startup + graceful shutdown)."""
    global trading_scheduler
    import asyncio
    _background_tasks: list = []

    logger.info("Starting Crypto Analytics Platform...")

    try:
        # В production используем Alembic (alembic upgrade head перед запуском).
        # В development — create_all для быстрого старта без PostgreSQL.
        use_alembic = os.getenv("USE_ALEMBIC", "false").lower() == "true"
        if engine and Base:
            try:
                if use_alembic:
                    import subprocess
                    backend_dir = Path(__file__).resolve().parent.parent
                    subprocess.run(["alembic", "upgrade", "head"], cwd=str(backend_dir), check=False)
                    logger.info("Alembic migrations applied")
                else:
                    Base.metadata.create_all(bind=engine)
                    logger.info("Database tables created (create_all)")
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

        mode = _scheduler_mode()
        if mode == "asyncio":
            # Auto-collect signals from Telegram channels on startup
            import asyncio
            async def _auto_collect():
                await asyncio.sleep(3)
                try:
                    from app.core.database import SessionLocal
                    from app.core.config import get_settings
                    from app.services.collection_pipeline import run_full_collection_async
                    from app.services.metrics_calculator import recalculate_all_channels

                    db = SessionLocal()
                    try:
                        st = get_settings()
                        result = await run_full_collection_async(db, st)
                        tg = result.get("telegram") or {}
                        rd = result.get("reddit") or {}
                        total = (tg.get("saved") or 0) + (rd.get("saved") or 0)
                        db.commit()
                        recalculate_all_channels(db)
                        logger.info(
                            "Startup collection: saved=%s tg_posts=%s tg_channels=%s reddit_saved=%s",
                            total,
                            tg.get("posts_fetched"),
                            tg.get("channels"),
                            rd.get("saved"),
                        )
                    finally:
                        db.close()
                except Exception as e:
                    logger.warning("Startup collection failed: %s", e)
            t1 = asyncio.create_task(_auto_collect())
            _background_tasks.append(t1)

            # Start periodic collection schedulers
            try:
                from app.tasks.scheduler import (
                    periodic_collection,
                    periodic_reddit_collection,
                    periodic_weekly_digest,
                    periodic_daily_revalidation,
                    periodic_ml_train,
                    periodic_source_health,
                    periodic_source_discovery,
                )
                t2 = asyncio.create_task(periodic_collection())
                t3 = asyncio.create_task(periodic_reddit_collection())
                t4 = asyncio.create_task(periodic_weekly_digest())
                t5 = asyncio.create_task(periodic_daily_revalidation())
                t6 = asyncio.create_task(periodic_ml_train())
                t7 = asyncio.create_task(periodic_source_health())
                t8 = asyncio.create_task(periodic_source_discovery())
                _background_tasks.extend([t2, t3, t4, t5, t6, t7, t8])
                from app.tasks.scheduler import COLLECTION_INTERVAL, REDDIT_INTERVAL
                logger.info(
                    "Schedulers started (asyncio): tg_collect=%ss reddit=%ss digest=7d reval=24h ml=24h health=24h discovery=24h",
                    COLLECTION_INTERVAL,
                    REDDIT_INTERVAL,
                )
            except Exception as sched_err:
                logger.warning("Scheduler not started", error=str(sched_err))
        else:
            logger.info("In-process schedulers disabled (SCHEDULER_MODE=celery); relying on Celery beat/worker")

        logger.info("Application startup completed")
        yield

    except Exception as e:
        logger.error("Critical error during application startup", error=str(e))
        yield

    finally:
        # Graceful shutdown: cancel background tasks
        logger.info("Shutting down application (graceful)...")
        for task in _background_tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        # Stop trading scheduler
        try:
            if trading_scheduler is not None:
                trading_scheduler.stop()
                logger.info("Trading scheduler stopped")
        except Exception as e:
            logger.error("Error stopping trading scheduler", error=str(e))
        # Close DB engine
        try:
            if engine:
                engine.dispose()
        except Exception:
            pass
        logger.info("Application shutdown completed")

# Создание FastAPI приложения
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Crypto Analytics Platform API - Advanced crypto signals analysis with ML",
    docs_url=_OPENAPI_DOCS_URL,
    redoc_url=_OPENAPI_REDOC_URL,
    lifespan=lifespan,
    debug=getattr(settings, 'DEBUG', False)
)

# CORS: production — только BACKEND_CORS_ORIGINS; development — localhost/Docker + конфиг
if getattr(settings, "ENVIRONMENT", "development") == "production":
    _cfg = list(getattr(settings, "BACKEND_CORS_ORIGINS", None) or [])
    cors_origins = list(
        dict.fromkeys([o.strip() for o in _cfg if o and str(o).strip()])
    )
    if not cors_origins:
        logging.getLogger(__name__).warning(
            "BACKEND_CORS_ORIGINS пуст в production — укажите домены фронта в env"
        )
else:
    cors_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://frontend:3000",
        "http://localhost:3001",
        "http://localhost:8080",
    ]
    if hasattr(settings, "BACKEND_CORS_ORIGINS"):
        cors_origins.extend(settings.BACKEND_CORS_ORIGINS or [])
    cors_origins = list(dict.fromkeys([o for o in cors_origins if o]))

from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

app.add_middleware(SecurityHeadersMiddleware)
_CORS_ALLOW_HEADERS = [
    "Authorization",
    "Content-Type",
    "Accept",
    "Accept-Language",
    "Origin",
    "X-Requested-With",
    "X-Request-ID",
    "X-CSRF-Token",
    "X-ML-Model-Version",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=_CORS_ALLOW_HEADERS,
    expose_headers=["X-Request-ID"],
)

# Доверенные хосты в production (имена из CORS URL + TRUSTED_HOSTS)
if getattr(settings, "ENVIRONMENT", "development") == "production":
    try:
        from app.core.trusted_hosts import build_trusted_hosts

        _th = build_trusted_hosts(
            getattr(settings, "TRUSTED_HOSTS", None),
            list(getattr(settings, "BACKEND_CORS_ORIGINS", []) or []),
        )
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=_th)
        logger.info("TrustedHostMiddleware enabled: %s", _th)
    except Exception as e:
        logger.warning("TrustedHostMiddleware skip: %s", e)

# Добавляем middleware для ограничения подписок (если доступен)
if SubscriptionLimitMiddleware:
    app.add_middleware(SubscriptionLimitMiddleware)

# Добавляем rate limiting middleware
try:
    from app.middleware.rate_limit_middleware import RateLimitMiddleware
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    app.add_middleware(RateLimitMiddleware, redis_url=redis_url)
    logger.info("RateLimitMiddleware enabled")
except Exception as e:
    logger.warning("RateLimitMiddleware not loaded: %s", e)

try:
    from app.middleware.request_id_middleware import RequestIDMiddleware

    app.add_middleware(RequestIDMiddleware)
    logger.info("RequestIDMiddleware enabled")
except Exception as e:
    logger.warning("RequestIDMiddleware not loaded: %s", e)

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
    ("collect", "/api/v1/collect", "collect"),
    ("export_signals", "/api/v1", "export-csv"),
    ("export_endpoints", "/api/v1", "export"),
    ("stripe_checkout", "/api/v1/stripe", "stripe"),
    ("custom_alerts", "/api/v1/alerts", "alerts"),
    ("review_labels", "/api/v1/admin/review-labels", "review-labels"),
    ("extractions", "/api/v1/admin/extractions", "extractions"),
    ("extraction_decisions", "/api/v1/admin/extraction-decisions", "extraction-decisions"),
    ("normalized_signals", "/api/v1/admin/normalized-signals", "normalized-signals"),
    ("signal_relations", "/api/v1/admin/signal-relations", "signal-relations"),
    ("execution_models", "/api/v1/admin/execution-models", "execution-models"),
    ("signal_outcomes", "/api/v1/admin/signal-outcomes", "signal-outcomes"),
    ("shadow_divergence", "/api/v1/admin/shadow", "shadow-divergence"),
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
    ml_ok = False
    try:
        from app.core.service_probes import probe_ml_service

        ml_ok, _ = await probe_ml_service(settings.ML_SERVICE_URL, timeout=2.0)
    except Exception:
        pass
    return {
        "message": "🚀 Crypto Analytics Platform API",
        "version": settings.VERSION,
        "status": "running",
        "features": {
            "database": engine is not None,
            "ml_service": ml_ok,
            "trading_scheduler": trading_scheduler is not None,
            "cors_enabled": True,
        },
        "endpoints": (
            {
                "docs": "/docs",
                "health": "/health",
                "api": "/api/v1",
            }
            if _OPENAPI_DOCS
            else {
                "health": "/health",
                "api": "/api/v1",
            }
        ),
    }

@app.get("/ready")
async def readiness_check():
    """Readiness probe — БД обязательна; Redis/ML опционально (см. READINESS_REQUIRE_*)."""
    from sqlalchemy import text

    from app.core.service_probes import probe_ml_service, probe_redis_sync

    checks: dict = {"database": False, "redis": None, "ml_service": None}

    if not engine:
        return JSONResponse(
            status_code=503,
            content={"ready": False, "reason": "no_engine", "checks": checks},
        )

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception as e:
        checks["database"] = False
        checks["database_error"] = str(e)
        return JSONResponse(
            status_code=503,
            content={"ready": False, "reason": "database", "checks": checks},
        )

    r_ok, r_err = probe_redis_sync(settings.REDIS_URL)
    checks["redis"] = r_ok
    if not r_ok:
        checks["redis_error"] = r_err

    ml_ok, ml_err = await probe_ml_service(settings.ML_SERVICE_URL, timeout=2.5)
    checks["ml_service"] = ml_ok
    if not ml_ok:
        checks["ml_service_error"] = ml_err

    req_redis = bool(getattr(settings, "READINESS_REQUIRE_REDIS", False))
    req_ml = bool(getattr(settings, "READINESS_REQUIRE_ML", False))
    if req_redis and not r_ok:
        return JSONResponse(
            status_code=503,
            content={"ready": False, "reason": "redis_required", "checks": checks},
        )
    if req_ml and not ml_ok:
        return JSONResponse(
            status_code=503,
            content={"ready": False, "reason": "ml_required", "checks": checks},
        )

    return {"ready": True, "checks": checks}


@app.get("/health")
async def health_check():
    """Liveness probe — basic health check."""
    from datetime import datetime

    health_data = {
        "status": "healthy",
        "version": settings.VERSION,
        "timestamp": None,
        "services": {
            "api": "up",
            "database": "unknown",
            "redis": "unknown",
            "ml_service": "unknown",
        },
    }

    if engine:
        try:
            from sqlalchemy import text

            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            health_data["services"]["database"] = "up"
        except Exception as e:
            health_data["services"]["database"] = f"down: {str(e)}"
            logger.error("Database health check failed: %s", e)

    try:
        from app.core.service_probes import probe_redis_sync, probe_ml_service

        r_ok, r_err = probe_redis_sync(settings.REDIS_URL)
        health_data["services"]["redis"] = "up" if r_ok else f"down: {r_err}"

        ml_ok, ml_err = await probe_ml_service(settings.ML_SERVICE_URL, timeout=2.5)
        health_data["services"]["ml_service"] = "up" if ml_ok else f"down: {ml_err}"
        try:
            from app.services.ml_gateway import circuit_status

            health_data["services"]["ml_circuit"] = circuit_status()
        except Exception:
            health_data["services"]["ml_circuit"] = "unknown"
    except Exception as e:
        health_data["services"]["redis"] = f"check_error: {e}"
        health_data["services"]["ml_service"] = f"check_error: {e}"

    health_data["timestamp"] = datetime.utcnow().isoformat()
    return health_data


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint for scraping."""
    try:
        from app.core.metrics import metrics_response
        return metrics_response()
    except ImportError:
        return JSONResponse(status_code=503, content={"detail": "prometheus_client not installed"})


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
    from datetime import datetime

    return {
        "message": "API работает!",
        "data": "test",
        "timestamp": datetime.utcnow().isoformat(),
    }

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
                "channel_name": signal.channel.name if signal.channel else f"Channel {signal.channel_id}"
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

@app.post("/api/v1/predictions/test")
async def test_prediction():
    """Прокси к ML-сервису; без фейковых ответов при недоступности."""
    import httpx

    url = f"{settings.ML_SERVICE_URL.rstrip('/')}/api/v1/predictions/ml-predict"
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(
                url,
                json={
                    "asset": "BTC",
                    "direction": "LONG",
                    "entry_price": 65000,
                    "target_price": 72000,
                    "stop_loss": 63000,
                },
            )
            if resp.status_code == 200:
                return resp.json()
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "ml_service_error",
                    "status_code": resp.status_code,
                    "body": resp.text[:500],
                },
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={"error": "ml_service_unreachable", "message": str(e)},
        )

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
