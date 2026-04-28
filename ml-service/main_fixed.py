"""
Crypto Analytics ML Service - Fixed Version (legacy entrypoint, не используется Docker).
Production использует `main.py`. Этот файл — артефакт миграции _fixed→canonical (F9).
См. docs/SYSTEM_AUDIT_2026_04_28.md.
"""

import os
import sys

if (os.getenv("ENVIRONMENT", "development") or "development").lower() == "production":
    sys.stderr.write(
        "[ml-service/main_fixed.py] FATAL: legacy entrypoint, refusing to start "
        "under ENVIRONMENT=production. Use main:app instead.\n"
    )
    raise SystemExit(1)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Crypto Analytics ML Service",
    description="Machine Learning service for crypto signal analysis and predictions",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )

# Import API routers with error handling
routers = []

try:
    from api.health import router as health_router
    routers.append(("health", health_router))
    logger.info("✅ Health router loaded")
except ImportError as e:
    logger.warning(f"⚠️ Health router not available: {e}")

try:
    from api.predictions import router as predictions_router
    routers.append(("predictions", predictions_router))
    logger.info("✅ Predictions router loaded")
except ImportError as e:
    logger.warning(f"⚠️ Predictions router not available: {e}")

try:
    from api.backtesting import router as backtesting_router
    routers.append(("backtesting", backtesting_router))
    logger.info("✅ Backtesting router loaded")
except ImportError as e:
    logger.warning(f"⚠️ Backtesting router not available: {e}")

try:
    from api.risk_analysis import router as risk_analysis_router
    routers.append(("risk_analysis", risk_analysis_router))
    logger.info("✅ Risk analysis router loaded")
except ImportError as e:
    logger.warning(f"⚠️ Risk analysis router not available: {e}")

# Include available routers
for name, router in routers:
    app.include_router(router)
    logger.info(f"✅ Included {name} router")

# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint with service information
    """
    return {
        "service": "Crypto Analytics ML Service",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "health": "/api/v1/health",
            "predictions": "/api/v1/predictions",
            "backtesting": "/api/v1/backtesting",
            "risk_analysis": "/api/v1/risk-analysis",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }

@app.get("/api/v1/info")
async def service_info():
    """
    Service information endpoint
    """
    return {
        "service": "Crypto Analytics ML Service",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "Signal prediction",
            "Market analysis", 
            "Risk assessment",
            "Performance tracking",
            "Backtesting",
            "Real-time data integration"
        ],
        "available_routers": [name for name, _ in routers]
    }

@app.on_event("startup")
async def startup_event():
    """
    Startup event handler
    """
    logger.info("🚀 ML Service starting up...")
    logger.info("📊 Initializing ML models...")
    
    # Initialize any required services
    try:
        # Add any initialization logic here
        logger.info("✅ ML Service startup completed")
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Shutdown event handler
    """
    logger.info("🛑 ML Service shutting down...")
    logger.info("💾 Saving any pending data...")
    
    try:
        # Add any cleanup logic here
        logger.info("✅ ML Service shutdown completed")
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_fixed:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    ) 