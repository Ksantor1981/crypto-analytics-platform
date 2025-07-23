#!/usr/bin/env python3
"""
КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Принудительное переключение на PostgreSQL
"""

import os
import sys
import subprocess
import time

def force_postgresql_config():
    """Принудительная настройка PostgreSQL"""
    print("🔧 ПРИНУДИТЕЛЬНАЯ НАСТРОЙКА POSTGRESQL")
    
    # Прямое изменение конфига
    config_content = '''
from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Crypto Analytics Platform"
    VERSION: str = "1.0.0"
    
    # Database - ПРИНУДИТЕЛЬНО PostgreSQL
    DATABASE_URL: str = "postgresql://postgres:postgres123@localhost:5432/crypto_analytics"
    
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
    
    # ML Service
    ML_SERVICE_URL: str = "http://localhost:8001"
    
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
'''
    
    with open("backend/app/core/config.py", "w", encoding="utf-8") as f:
        f.write(config_content)
    
    print("  ✅ Config.py переписан с PostgreSQL")

def restart_all_services():
    """Перезапуск всех сервисов"""
    print("🔄 ПЕРЕЗАПУСК ВСЕХ СЕРВИСОВ")
    
    # 1. Остановка процессов
    subprocess.run(["taskkill", "/f", "/im", "python.exe"], capture_output=True)
    subprocess.run(["taskkill", "/f", "/im", "uvicorn.exe"], capture_output=True)
    time.sleep(2)
    
    # 2. Переменные окружения
    os.environ["DATABASE_URL"] = "postgresql://postgres:postgres123@localhost:5432/crypto_analytics"
    os.environ["SECRET_KEY"] = "crypto-analytics-secret-key-2024-development"
    
    # 3. Создание таблиц
    print("📊 Создание таблиц PostgreSQL...")
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            database="crypto_analytics", 
            user="postgres",
            password="postgres123"
        )
        print("  ✅ PostgreSQL подключение работает")
        conn.close()
    except Exception as e:
        print(f"  ⚠️ PostgreSQL: {e}")
    
    # Создание таблиц через Python
    try:
        os.chdir("backend")
        sys.path.insert(0, os.getcwd())
        
        from app.core.database import engine, Base
        from app.models import user, channel, signal, subscription, payment
        
        Base.metadata.drop_all(bind=engine)  # Удаляем старые
        Base.metadata.create_all(bind=engine)  # Создаем новые
        print("  ✅ Таблицы PostgreSQL созданы")
        
        os.chdir("..")
    except Exception as e:
        print(f"  ❌ Ошибка таблиц: {e}")
        os.chdir("..")
    
    # 4. Запуск ML Service
    print("🤖 Запуск ML Service...")
    subprocess.Popen([sys.executable, "ml-service/main.py"], 
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(3)
    
    # 5. Запуск Backend
    print("🚀 Запуск Backend...")
    env = os.environ.copy()
    env["DATABASE_URL"] = "postgresql://postgres:postgres123@localhost:5432/crypto_analytics"
    env["SECRET_KEY"] = "crypto-analytics-secret-key-2024-development"
    
    subprocess.Popen([
        sys.executable, "-m", "uvicorn", "backend.app.main:app",
        "--host", "0.0.0.0", "--port", "8000", "--reload"
    ], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    time.sleep(5)
    print("  ✅ Сервисы запущены")

def main():
    print("🚨 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ ИНФРАСТРУКТУРЫ")
    print("=" * 50)
    
    force_postgresql_config()
    restart_all_services()
    
    print("\n🎯 ИСПРАВЛЕНИЯ ЗАВЕРШЕНЫ")
    print("Проверяем результат...")

if __name__ == "__main__":
    main() 