#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных с тестовыми данными
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.core.config import get_settings
from backend.app.models.base import BaseModel
from backend.app.models.user import User, UserRole, SubscriptionPlan, SubscriptionStatus
from backend.app.models.channel import Channel
from backend.app.models.signal import Signal, SignalStatus, SignalDirection
from backend.app.core.security import get_password_hash
from datetime import datetime, timedelta
import random

def init_database():
    """Инициализация базы данных с тестовыми данными"""
    
    settings = get_settings()
    
    # Создаем движок базы данных
    engine = create_engine(settings.database_url, echo=True)
    
    # Создаем все таблицы
    BaseModel.metadata.create_all(bind=engine)
    
    # Создаем сессию
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("🗄️ Инициализация базы данных...")
        
        # Создаем тестового пользователя
        test_user = User(
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_verified=True,
            role=UserRole.PREMIUM_USER,
            subscription_plan=SubscriptionPlan.PREMIUM,
            subscription_status=SubscriptionStatus.ACTIVE,
            channels_limit=50,
            api_calls_limit=1000
        )
        
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        print(f"✅ Создан тестовый пользователь: {test_user.email}")
        
        # Создаем тестовые каналы
        channels_data = [
            {
                "username": "crypto_signals_pro",
                "name": "Crypto Signals Pro",
                "description": "Профессиональные сигналы криптовалют",
                "category": "premium",
                "expected_accuracy": "85%",
                "subscribers_count": 15000
            },
            {
                "username": "altcoin_trader",
                "name": "Altcoin Trader",
                "description": "Торговля альткоинами",
                "category": "altcoins",
                "expected_accuracy": "75%",
                "subscribers_count": 8500
            },
            {
                "username": "bitcoin_master",
                "name": "Bitcoin Master",
                "description": "Экспертный анализ Bitcoin",
                "category": "bitcoin",
                "expected_accuracy": "80%",
                "subscribers_count": 22000
            },
            {
                "username": "solana_pro",
                "name": "Solana Pro",
                "description": "Специализация на Solana",
                "category": "solana",
                "expected_accuracy": "90%",
                "subscribers_count": 12000
            },
            {
                "username": "cardano_signals",
                "name": "Cardano Signals",
                "description": "Сигналы по Cardano",
                "category": "cardano",
                "expected_accuracy": "70%",
                "subscribers_count": 6500
            }
        ]
        
        channels = []
        for channel_data in channels_data:
            channel = Channel(
                owner_id=test_user.id,
                **channel_data
            )
            db.add(channel)
            channels.append(channel)
        
        db.commit()
        print(f"✅ Создано {len(channels)} каналов")
        
        # Создаем тестовые сигналы
        signals_data = [
            {
                "channel_id": channels[0].id,  # Crypto Signals Pro
                "asset": "BTC",
                "symbol": "BTC",
                "direction": SignalDirection.LONG,
                "entry_price": 45000.0,
                "tp1_price": 47000.0,
                "stop_loss": 43000.0,
                "confidence_score": 0.85,
                "status": SignalStatus.PENDING,
                "original_text": "Bitcoin показывает признаки разворота вверх"
            },
            {
                "channel_id": channels[1].id,  # Altcoin Trader
                "asset": "ETH",
                "symbol": "ETH",
                "direction": SignalDirection.SHORT,
                "entry_price": 2800.0,
                "tp1_price": 2650.0,
                "stop_loss": 2900.0,
                "confidence_score": 0.75,
                "status": SignalStatus.TP1_HIT,
                "original_text": "Ethereum тестирует поддержку"
            },
            {
                "channel_id": channels[2].id,  # Bitcoin Master
                "asset": "ADA",
                "symbol": "ADA",
                "direction": SignalDirection.LONG,
                "entry_price": 0.45,
                "tp1_price": 0.52,
                "stop_loss": 0.42,
                "confidence_score": 0.70,
                "status": SignalStatus.PENDING,
                "original_text": "Cardano готов к пробою сопротивления"
            },
            {
                "channel_id": channels[3].id,  # Solana Pro
                "asset": "SOL",
                "symbol": "SOL",
                "direction": SignalDirection.SHORT,
                "entry_price": 95.0,
                "tp1_price": 88.0,
                "stop_loss": 98.0,
                "confidence_score": 0.90,
                "status": SignalStatus.TP1_HIT,
                "original_text": "Solana корректируется после роста"
            },
            {
                "channel_id": channels[4].id,  # Cardano Signals
                "asset": "DOT",
                "symbol": "DOT",
                "direction": SignalDirection.LONG,
                "entry_price": 6.8,
                "tp1_price": 7.2,
                "stop_loss": 6.5,
                "confidence_score": 0.65,
                "status": SignalStatus.SL_HIT,
                "original_text": "Polkadot формирует паттерн"
            },
            {
                "channel_id": channels[0].id,  # Crypto Signals Pro
                "asset": "BTC",
                "symbol": "BTC",
                "direction": SignalDirection.SHORT,
                "entry_price": 46000.0,
                "tp1_price": 44500.0,
                "stop_loss": 46500.0,
                "confidence_score": 0.80,
                "status": SignalStatus.PENDING,
                "original_text": "Bitcoin корректируется"
            }
        ]
        
        # Добавляем временные метки
        current_time = datetime.utcnow()
        for i, signal_data in enumerate(signals_data):
            # Разные времена для разных сигналов
            hours_ago = [2, 6, 1, 12, 24, 0.5][i % len(signals_data)]
            signal_data["created_at"] = current_time - timedelta(hours=hours_ago)
            signal_data["updated_at"] = current_time - timedelta(hours=hours_ago)
            
            signal = Signal(**signal_data)
            db.add(signal)
        
        db.commit()
        print(f"✅ Создано {len(signals_data)} сигналов")
        
        print("\n🎉 База данных успешно инициализирована!")
        print(f"📊 Пользователь: {test_user.email}")
        print(f"📺 Каналов: {len(channels)}")
        print(f"📈 Сигналов: {len(signals_data)}")
        
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
