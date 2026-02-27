"""
CLI для валидации сигналов по историческим ценам.
Запуск: docker exec crypto-analytics-backend python scripts/validate_history_cli.py
"""
import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
from app.services.historical_validator import validate_all_signals


async def main():
    settings = get_settings()
    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    db = Session()
    try:
        result = await validate_all_signals(db)
        print(f"Validated: {result['validated']}/{result['total_signals']}")
        print(f"TP hit: {result['tp_hit']}, SL hit: {result['sl_hit']}")
        print(f"Accuracy: {result['accuracy']}%")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
