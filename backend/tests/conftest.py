import sys
import os
from typing import AsyncGenerator, Generator

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import pytest
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.models import Base
from app.main import app
from app.core.database import get_db

# Используем базу данных в памяти для тестов
TEST_DATABASE_URL = "sqlite:///:memory:"

# Создаем движок для тестов
engine = create_engine(
    TEST_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    echo=True  # Включаем логирование SQL-запросов
)

# Создаем фабрику сессий для тестов
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Фикстура для создания и удаления таблиц
@pytest.fixture(scope="session", autouse=True)
def setup_database():
    # Создаем все таблицы
    Base.metadata.create_all(bind=engine)
    yield
    # Удаляем все таблицы
    Base.metadata.drop_all(bind=engine)

# Фикстура для получения сессии БД
@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

# Переопределяем зависимость get_db
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Фикстура для event_loop
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()

# Фикстура для асинхронного HTTP-клиента
@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

# Добавляем автоматическую маркировку для интеграционных тестов
def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        'integration: mark test as integration test (deselect with "-m not integration")',
    )

def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-integration"):
        skip_integration = pytest.mark.skip(reason="need --run-integration option to run")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)

# Добавляем опцию командной строки для запуска интеграционных тестов
def pytest_addoption(parser):
    parser.addoption(
        "--run-integration", action="store_true", default=False, help="run integration tests"
    )