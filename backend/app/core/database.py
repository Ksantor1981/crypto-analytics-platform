from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base

from .config import get_settings

# Получаем настройки
settings = get_settings()

# Создаем движок SQLAlchemy
engine = create_engine(settings.database_url)

# Создаем фабрику сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency для получения сессии БД
def get_db():
    """
    Dependency для получения сессии БД
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 