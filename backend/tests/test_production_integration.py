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

from app.core.production_logging import get_logger, set_trace_id
from app.services.message_queue import RedisMessageQueue, QueueMessage, MessagePriority
from app.core.config import get_settings

# Initialize settings
settings = get_settings()

class TestProductionIntegration:
    """Integration tests for production-ready systems"""
    
    @pytest.fixture
    async def mock_redis_client(self):
        """Mock Redis client for testing"""
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)
        mock_client.publish = AsyncMock(return_value=1)
        mock_client.close = AsyncMock()
        mock_client.zcard = AsyncMock(return_value=0)
        mock_client.llen = AsyncMock(return_value=0)
        mock_client.scard = AsyncMock(return_value=0)
        
        mock_pubsub = AsyncMock()
        mock_pubsub.subscribe = AsyncMock()
        mock_pubsub.unsubscribe = AsyncMock()
        mock_pubsub.close = AsyncMock()
        mock_pubsub.listen = AsyncMock()
        
        mock_client.pubsub = MagicMock(return_value=mock_pubsub)
        
        return mock_client, mock_pubsub
    
    @pytest.fixture
    async def message_queue(self, mock_redis_client):
        """Create message queue with mocked Redis"""
        mock_client, mock_pubsub = mock_redis_client
        
        queue = RedisMessageQueue()
        
        with patch('app.services.message_queue.redis.Redis', return_value=mock_client):
            await queue.connect()
        
        yield queue
        
        await queue.disconnect()
    
    @pytest.mark.asyncio
    async def test_logging_with_message_queue_integration(self, message_queue):
        """Test logging integration with message queue"""
        # Setup logger with trace ID
        logger = get_logger("integration_test")
        trace_id = set_trace_id("integration-test-123")
        
        # Create test message
        test_message = QueueMessage(
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
    async def test_signal_processing_workflow(self, message_queue):
        """Test complete signal processing workflow"""
        # Mock signal data
        signal_data = {
            "channel": "test_channel",
            "message_text": "BUY BTC at $50000",
            "timestamp": datetime.utcnow().isoformat(),
            "confidence": 0.8
        }
        
        # Track processed messages
        processed_messages = []
        
        async def signal_processor_handler(message: QueueMessage):
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
        test_message = QueueMessage(
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
    
    @pytest.mark.asyncio
    async def test_market_data_processing_workflow(self, message_queue):
        """Test market data processing workflow"""
        # Mock market data
        market_data = {
            "symbol": "bitcoin",
            "current_price": 50000.0,
            "volume_24h": 1000000000,
            "price_change_24h": 2.5,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Track metrics calculations
        calculated_metrics = []
        
        async def metrics_calculator_handler(message: QueueMessage):
            """Mock metrics calculator handler"""
            data = message.payload
            
            # Simulate metrics calculation
            metrics = {
                "symbol": data["symbol"],
                "volatility": 0.15,
                "trend": "bullish",
                "momentum": 0.8,
                "calculated_at": datetime.utcnow().isoformat()
            }
            
            calculated_metrics.append(metrics)
            
            await message_queue.publish_metrics_calculated({
                "symbol": data["symbol"],
                "metrics": metrics
            })
        
        # Subscribe to market data updates
        await message_queue.subscribe_to_channel(
            message_queue.MARKET_DATA_UPDATED_CHANNEL,
            metrics_calculator_handler
        )
        
        # Publish market data update
        await message_queue.publish_market_data_updated(market_data)
        
        # Simulate message handling
        test_message = QueueMessage(
            id="market-123",
            type="market_data_updated",
            payload=market_data
        )
        
        redis_message = {
            'channel': message_queue.MARKET_DATA_UPDATED_CHANNEL.encode('utf-8'),
            'data': json.dumps(test_message.to_dict()).encode('utf-8')
        }
        
        await message_queue._handle_message(redis_message)
        
        # Verify metrics were calculated
        assert len(calculated_metrics) == 1
        assert calculated_metrics[0]["symbol"] == "bitcoin"
        assert "volatility" in calculated_metrics[0]
    
    @pytest.mark.asyncio
    async def test_error_handling_workflow(self, message_queue):
        """Test error handling across systems"""
        # Track errors
        error_messages = []
        
        async def error_handler(message: QueueMessage):
            """Handler that always fails"""
            error_messages.append(message)
            raise ValueError("Simulated processing error")
        
        # Subscribe with failing handler
        await message_queue.subscribe_to_channel("test_error_channel", error_handler)
        
        # Create test message
        test_message = QueueMessage(
            id="error-test-123",
            type="test_error",
            payload={"test": "error"},
            max_retries=2
        )
        
        # Mock retry scheduling
        message_queue.redis_client.zadd = AsyncMock()
        
        # Simulate message handling
        redis_message = {
            'channel': b'test_error_channel',
            'data': json.dumps(test_message.to_dict()).encode('utf-8')
        }
        
        await message_queue._handle_message(redis_message)
        
        # Verify error was handled and retry scheduled
        assert len(error_messages) == 1
        message_queue.redis_client.zadd.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_performance_monitoring(self, message_queue):
        """Test performance monitoring across systems"""
        import time
        
        # Track performance metrics
        performance_data = []
        
        async def performance_handler(message: QueueMessage):
            """Handler that tracks performance"""
            start_time = time.time()
            
            # Simulate processing
            await asyncio.sleep(0.01)  # 10ms processing time
            
            duration = time.time() - start_time
            performance_data.append({
                "message_id": message.id,
                "processing_time": duration,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Subscribe handler
        await message_queue.subscribe_to_channel("performance_test", performance_handler)
        
        # Send multiple messages
        for i in range(5):
            test_message = QueueMessage(
                id=f"perf-{i}",
                type="performance_test",
                payload={"index": i}
            )
            
            redis_message = {
                'channel': b'performance_test',
                'data': json.dumps(test_message.to_dict()).encode('utf-8')
            }
            
            await message_queue._handle_message(redis_message)
        
        # Verify all messages were processed
        assert len(performance_data) == 5
        
        # Check performance metrics
        avg_time = sum(p["processing_time"] for p in performance_data) / len(performance_data)
        assert avg_time > 0.005  # At least 5ms (due to sleep)
        assert avg_time < 0.1    # Less than 100ms
    
    @pytest.mark.asyncio
    async def test_configuration_integration(self):
        """Test configuration integration across systems"""
        # Test that all systems use the same configuration
        from app.core.config import (
            redis_config, telegram_config, processing_config,
            market_data_config, logging_config
        )
        
        # Verify Redis configuration
        assert redis_config.host == "localhost"
        assert redis_config.port == 6379
        assert redis_config.db == 0
        
        # Verify processing configuration
        assert processing_config.collection_interval_seconds == 60
        assert processing_config.batch_processing_interval_seconds == 30
        assert processing_config.batch_size == 100
        
        # Verify market data configuration
        assert market_data_config.update_interval_seconds == 300
        assert len(market_data_config.tracked_symbols) > 0
        
        # Verify logging configuration
        assert logging_config.level == "INFO"
        assert logging_config.include_trace_id is True
    
    @pytest.mark.asyncio
    async def test_health_check_integration(self, message_queue):
        """Test health check integration"""
        # Get queue statistics
        stats = await message_queue.get_queue_stats()
        
        # Verify statistics structure
        assert "delayed_messages" in stats
        assert "dead_letter_messages" in stats
        assert "processing_messages" in stats
        assert "active_channels" in stats
        assert "total_subscribers" in stats
        
        # All should be 0 for clean test environment
        assert stats["delayed_messages"] == 0
        assert stats["dead_letter_messages"] == 0
        assert stats["processing_messages"] == 0
    
    @pytest.mark.asyncio
    async def test_graceful_shutdown(self, message_queue):
        """Test graceful shutdown of systems"""
        # Add some subscribers
        async def dummy_handler(message):
            pass
        
        await message_queue.subscribe_to_channel("test_shutdown", dummy_handler)
        
        # Verify subscription
        assert "test_shutdown" in message_queue.subscribers
        
        # Test graceful disconnect
        await message_queue.disconnect()
        
        # Verify cleanup
        assert not message_queue.running
        message_queue.redis_client.close.assert_called_once()
        message_queue.pubsub.close.assert_called_once()

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
        from app.core.config import logging_config
        
        # Verify logging settings
        assert logging_config.level in ["DEBUG", "INFO", "WARNING", "ERROR"]
        assert logging_config.file_enabled is not None
        assert logging_config.include_trace_id is not None
        
    def test_redis_configuration(self):
        """Test Redis configuration"""
        from app.core.config import redis_config
        
        # Verify Redis settings
        assert redis_config.host is not None
        assert redis_config.port > 0
        assert redis_config.db >= 0
        assert redis_config.socket_timeout > 0
        
    def test_processing_configuration(self):
        """Test processing configuration"""
        from app.core.config import processing_config
        
        # Verify processing settings
        assert processing_config.collection_interval_seconds > 0
        assert processing_config.batch_processing_interval_seconds > 0
        assert processing_config.batch_size > 0
        assert processing_config.signal_retention_days > 0
        
    def test_market_data_configuration(self):
        """Test market data configuration"""
        from app.core.config import market_data_config
        
        # Verify market data settings
        assert market_data_config.update_interval_seconds > 0
        assert market_data_config.api_timeout_seconds > 0
        assert len(market_data_config.tracked_symbols) > 0
        assert market_data_config.data_retention_days > 0
        
    def test_telegram_configuration(self):
        """Test Telegram configuration"""
        from app.core.config import telegram_config
        
        # Verify Telegram settings
        assert telegram_config.session_name is not None
        assert isinstance(telegram_config.channels, list)
        
    def test_security_configuration(self):
        """Test security configuration"""
        # Verify JWT settings
        assert settings.SECRET_KEY is not None
        assert len(settings.SECRET_KEY) >= 32  # Minimum secure length
        assert settings.JWT_ALGORITHM == "HS256"
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0

class TestSystemStability:
    """Test system stability under various conditions"""
    
    @pytest.mark.asyncio
    async def test_concurrent_message_processing(self):
        """Test concurrent message processing"""
        queue = RedisMessageQueue()
        
        # Mock Redis client
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)
        mock_client.publish = AsyncMock(return_value=1)
        
        mock_pubsub = AsyncMock()
        mock_client.pubsub = MagicMock(return_value=mock_pubsub)
        
        with patch('app.services.message_queue.redis.Redis', return_value=mock_client):
            await queue.connect()
        
        # Track processed messages
        processed_count = 0
        processing_lock = asyncio.Lock()
        
        async def concurrent_handler(message: QueueMessage):
            nonlocal processed_count
            async with processing_lock:
                processed_count += 1
                await asyncio.sleep(0.001)  # Simulate processing
        
        await queue.subscribe_to_channel("concurrent_test", concurrent_handler)
        
        # Create multiple messages
        messages = []
        for i in range(10):
            message = QueueMessage(
                id=f"concurrent-{i}",
                type="concurrent_test",
                payload={"index": i}
            )
            messages.append({
                'channel': b'concurrent_test',
                'data': json.dumps(message.to_dict()).encode('utf-8')
            })
        
        # Process messages concurrently
        tasks = [queue._handle_message(msg) for msg in messages]
        await asyncio.gather(*tasks)
        
        # Verify all messages were processed
        assert processed_count == 10
        
        await queue.disconnect()
    
    @pytest.mark.asyncio
    async def test_memory_usage_stability(self):
        """Test memory usage doesn't grow excessively"""
        import gc
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create and destroy many objects
        for i in range(1000):
            message = QueueMessage(
                id=f"memory-test-{i}",
                type="memory_test",
                payload={"data": "x" * 1000}  # 1KB payload
            )
            
            # Convert to dict and back
            data = message.to_dict()
            restored = QueueMessage.from_dict(data)
            
            # Clear references
            del message, data, restored
        
        # Force garbage collection
        gc.collect()
        
        # Check memory usage
        final_memory = process.memory_info().rss
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be reasonable (less than 50MB)
        assert memory_growth < 50 * 1024 * 1024, f"Memory grew by {memory_growth / 1024 / 1024:.2f}MB"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
