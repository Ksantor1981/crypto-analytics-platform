"""
Simplified production-ready logging system
"""
import logging
import json
import uuid
import os
from datetime import datetime
from typing import Optional
from contextvars import ContextVar

# Context variable for trace ID
trace_id_context: ContextVar[Optional[str]] = ContextVar('trace_id', default=None)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)

def set_trace_id(trace_id: Optional[str] = None) -> str:
    """Set trace ID for current context"""
    if trace_id is None:
        trace_id = str(uuid.uuid4())
    
    trace_id_context.set(trace_id)
    return trace_id

def get_trace_id() -> Optional[str]:
    """Get current trace ID from context"""
    return trace_id_context.get()

def log_performance(logger: logging.Logger, operation: str, duration: float, **kwargs):
    """Log performance metrics"""
    trace_id = get_trace_id()
    message = f"Performance: {operation} completed in {duration:.3f}s"
    if trace_id:
        message += f" [trace_id: {trace_id[:8]}]"
    logger.info(message)

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
