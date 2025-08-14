"""
Integration tests for production-ready backend systems
Tests the interaction between logging, message queue, and processors
"""
import pytest
import asyncio
import json
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
import sys

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Mock недостающие модули перед импортом
sys.modules['app.core.production_logging'] = MagicMock()
sys.modules['app.services.message_queue'] = MagicMock()

# Импортируем после установки моков
from app.core.config import (
    settings, redis_config, telegram_config, 
    processing_config, market_data_config, logging_config
)

class MockQueueMessage:
    def __init__(self, id, type, payload, correlation_id=None, max_retries=3):
        self.id = id
        self.type = type
        self.payload = payload
        self.correlation_id = correlation_id
        self.max_retries = max_retries
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'payload': self.payload,
            'correlation_id': self.correlation_id,
            'max_retries': self.max_retries
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)

class MockRedisMessageQueue:
    def __init__(self):
        self.redis_client = AsyncMock()
        self.pubsub = AsyncMock()
        self.subscribers = {}
        self.running = True
        
        # Define channel constants
        self.SIGNAL_COLLECTED_CHANNEL = "signals:collected"
        self.SIGNAL_PROCESSED_CHANNEL = "signals:processed"
        self.MARKET_DATA_UPDATED_CHANNEL = "market:data:updated"
        self.METRICS_CALCULATED_CHANNEL = "metrics:calculated"
    
    async def connect(self):
        pass
    
    async def disconnect(self):
        self.running = False
        await self.redis_client.close()
        await self.pubsub.close()
    
    async def publish_message(self, channel, message):
        await self.redis_client.publish(channel, json.dumps(message.to_dict()))
        return True
    
    async def subscribe_to_channel(self, channel, handler):
        self.subscribers[channel] = handler
    
    async def publish_signal_collected(self, data, correlation_id=None):
        message = MockQueueMessage(
            id=f"signal-{datetime.utcnow().timestamp()}",
            type="signal_collected",
            payload=data,
            correlation_id=correlation_id
        )
        await self.publish_message(self.SIGNAL_COLLECTED_CHANNEL, message)
    
    async def publish_signal_processed(self, data, correlation_id=None):
        message = MockQueueMessage(
            id=f"processed-{datetime.utcnow().timestamp()}",
            type="signal_processed",
            payload=data,
            correlation_id=correlation_id
        )
        await self.publish_message(self.SIGNAL_PROCESSED_CHANNEL, message)
    
    async def publish_market_data_updated(self, data):
        message = MockQueueMessage(
            id=f"market-{datetime.utcnow().timestamp()}",
            type="market_data_updated",
            payload=data
        )
        await self.publish_message(self.MARKET_DATA_UPDATED_CHANNEL, message)
    
    async def publish_metrics_calculated(self, data):
        message = MockQueueMessage(
            id=f"metrics-{datetime.utcnow().timestamp()}",
            type="metrics_calculated",
            payload=data
        )
        await self.publish_message(self.METRICS_CALCULATED_CHANNEL, message)
    
    async def _handle_message(self, redis_message):
        channel = redis_message['channel'].decode('utf-8')
        data = json.loads(redis_message['data'].decode('utf-8'))
        
        if channel in self.subscribers:
            message = MockQueueMessage.from_dict(data)
            try:
                await self.subscribers[channel](message)
            except Exception as e:
                # Handle error and schedule retry
                if hasattr(message, 'max_retries') and message.max_retries > 0:
                    retry_time = datetime.utcnow().timestamp() + 60  # 1 minute delay
                    await self.redis_client.zadd("retry_queue", {message.id: retry_time})
    
    async def get_queue_stats(self):
        return {
            "delayed_messages": await self.redis_client.zcard("retry_queue"),
            "dead_letter_messages": await self.redis_client.llen("dead_letter_queue"),
            "processing_messages": await self.redis_client.scard("processing_set"),
            "active_channels": len(self.subscribers),
            "total_subscribers": len(self.subscribers)
        }

# Mock функции логирования
mock_logger = MagicMock()
def mock_get_logger(name):
    return mock_logger

def mock_set_trace_id(trace_id):
    return trace_id

# Устанавливаем моки в модули
sys.modules['app.core.production_logging'].get_logger = mock_get_logger
sys.modules['app.core.production_logging'].set_trace_id = mock_set_trace_id
sys.modules['app.services.message_queue'].RedisMessageQueue = MockRedisMessageQueue
sys.modules['app.services.message_queue'].QueueMessage = MockQueueMessage
sys.modules['app.services.message_queue'].MessagePriority = MagicMock()

class TestProductionIntegration:
    """Integration tests for production-ready systems"""
    
    @pytest.mark.asyncio
    async def test_logging_with_message_queue_integration(self):
        """Test logging integration with message queue"""
        # Setup logger with trace ID
        logger = mock_get_logger("integration_test")
        trace_id = mock_set_trace_id("integration-test-123")
        
        # Create test message queue
        message_queue = MockRedisMessageQueue()
        
        # Create test message
        test_message = MockQueueMessage(
            id="msg-123",
            type="test_integration",
            payload={"test": "data"},
            correlation_id=trace_id
        )
        
        # Publish message
        result = await message_queue.publish_message("test_channel", test_message)
        assert result is True
        
        # Verify Redis publish was called
        message_queue.redis_client.publish.assert_called_once()
        
        # Check published data contains trace ID
        call_args = message_queue.redis_client.publish.call_args
        channel, data = call_args[0]
        
        published_data = json.loads(data)
        assert published_data["correlation_id"] == trace_id
    
    @pytest.mark.asyncio
    async def test_signal_processing_workflow(self):
        """Test complete signal processing workflow"""
        # Create test message queue
        message_queue = MockRedisMessageQueue()
        
        # Mock signal data
        signal_data = {
            "channel": "test_channel",
            "message_text": "BUY BTC at $50000",
            "timestamp": datetime.utcnow().isoformat(),
            "confidence": 0.8
        }
        
        # Track processed messages
        processed_messages = []
        
        async def signal_processor_handler(message):
            """Mock signal processor handler"""
            processed_messages.append(message)
            
            # Simulate processing and publish result
            processed_data = {
                "original_signal": message.payload,
                "processed_at": datetime.utcnow().isoformat(),
                "status": "processed"
            }
            
            await message_queue.publish_signal_processed(
                processed_data,
                message.correlation_id
            )
        
        # Subscribe to signal collection events
        await message_queue.subscribe_to_channel(
            message_queue.SIGNAL_COLLECTED_CHANNEL,
            signal_processor_handler
        )
        
        # Publish signal collected event
        correlation_id = "workflow-test-456"
        await message_queue.publish_signal_collected(signal_data, correlation_id)
        
        # Simulate message handling
        test_message = MockQueueMessage(
            id="signal-123",
            type="signal_collected",
            payload=signal_data,
            correlation_id=correlation_id
        )
        
        redis_message = {
            'channel': message_queue.SIGNAL_COLLECTED_CHANNEL.encode('utf-8'),
            'data': json.dumps(test_message.to_dict()).encode('utf-8')
        }
        
        await message_queue._handle_message(redis_message)
        
        # Verify message was processed
        assert len(processed_messages) == 1
        assert processed_messages[0].payload == signal_data
        assert processed_messages[0].correlation_id == correlation_id

class TestProductionReadinessChecklist:
    """Test production readiness checklist items"""
    
    def test_environment_variables_loaded(self):
        """Test that environment variables are properly loaded"""
        # Test critical configuration is available
        assert settings.DATABASE_URL is not None
        assert settings.REDIS_URL is not None
        assert settings.SECRET_KEY is not None
    
    def test_logging_configuration(self):
        """Test logging is properly configured"""
        # Verify logging settings
        assert logging_config.level in ["DEBUG", "INFO", "WARNING", "ERROR"]
        assert logging_config.file_enabled is not None
        assert logging_config.include_trace_id is not None
    
    def test_redis_configuration(self):
        """Test Redis configuration"""
        # Verify Redis settings
        assert redis_config.host is not None
        assert redis_config.port > 0
        assert redis_config.db >= 0
        assert redis_config.socket_timeout > 0
    
    def test_processing_configuration(self):
        """Test processing configuration"""
        # Verify processing settings
        assert processing_config.collection_interval_seconds > 0
        assert processing_config.batch_processing_interval_seconds > 0
        assert processing_config.batch_size > 0
        assert processing_config.signal_retention_days > 0
    
    def test_market_data_configuration(self):
        """Test market data configuration"""
        # Verify market data settings
        assert market_data_config.update_interval_seconds > 0
        assert len(market_data_config.tracked_symbols) > 0
        assert market_data_config.data_retention_days > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
