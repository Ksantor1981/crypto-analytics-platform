"""
Structured logging configuration
"""
import logging
import sys
from typing import Any, Dict
import structlog
from pythonjsonlogger import jsonlogger

from .config import settings

def setup_logging() -> None:
    """Configure structured logging for the application."""
    
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
            structlog.processors.JSONRenderer() if settings.ENVIRONMENT == "production" else structlog.dev.ConsoleRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    
    if settings.ENVIRONMENT == "production":
        # JSON logging for production
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s'
        )
    else:
        # Human-readable logging for development
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Setup handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.setLevel(log_level)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)
    
    # Reduce noise from some libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    # Create application logger
    logger = structlog.get_logger(__name__)
    logger.info(
        "Logging configured",
        environment=settings.ENVIRONMENT,
        debug=settings.DEBUG,
        log_level=log_level
    )

def get_logger(name: str) -> Any:
    """Get a structured logger instance."""
    return structlog.get_logger(name)

# Security logging helpers
def log_security_event(event_type: str, details: Dict[str, Any], user_id: str = None) -> None:
    """Log security-related events."""
    logger = get_logger("security")
    logger.warning(
        "Security event",
        event_type=event_type,
        user_id=user_id,
        **details
    )

def log_authentication_attempt(success: bool, email: str, ip: str, user_agent: str = None) -> None:
    """Log authentication attempts."""
    logger = get_logger("auth")
    
    if success:
        logger.info(
            "Authentication successful",
            email=email,
            ip=ip,
            user_agent=user_agent
        )
    else:
        logger.warning(
            "Authentication failed",
            email=email,
            ip=ip,
            user_agent=user_agent
        )

def log_api_access(method: str, path: str, status_code: int, user_id: str = None, duration: float = None) -> None:
    """Log API access."""
    logger = get_logger("api")
    logger.info(
        "API access",
        method=method,
        path=path,
        status_code=status_code,
        user_id=user_id,
        duration_ms=duration * 1000 if duration else None
    ) 