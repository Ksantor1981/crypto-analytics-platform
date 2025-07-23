#!/usr/bin/env python3
"""
Скрипт для настройки SQLite базы данных
Используется как альтернатива PostgreSQL для локальной разработки
"""

import os
import sys
from pathlib import Path
from sqlalchemy import text

# Добавляем backend в путь
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.config import get_settings
from app.core.database import engine, Base
# Явно импортируем все модели
from app.models.user import User, UserRole
from app.models.channel import Channel
from app.models.signal import Signal
from app.models.subscription import Subscription
from app.models.payment import Payment
from app.models.api_key import APIKey
from app.models.performance_metric import PerformanceMetric

def setup_sqlite_database():
    """Создает SQLite базу данных и все таблицы"""
    
    # Устанавливаем флаг для использования SQLite
    os.environ["USE_SQLITE"] = "true"
    
    settings = get_settings()
    print(f"🔧 Настройка SQLite базы данных...")
    print(f"📁 Путь к БД: {settings.database_url}")
    
    try:
        # Явный импорт моделей гарантирует создание всех таблиц
        Base.metadata.create_all(bind=engine)
        print("✅ База данных успешно создана!")
        
        # Проверяем подключение
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            row = result.fetchone()
            if row and row[0] == 1:
                print("✅ Подключение к базе данных работает!")
            else:
                print("❌ Проблема с подключением к базе данных")
                return False
            
    except Exception as e:
        print(f"❌ Ошибка при создании базы данных: {e}")
        return False
    
    return True

def create_sample_data():
    """Создает тестовые данные"""
    from sqlalchemy.orm import Session
    print("📝 Создание тестовых данных...")
    
    try:
        db = Session(engine)
        
        # Создаем тестового пользователя
        test_user = User(
            email="test@example.com",
            hashed_password=__import__('app.core.security', fromlist=['get_password_hash']).get_password_hash("test123"),
            is_active=True,
            role=UserRole.FREE_USER
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        print("✅ Тестовый пользователь создан: test@example.com / test123")
        
        # Создаем тестовый канал
        test_channel = Channel(
            name="Test Crypto Channel",
            url="https://t.me/testcrypto",
            platform="telegram",
            category="crypto",
            is_active=True
        )
        db.add(test_channel)
        db.commit()
        print("✅ Тестовый канал создан")
        
        # Создаем тестовый сигнал
        from app.models.signal import SignalDirection, SignalStatus
        
        test_signal = Signal(
            channel_id=test_channel.id,
            asset="BTC/USDT",
            symbol="BTCUSDT",
            direction=SignalDirection.LONG,
            entry_price=50000.0,
            tp1_price=55000.0,
            stop_loss=48000.0,
            status=SignalStatus.PENDING
        )
        db.add(test_signal)
        db.commit()
        print("✅ Тестовый сигнал создан")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Ошибка при создании тестовых данных: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Настройка SQLite базы данных для Crypto Analytics Platform")
    print("=" * 60)
    
    if setup_sqlite_database():
        if create_sample_data():
            print("\n🎉 Настройка завершена успешно!")
            print("📋 Тестовые данные:")
            print("   - Email: test@example.com")
            print("   - Password: test123")
            print("\n🔗 Для запуска backend используйте:")
            print("   cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
        else:
            print("⚠️ База данных создана, но тестовые данные не добавлены")
    else:
        print("❌ Настройка не завершена")
        sys.exit(1) 