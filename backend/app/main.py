# FastAPI main application

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import uvicorn
import logging

from .core.config import get_settings
from .core.database import engine, Base
from .api.endpoints import channels, users, signals, subscriptions, payments, ml_integration

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
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Добавляем middleware для доверенных хостов
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Создание таблиц при запуске
@app.on_event("startup")
async def startup_event():
    """Создание таблиц базы данных при запуске приложения"""
    try:
        # Создаем все таблицы
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")

# Подключение роутеров
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(channels.router, prefix="/api/v1/channels", tags=["channels"])
app.include_router(signals.router, prefix="/api/v1/signals", tags=["signals"])
app.include_router(subscriptions.router, prefix="/api/v1/subscriptions", tags=["subscriptions"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["payments"])
app.include_router(ml_integration.router, prefix="/api/v1/ml", tags=["ml-integration"])

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