"""
ML Service Health Check API
"""

from fastapi import APIRouter, Depends
from datetime import datetime
from typing import Dict, Any
import psutil
import os

from models.simple_predictor import SimplePredictor

router = APIRouter(prefix="/api/v1/health", tags=["health"])

@router.get("/")
async def health_check():
    """
    Basic health check endpoint
    """
    return {
        "status": "healthy",
        "service": "ml-service",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "model_info": {
            "version": "1.0.0-simple",
            "type": "simple_predictor",
            "features": 4
        }
    }

@router.get("/detailed")
async def detailed_health_check():
    """
    Detailed health check with system metrics
    """
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Model status
        model = SimplePredictor()
        model_status = {
            "model_version": "1.0.0-simple",
            "is_trained": True,
            "feature_count": 4,
            "features": ["entry_price", "target_price", "stop_loss", "direction"]
        }
        
        return {
            "status": "healthy",
            "service": "ml-service",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "system_metrics": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2)
            },
            "model_status": model_status
        }
        
    except Exception as e:
        return {
            "status": "degraded",
            "service": "ml-service",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@router.get("/readiness")
async def readiness_check():
    """
    Readiness check for Kubernetes/Docker deployments
    """
    try:
        # Check if model can be instantiated
        model = SimplePredictor()
        
        # Test prediction
        test_data = {
            "asset": "BTC",
            "direction": "LONG",
            "entry_price": 45000.0,
            "target_price": 47000.0,
            "stop_loss": 43000.0
        }
        
        prediction = model.predict(test_data)
        
        return {
            "status": "ready",
            "service": "ml-service",
            "timestamp": datetime.now().isoformat(),
            "test_prediction": prediction
        }
        
    except Exception as e:
        return {
            "status": "not_ready",
            "service": "ml-service",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@router.get("/liveness")
async def liveness_check():
    """
    Liveness check for Kubernetes/Docker deployments
    """
    return {
        "status": "alive",
        "service": "ml-service",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": _get_uptime_seconds()
    }

def _get_uptime_seconds() -> float:
    """
    Get service uptime in seconds
    """
    try:
        # Simple uptime calculation based on process start time
        process = psutil.Process(os.getpid())
        create_time = process.create_time()
        return datetime.now().timestamp() - create_time
    except:
        return 0.0 