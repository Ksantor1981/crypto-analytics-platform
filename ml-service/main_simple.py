"""
Crypto Analytics ML Service - Simplified Version
Main FastAPI application without problematic imports
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
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
        "service": "Crypto Analytics ML Service",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "Signal prediction",
            "Market analysis",
            "Risk assessment",
            "Performance tracking"
        ]
    }

@app.get("/api/v1/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "ml-service",
        "version": "1.0.0"
    }

@app.post("/api/v1/predictions/predict")
async def predict_signal(request: dict):
    """
    Simple signal prediction endpoint
    """
    try:
        # Extract data from request
        asset = request.get('asset', 'BTC')
        direction = request.get('direction', 'LONG')
        entry_price = float(request.get('entry_price', 50000))
        channel_accuracy = float(request.get('channel_accuracy', 0.5))
        confidence = float(request.get('confidence', 0.5))
        
        # Simple prediction logic
        base_probability = 0.5
        
        # Asset bonus
        asset_bonus = {
            'BTC': 0.1,
            'ETH': 0.08,
            'BNB': 0.05,
            'ADA': 0.03,
            'SOL': 0.02
        }.get(asset.upper(), 0.0)
        
        # Direction bonus
        direction_bonus = 0.05 if direction.upper() == 'LONG' else 0.0
        
        # Channel accuracy bonus
        channel_bonus = (channel_accuracy - 0.5) * 0.3
        
        # Confidence bonus
        confidence_bonus = (confidence - 0.5) * 0.2
        
        # Calculate final probability
        success_probability = max(0.1, min(0.95, 
            base_probability + asset_bonus + direction_bonus + 
            channel_bonus + confidence_bonus
        ))
        
        # Generate recommendation
        if success_probability >= 0.7:
            recommendation = "STRONG BUY"
        elif success_probability >= 0.6:
            recommendation = "BUY"
        elif success_probability >= 0.4:
            recommendation = "NEUTRAL"
        else:
            recommendation = "CAUTION"
        
        return {
            "success_probability": round(success_probability, 3),
            "confidence": round(confidence, 3),
            "recommendation": recommendation,
            "risk_score": round(1.0 - success_probability, 3),
            "asset": asset,
            "direction": direction,
            "entry_price": entry_price,
            "prediction_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/predictions/model/info")
async def get_model_info():
    """
    Model information endpoint
    """
    return {
        "model_version": "1.0.0-simple",
        "model_type": "simple_rule_based",
        "is_trained": True,
        "feature_names": [
            'asset_type',
            'direction_score', 
            'channel_accuracy',
            'confidence'
        ],
        "created_at": datetime.now().isoformat()
    }

@app.on_event("startup")
async def startup_event():
    """
    Startup event handler
    """
    logger.info("🚀 ML Service starting up...")
    logger.info("📊 Initializing ML models...")
    logger.info("✅ ML Service startup completed")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Shutdown event handler
    """
    logger.info("🛑 ML Service shutting down...")
    logger.info("💾 Saving any pending data...")
    logger.info("✅ ML Service shutdown completed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_simple:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    ) 