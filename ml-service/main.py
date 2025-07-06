"""
Crypto Analytics ML Service
Main FastAPI application
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
from datetime import datetime

# Import API routers
try:
    from api.predictions import router as predictions_router
    from api.health import router as health_router
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from api.predictions import router as predictions_router
    from api.health import router as health_router

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
    allow_origins=["*"],  # В продакшене заменить на конкретные домены
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

# Include routers without additional prefix since they already have prefixes
app.include_router(predictions_router)
app.include_router(health_router)

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
        "service_name": "ml-service",
        "service_type": "machine_learning",
        "version": "1.0.0",
        "description": "ML service for crypto signal analysis",
        "features": [
            "signal_success_prediction",
            "batch_predictions",
            "feature_importance_analysis",
            "risk_scoring"
        ],
        "model_type": "rule_based_mvp_stub",
        "supported_assets": ["BTC", "ETH", "BNB", "ADA", "SOL", "DOT", "MATIC", "AVAX"],
        "api_version": "v1"
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """
    Application startup event
    """
    logger.info("🚀 ML Service starting up...")
    logger.info("📊 Initializing ML models...")
    
    # В реальном проекте здесь будет загрузка обученных моделей
    # model = load_trained_models()
    
    logger.info("✅ ML Service startup completed")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown event
    """
    logger.info("🛑 ML Service shutting down...")
    logger.info("💾 Saving any pending data...")
    logger.info("✅ ML Service shutdown completed")

# Run the application
if __name__ == "__main__":
    import uvicorn
    
    # Configuration
    host = os.getenv("ML_SERVICE_HOST", "0.0.0.0")
    port = int(os.getenv("ML_SERVICE_PORT", "8001"))
    
    logger.info(f"Starting ML Service on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    ) 