"""
ML Service Integration API
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import httpx
import logging
from datetime import datetime

from ...core.database import get_db
from ...models.signal import Signal
from ...models.user import User
from ...core.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ml", tags=["ml-integration"])

# ML Service configuration
ML_SERVICE_URL = "http://localhost:8001"  # В продакшене из env переменных

# Pydantic models
class MLPredictionRequest(BaseModel):
    signal_id: int = Field(..., description="Signal ID to predict")

class DirectMLPredictionRequest(BaseModel):
    # Изменяем формат для соответствия ML Service API
    asset: str = Field(..., description="Asset symbol (e.g., BTCUSDT)")
    entry_price: float = Field(..., description="Entry price")
    target_price: Optional[float] = Field(None, description="Target price")
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    confidence: Optional[float] = Field(0.5, description="Signal confidence")
    direction: Optional[str] = Field("LONG", description="Signal direction")
    
class MLPredictionResponse(BaseModel):
    signal_id: int
    success_probability: float
    confidence: float
    recommendation: str
    risk_score: float
    features_importance: Dict[str, float]
    model_version: str
    prediction_timestamp: datetime

class BatchMLPredictionRequest(BaseModel):
    signal_ids: List[int] = Field(..., description="List of signal IDs to predict")
    
class BatchMLPredictionResponse(BaseModel):
    predictions: List[MLPredictionResponse]
    total_processed: int
    failed_predictions: List[int]

@router.post("/predict/signal", response_model=MLPredictionResponse)
async def predict_signal(
    request: MLPredictionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get ML prediction for a specific signal
    """
    try:
        # Get signal from database
        signal = db.query(Signal).filter(Signal.id == request.signal_id).first()
        if not signal:
            raise HTTPException(status_code=404, detail="Signal not found")
        
        # Prepare data for ML service
        ml_request_data = {
            "asset": signal.asset,
            "direction": signal.direction,
            "entry_price": float(signal.entry_price),
            "target_price": float(signal.target_price) if signal.target_price else None,
            "stop_loss": float(signal.stop_loss) if signal.stop_loss else None,
            "channel_id": signal.channel_id,
            "channel_accuracy": signal.channel.accuracy if signal.channel else 0.5,
            "confidence": float(signal.confidence) if signal.confidence else 0.5
        }
        
        # Call ML service
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{ML_SERVICE_URL}/api/v1/predictions/signal",
                json=ml_request_data
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=500,
                    detail=f"ML service error: {response.status_code}"
                )
            
            ml_prediction = response.json()
            
            # Convert to our response format
            return MLPredictionResponse(
                signal_id=request.signal_id,
                success_probability=ml_prediction["success_probability"],
                confidence=ml_prediction["confidence"],
                recommendation=ml_prediction["recommendation"],
                risk_score=ml_prediction["risk_score"],
                features_importance=ml_prediction["features_importance"],
                model_version=ml_prediction["model_version"],
                prediction_timestamp=ml_prediction["prediction_timestamp"]
            )
            
    except httpx.RequestError as e:
        logger.error(f"ML service request error: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="ML service unavailable"
        )
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Prediction error: {str(e)}"
        )

@router.post("/predict/batch", response_model=BatchMLPredictionResponse)
async def predict_batch_signals(
    request: BatchMLPredictionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get ML predictions for multiple signals
    """
    try:
        # Get signals from database
        signals = db.query(Signal).filter(Signal.id.in_(request.signal_ids)).all()
        
        if not signals:
            raise HTTPException(status_code=404, detail="No signals found")
        
        # Prepare batch data for ML service
        ml_signals = []
        for signal in signals:
            ml_request_data = {
                "asset": signal.asset,
                "direction": signal.direction,
                "entry_price": float(signal.entry_price),
                "target_price": float(signal.target_price) if signal.target_price else None,
                "stop_loss": float(signal.stop_loss) if signal.stop_loss else None,
                "channel_id": signal.channel_id,
                "channel_accuracy": signal.channel.accuracy if signal.channel else 0.5,
                "confidence": float(signal.confidence) if signal.confidence else 0.5
            }
            ml_signals.append(ml_request_data)
        
        batch_request_data = {"signals": ml_signals}
        
        # Call ML service
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{ML_SERVICE_URL}/api/v1/predictions/batch",
                json=batch_request_data
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=500,
                    detail=f"ML service error: {response.status_code}"
                )
            
            ml_batch_result = response.json()
            
            # Convert to our response format
            predictions = []
            for i, ml_prediction in enumerate(ml_batch_result["predictions"]):
                signal_id = signals[i].id
                predictions.append(MLPredictionResponse(
                    signal_id=signal_id,
                    success_probability=ml_prediction["success_probability"],
                    confidence=ml_prediction["confidence"],
                    recommendation=ml_prediction["recommendation"],
                    risk_score=ml_prediction["risk_score"],
                    features_importance=ml_prediction["features_importance"],
                    model_version=ml_prediction["model_version"],
                    prediction_timestamp=ml_prediction["prediction_timestamp"]
                ))
            
            return BatchMLPredictionResponse(
                predictions=predictions,
                total_processed=len(predictions),
                failed_predictions=[]
            )
            
    except httpx.RequestError as e:
        logger.error(f"ML service request error: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="ML service unavailable"
        )
    except Exception as e:
        logger.error(f"Batch prediction error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Batch prediction error: {str(e)}"
        )

@router.post("/predict")
async def direct_ml_predict(request: DirectMLPredictionRequest):
    """
    Direct ML prediction without requiring signal in database
    """
    try:
        # Формируем данные в правильном формате для ML service
        ml_payload = {
            "asset": request.asset,
            "entry_price": request.entry_price,
            "target_price": request.target_price,
            "stop_loss": request.stop_loss,
            "confidence": request.confidence
        }
        
        # Убираем None значения
        ml_payload = {k: v for k, v in ml_payload.items() if v is not None}
        
        # Call ML service directly
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{ML_SERVICE_URL}/api/v1/predictions/predict",
                json=ml_payload
            )
            
            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"ML service error {response.status_code}: {error_detail}")
                raise HTTPException(
                    status_code=500,
                    detail=f"ML service error: {response.status_code} - {error_detail}"
                )
            
            return response.json()
            
    except httpx.RequestError as e:
        logger.error(f"ML service request error: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="ML service unavailable"
        )
    except Exception as e:
        logger.error(f"Direct prediction error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Prediction error: {str(e)}"
        )

@router.get("/health")
async def ml_service_health():
    """
    Check ML service health
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{ML_SERVICE_URL}/api/v1/health/")
            
            if response.status_code == 200:
                return {
                    "ml_service_status": "healthy",
                    "ml_service_response": response.json()
                }
            else:
                return {
                    "ml_service_status": "unhealthy",
                    "status_code": response.status_code
                }
                
    except httpx.RequestError as e:
        logger.error(f"ML service health check failed: {str(e)}")
        return {
            "ml_service_status": "unavailable",
            "error": str(e)
        }

@router.get("/model/info")
async def get_ml_model_info():
    """
    Get ML model information
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{ML_SERVICE_URL}/api/v1/predictions/model/info")
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to get model info"
                )
                
    except httpx.RequestError as e:
        logger.error(f"ML model info request failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="ML service unavailable"
        ) 