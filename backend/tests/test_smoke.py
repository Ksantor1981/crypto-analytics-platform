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
    """Test message queue system"""
    try:
        from app.services.message_queue import QueueMessage, MessagePriority, RedisMessageQueue
        
        # Test message creation
        message = QueueMessage(
            id="test-123",
            type="test_message",
            payload={"test": "data"},
            priority=MessagePriority.NORMAL
        )
        assert message.id == "test-123"
        assert message.type == "test_message"
        assert message.priority == MessagePriority.NORMAL
        
        # Test message serialization
        message_dict = message.to_dict()
        assert message_dict["id"] == "test-123"
        assert message_dict["priority"] == "normal"
        
        # Test message deserialization
        restored_message = QueueMessage.from_dict(message_dict)
        assert restored_message.id == "test-123"
        assert restored_message.priority == MessagePriority.NORMAL
        
        # Test queue creation (without connecting to Redis)
        queue = RedisMessageQueue()
        assert queue is not None
        assert queue.redis_url == "redis://localhost:6379/0"
        
        print("✅ Message Queue OK")
    except Exception as e:
        pytest.fail(f"Message queue test failed: {e}")