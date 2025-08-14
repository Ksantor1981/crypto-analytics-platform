"""
Pytest configuration and fixtures for integration tests
"""
import pytest
import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_redis_client():
    """Mock Redis client for testing"""
    mock_client = AsyncMock()
    mock_client.ping = AsyncMock(return_value=True)
    mock_client.publish = AsyncMock(return_value=1)
    mock_client.close = AsyncMock()
    mock_client.zcard = AsyncMock(return_value=0)
    mock_client.llen = AsyncMock(return_value=0)
    mock_client.scard = AsyncMock(return_value=0)
    mock_client.zadd = AsyncMock(return_value=1)
    mock_client.get = AsyncMock(return_value=None)
    mock_client.set = AsyncMock(return_value=True)
    mock_client.delete = AsyncMock(return_value=1)
    
    # Mock pubsub
    mock_pubsub = AsyncMock()
    mock_pubsub.subscribe = AsyncMock()
    mock_pubsub.unsubscribe = AsyncMock()
    mock_pubsub.close = AsyncMock()
    mock_pubsub.listen = AsyncMock()
    
    mock_client.pubsub = MagicMock(return_value=mock_pubsub)
    
    return mock_client, mock_pubsub

@pytest.fixture(autouse=True)
def mock_redis_for_all_tests():
    """Automatically mock Redis for all tests"""
    with patch('redis.Redis') as mock_redis_class:
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)
        mock_client.publish = AsyncMock(return_value=1)
        mock_client.close = AsyncMock()
        mock_client.zcard = AsyncMock(return_value=0)
        mock_client.llen = AsyncMock(return_value=0)
        mock_client.scard = AsyncMock(return_value=0)
        mock_client.zadd = AsyncMock(return_value=1)
        
        mock_pubsub = AsyncMock()
        mock_pubsub.subscribe = AsyncMock()
        mock_pubsub.unsubscribe = AsyncMock()
        mock_pubsub.close = AsyncMock()
        mock_client.pubsub = MagicMock(return_value=mock_pubsub)
        
        mock_redis_class.return_value = mock_client
        yield mock_client

@pytest.fixture
def mock_logger():
    """Mock logger for testing"""
    logger = MagicMock()
    logger.info = MagicMock()
    logger.error = MagicMock()
    logger.warning = MagicMock()
    logger.debug = MagicMock()
    return logger

@pytest.fixture
def test_settings():
    """Test settings with safe defaults"""
    from app.core.config import Settings
    
    # Override some settings for testing
    os.environ.update({
        'DATABASE_URL': 'sqlite:///./test_crypto_analytics.db',
        'USE_SQLITE': 'true',
        'REDIS_URL': 'redis://localhost:6379/15',  # Use different DB for tests
        'SECRET_KEY': 'test-secret-key-for-testing-very-long-and-secure',
        'ENVIRONMENT': 'testing',
        'DEBUG': 'true'
    })
    
    return Settings()

# Add pytest markers
pytest_plugins = []

def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "redis: marks tests that require Redis"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )