import pytest
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

def test_imports():
    from app.core.config import get_settings
    from app.core.logging import get_logger
    assert get_settings is not None
    assert get_logger is not None
    print("✅ Imports OK")

def test_config():
    from app.core.config import get_settings
    settings = get_settings()
    assert settings.DATABASE_URL is not None
    assert settings.SECRET_KEY is not None
    print("✅ Config OK")

def test_logging():
    from app.core.logging import get_logger
    logger = get_logger("test")
    logger.info("Test message")
    print("✅ Logging OK")

def test_message_queue():
    """Test message queue connectivity"""
    import redis
    r = redis.Redis(host='localhost', port=6379, db=0, socket_connect_timeout=2)
    try:
        assert r.ping()
    except redis.ConnectionError:
        pytest.skip("Redis not available")