import os
import sys
import argparse
from pathlib import Path

# Добавляем папку backend в путь Python, чтобы импорты работали корректно
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

from app.core.database import engine, Base, SessionLocal
from app import models  # Импортируем __init__.py, который подтягивает все модели
from app.core.security import get_password_hash

def seed_data():
    """Fills the database with dummy data for testing."""
    print("🌱 Заполнение базы данных тестовыми данными...")
    db = SessionLocal()
    try:
        # 1. Check if data exists
        if db.query(models.Signal).count() > 0:
            print("✅ База данных уже содержит данные. Пропускаем.")
            return

        # 2. Create a dummy user and channel
        test_user = db.query(models.User).filter(models.User.email == "test@example.com").first()
        if not test_user:
            test_user = models.User(
                email="test@example.com",
                username="testuser",
                hashed_password=get_password_hash("password"),
                role=models.UserRole.PRO_USER,
                is_active=True,
                is_verified=True
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)

        test_channel = db.query(models.Channel).filter(models.Channel.name == "Test ML Channel").first()
        if not test_channel:
            test_channel = models.Channel(
                name="Test ML Channel",
                telegram_id="-100123456789",
                owner_id=test_user.id
            )
            db.add(test_channel)
            db.commit()
            db.refresh(test_channel)

        # 3. Create dummy signals and results
        signals_to_create = []
        for i in range(25):
            pnl = round(random.uniform(-150.5, 200.5), 2)
            new_signal = models.Signal(
                channel_id=test_channel.id,
                asset=f"ASSET{i}/USDT",
                symbol=f"ASSET{i}USDT",
                direction="LONG" if random.random() > 0.5 else "SHORT",
                entry_price=round(random.uniform(1000, 50000), 2),
                status="TP1_HIT" if pnl > 0 else "SL_HIT"
            )
            
            new_signal.result = models.SignalResult(
                pnl=pnl,
                pnl_percentage=round(random.uniform(-10.0, 15.0), 2),
                is_success=pnl > 0,
                duration_minutes=random.randint(5, 240),
                max_drawdown=round(random.uniform(0.1, 5.0), 2),
                risk_reward_ratio=round(random.uniform(0.5, 3.0), 2)
            )
            signals_to_create.append(new_signal)
        
        db.add_all(signals_to_create)
        db.commit()
        print(f"✅ Успешно создано {len(signals_to_create)} сигналов с результатами.")

    finally:
        db.close()

def main():
    print("📊 Создание таблиц в базе данных...")
    try:
        # Убеждаемся, что все модели загружены, импортировав их
        # Этот импорт (models) уже сделал все необходимое
        Base.metadata.create_all(bind=engine)
        print("✅ Таблицы успешно созданы!")
    except Exception as e:
        print(f"❌ Произошла ошибка при создании таблиц: {e}")
        print("💡 Убедитесь, что ваш сервер PostgreSQL запущен и доступен.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage database tables and data.")
    parser.add_argument(
        '--seed',
        action='store_true',
        help='Fill the database with test data after creating tables.'
    )
    args = parser.parse_args()

    main()

    if args.seed:
        seed_data()
