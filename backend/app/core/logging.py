"""
Structured logging configuration using structlog
"""
import structlog
import logging
import sys
from typing import Dict, Any, Optional
from datetime import datetime

from app.core.config import get_settings

# Получаем настройки
settings = get_settings()

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer() if settings.ENVIRONMENT == "production" 
        else structlog.dev.ConsoleRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Configure standard library logging
logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
)

def get_logger(name: str = __name__) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance"""
    return structlog.get_logger(name)

def log_authentication_attempt(
    user_email: str,
    success: bool,
    ip_address: str,
    user_agent: str = None,
    additional_data: Dict[str, Any] = None
):
    """Log authentication attempts for security monitoring"""
    logger = get_logger("auth")
    
    log_data = {
        "event": "authentication_attempt",
        "user_email": user_email,
        "success": success,
        "ip_address": ip_address,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    if user_agent:
        log_data["user_agent"] = user_agent
    
    if additional_data:
        log_data.update(additional_data)
    
    if success:
        logger.info("Authentication successful", **log_data)
    else:
        logger.warning("Authentication failed", **log_data)

def log_security_event(
    event_type: str,
    user_id: Optional[int] = None,
    ip_address: str = None,
    details: Dict[str, Any] = None
):
    """Log security-related events"""
    logger = get_logger("security")
    
    log_data = {
        "event": "security_event",
        "event_type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    if user_id:
        log_data["user_id"] = user_id
    
    if ip_address:
        log_data["ip_address"] = ip_address
    
    if details:
        log_data.update(details)
    
    logger.warning("Security event detected", **log_data)

def log_api_request(
    method: str,
    endpoint: str,
    user_id: Optional[int] = None,
    ip_address: str = None,
    response_status: int = None,
    response_time_ms: float = None
):
    """Log API requests for monitoring"""
    logger = get_logger("api")
    
    log_data = {
        "event": "api_request",
        "method": method,
        "endpoint": endpoint,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    if user_id:
        log_data["user_id"] = user_id
    
    if ip_address:
        log_data["ip_address"] = ip_address
    
    if response_status:
        log_data["response_status"] = response_status
    
    if response_time_ms:
        log_data["response_time_ms"] = response_time_ms
    
    logger.info("API request", **log_data)

def log_signal_processing(
    signal_id: int,
    action: str,
    success: bool,
    details: Dict[str, Any] = None
):
    """Log signal processing events"""
    logger = get_logger("signals")
    
    log_data = {
        "event": "signal_processing",
        "signal_id": signal_id,
        "action": action,
        "success": success,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    if details:
        log_data.update(details)
    
    if success:
        logger.info("Signal processing successful", **log_data)
    else:
        logger.error("Signal processing failed", **log_data) 