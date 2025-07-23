"""
Production-ready message queue system using Redis Pub/Sub
Provides event-driven communication between services
"""
import asyncio
import json
import uuid
import redis.asyncio as redis
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from app.core.production_logging import get_logger, set_trace_id, get_trace_id

logger = get_logger(__name__)

class MessagePriority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class QueueMessage:
    """Message structure for queue communication"""
    id: str
    type: str
    payload: Dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    correlation_id: Optional[str] = None
    created_at: Optional[str] = None
    max_retries: int = 3
    retry_count: int = 0
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()
        if self.correlation_id is None:
            self.correlation_id = get_trace_id()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        data = asdict(self)
        data['priority'] = self.priority.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QueueMessage':
        """Create message from dictionary"""
        if 'priority' in data:
            data['priority'] = MessagePriority(data['priority'])
        return cls(**data)

class RedisMessageQueue:
    """Redis-based message queue with Pub/Sub"""
    
    # Channel names
    SIGNAL_COLLECTED_CHANNEL = "signals.collected"
    SIGNAL_PROCESSED_CHANNEL = "signals.processed"
    MARKET_DATA_UPDATED_CHANNEL = "market_data.updated"
    METRICS_CALCULATED_CHANNEL = "metrics.calculated"
    ERROR_CHANNEL = "system.errors"
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self.subscribers: Dict[str, List[Callable]] = {}
        self.running = False
        
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            self.pubsub = self.redis_client.pubsub()
            logger.info("Connected to Redis message queue")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from Redis"""
        self.running = False
        if self.pubsub:
            await self.pubsub.close()
        if self.redis_client:
            await self.redis_client.close()
        logger.info("Disconnected from Redis message queue")
    
    async def publish_message(self, channel: str, message: QueueMessage) -> bool:
        """Publish message to channel"""
        try:
            if not self.redis_client:
                await self.connect()
            
            # Set trace ID if available
            if message.correlation_id:
                set_trace_id(message.correlation_id)
            
            message_data = json.dumps(message.to_dict())
            result = await self.redis_client.publish(channel, message_data)
            
            logger.info(f"Published message to {channel}", extra={
                "message_id": message.id,
                "message_type": message.type,
                "channel": channel,
                "subscribers": result
            })
            
            return result > 0
            
        except Exception as e:
            logger.error(f"Failed to publish message to {channel}: {e}", extra={
                "message_id": message.id,
                "channel": channel
            })
            return False
    
    async def subscribe_to_channel(self, channel: str, handler: Callable[[QueueMessage], None]):
        """Subscribe to channel with message handler"""
        if channel not in self.subscribers:
            self.subscribers[channel] = []
        
        self.subscribers[channel].append(handler)
        
        if self.pubsub:
            await self.pubsub.subscribe(channel)
            logger.info(f"Subscribed to channel: {channel}")
    
    async def start_listening(self):
        """Start listening for messages"""
        if not self.pubsub:
            await self.connect()
        
        self.running = True
        logger.info("Started message queue listener")
        
        try:
            async for message in self.pubsub.listen():
                if not self.running:
                    break
                
                if message['type'] == 'message':
                    await self._handle_message(message)
                    
        except Exception as e:
            logger.error(f"Error in message listener: {e}")
        finally:
            self.running = False
    
    async def _handle_message(self, redis_message: Dict[str, Any]):
        """Handle incoming message"""
        try:
            channel = redis_message['channel'].decode('utf-8')
            data = json.loads(redis_message['data'].decode('utf-8'))
            message = QueueMessage.from_dict(data)
            
            # Set trace ID for processing
            if message.correlation_id:
                set_trace_id(message.correlation_id)
            
            logger.info(f"Received message from {channel}", extra={
                "message_id": message.id,
                "message_type": message.type,
                "channel": channel
            })
            
            # Call all handlers for this channel
            if channel in self.subscribers:
                for handler in self.subscribers[channel]:
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            await handler(message)
                        else:
                            handler(message)
                    except Exception as e:
                        logger.error(f"Handler error for {channel}: {e}", extra={
                            "message_id": message.id,
                            "handler": handler.__name__
                        })
                        
                        # Schedule retry if not exceeded max retries
                        if message.retry_count < message.max_retries:
                            await self._schedule_retry(message, channel)
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def _schedule_retry(self, message: QueueMessage, channel: str):
        """Schedule message retry"""
        message.retry_count += 1
        retry_delay = min(2 ** message.retry_count, 60)  # Exponential backoff, max 60s
        
        logger.warning(f"Scheduling retry {message.retry_count}/{message.max_retries} for message {message.id} in {retry_delay}s")
        
        # Use Redis sorted set for delayed retry
        retry_time = datetime.utcnow() + timedelta(seconds=retry_delay)
        retry_data = {
            "message": message.to_dict(),
            "channel": channel,
            "retry_time": retry_time.isoformat()
        }
        
        await self.redis_client.zadd(
            "message_retries",
            {json.dumps(retry_data): retry_time.timestamp()}
        )
    
    # Convenience methods for specific message types
    async def publish_signal_collected(self, signal_data: Dict[str, Any], correlation_id: Optional[str] = None):
        """Publish signal collected event"""
        message = QueueMessage(
            id=str(uuid.uuid4()),
            type="signal_collected",
            payload=signal_data,
            correlation_id=correlation_id
        )
        return await self.publish_message(self.SIGNAL_COLLECTED_CHANNEL, message)
    
    async def publish_signal_processed(self, processed_data: Dict[str, Any], correlation_id: Optional[str] = None):
        """Publish signal processed event"""
        message = QueueMessage(
            id=str(uuid.uuid4()),
            type="signal_processed",
            payload=processed_data,
            correlation_id=correlation_id
        )
        return await self.publish_message(self.SIGNAL_PROCESSED_CHANNEL, message)
    
    async def publish_market_data_updated(self, market_data: Dict[str, Any], correlation_id: Optional[str] = None):
        """Publish market data updated event"""
        message = QueueMessage(
            id=str(uuid.uuid4()),
            type="market_data_updated",
            payload=market_data,
            correlation_id=correlation_id
        )
        return await self.publish_message(self.MARKET_DATA_UPDATED_CHANNEL, message)
    
    async def publish_metrics_calculated(self, metrics_data: Dict[str, Any], correlation_id: Optional[str] = None):
        """Publish metrics calculated event"""
        message = QueueMessage(
            id=str(uuid.uuid4()),
            type="metrics_calculated",
            payload=metrics_data,
            correlation_id=correlation_id
        )
        return await self.publish_message(self.METRICS_CALCULATED_CHANNEL, message)
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        if not self.redis_client:
            return {}
        
        try:
            stats = {
                "delayed_messages": await self.redis_client.zcard("message_retries"),
                "dead_letter_messages": await self.redis_client.llen("dead_letter_queue"),
                "processing_messages": await self.redis_client.scard("processing_messages"),
                "active_channels": len(self.subscribers),
                "total_subscribers": sum(len(handlers) for handlers in self.subscribers.values())
            }
            return stats
        except Exception as e:
            logger.error(f"Error getting queue stats: {e}")
            return {}

# Global message queue instance
message_queue = RedisMessageQueue()

# Export main classes and functions
__all__ = [
    'QueueMessage',
    'MessagePriority',
    'RedisMessageQueue',
    'message_queue'
]
