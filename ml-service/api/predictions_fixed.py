"""
Fixed predictions API without problematic imports
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
import logging
import time
from datetime import datetime
import random

# Используем простой предиктор
from models.simple_predictor import SimplePredictor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/predictions", tags=["predictions"])

# Инициализируем модель
predictor = SimplePredictor()

# Pydantic модели
class SignalPredictionRequest(BaseModel):
    asset: str = Field(..., description="Asset symbol (e.g., BTC, ETH)")
    direction: str = Field(..., description="Signal direction (LONG/SHORT)")
    entry_price: float = Field(..., description="Entry price")
    target_price: float = Field(None, description="Target price")
    stop_loss: float = Field(None, description="Stop loss price")
    channel_id: int = Field(..., description="Channel ID")
    channel_accuracy: float = Field(0.5, description="Channel accuracy (0-1)")
    confidence: float = Field(0.5, description="Signal confidence (0-1)")

class SignalPredictionResponse(BaseModel):
    success_probability: float
    confidence: float
    recommendation: str
    risk_score: float
    features_importance: Dict[str, float]
    model_version: str
    prediction_timestamp: str

class BatchPredictionRequest(BaseModel):
    signals: List[SignalPredictionRequest]

class BatchPredictionResponse(BaseModel):
    predictions: List[SignalPredictionResponse]
    total_processed: int
    processing_time_ms: float

class ModelInfoResponse(BaseModel):
    model_version: str
    model_type: str
    is_trained: bool
    feature_names: List[str]
    created_at: str

class PredictionRequest(BaseModel):
    asset: str
    entry_price: float
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    direction: str = "LONG"

class PredictionResponse(BaseModel):
    asset: str
    prediction: str
    confidence: float
    expected_return: float
    risk_level: str
    market_data: Dict[str, Any]
    recommendation: str

# Mock market data for testing
MOCK_MARKET_DATA = {
    "BTC": {"price": 50000, "volume": 1000000, "change_24h": 2.5},
    "ETH": {"price": 3000, "volume": 500000, "change_24h": 1.8},
    "BNB": {"price": 400, "volume": 200000, "change_24h": 0.5},
    "SOL": {"price": 100, "volume": 150000, "change_24h": 3.2},
    "ADA": {"price": 0.5, "volume": 80000, "change_24h": -1.2},
    "DOT": {"price": 7, "volume": 120000, "change_24h": 0.8},
    "LINK": {"price": 15, "volume": 90000, "change_24h": 1.5},
    "UNI": {"price": 8, "volume": 70000, "change_24h": -0.3}
}

def get_mock_market_data(asset: str) -> Dict[str, Any]:
    """Get mock market data for an asset"""
    asset_upper = asset.upper()
    if asset_upper in MOCK_MARKET_DATA:
        data = MOCK_MARKET_DATA[asset_upper].copy()
        # Add some randomness to make it more realistic
        data["price"] += random.uniform(-0.01, 0.01) * data["price"]
        data["volume"] += random.uniform(-0.05, 0.05) * data["volume"]
        data["change_24h"] += random.uniform(-0.1, 0.1)
        return data
    else:
        # Default data for unknown assets
        return {
            "price": 100,
            "volume": 50000,
            "change_24h": 0.0,
            "market_cap": 1000000,
            "circulating_supply": 1000000
        }

@router.post("/predict", response_model=PredictionResponse)
async def predict_signal(request: PredictionRequest) -> PredictionResponse:
    """
    Предсказание успешности торгового сигнала
    """
    try:
        start_time = time.time()
        
        # Получаем mock рыночные данные
        market_data = get_mock_market_data(request.asset)
        current_price = market_data["price"]
        
        # Анализируем сигнал
        signal_data = {
            "asset": request.asset,
            "direction": request.direction,
            "entry_price": request.entry_price,
            "target_price": request.target_price,
            "stop_loss": request.stop_loss,
            "channel_accuracy": 0.7,  # Default value
            "confidence": 0.6  # Default value
        }
        
        # Получаем предсказание
        prediction_result = predictor.predict(signal_data)
        
        # Рассчитываем ожидаемую доходность
        expected_return = 0.0
        if request.target_price and request.entry_price:
            if request.direction == "LONG":
                expected_return = (request.target_price - request.entry_price) / request.entry_price * 100
            else:
                expected_return = (request.entry_price - request.target_price) / request.entry_price * 100
        
        # Определяем уровень риска
        risk_level = "LOW"
        if abs(expected_return) > 20:
            risk_level = "HIGH"
        elif abs(expected_return) > 10:
            risk_level = "MEDIUM"
        
        # Определяем рекомендацию
        recommendation = "HOLD"
        if prediction_result["recommendation"] == "BUY" and prediction_result["confidence"] > 0.7:
            recommendation = "BUY"
        elif prediction_result["recommendation"] == "SELL" and prediction_result["confidence"] > 0.7:
            recommendation = "SELL"
        
        processing_time = (time.time() - start_time) * 1000
        
        logger.info(f"✅ Prediction completed for {request.asset} in {processing_time:.2f}ms")
        
        return PredictionResponse(
            asset=request.asset,
            prediction=prediction_result["recommendation"],
            confidence=prediction_result["confidence"],
            expected_return=expected_return,
            risk_level=risk_level,
            market_data=market_data,
            recommendation=recommendation
        )
        
    except Exception as e:
        logger.error(f"❌ Prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@router.get("/market-data/{asset}")
async def get_market_data(asset: str) -> Dict[str, Any]:
    """
    Получение рыночных данных для актива
    """
    try:
        market_data = get_mock_market_data(asset)
        
        # Добавляем технические индикаторы
        market_data.update({
            "rsi": random.uniform(30, 70),
            "macd": random.uniform(-0.01, 0.01),
            "bollinger_position": random.uniform(0, 1),
            "volume_ratio": random.uniform(0.8, 1.2),
            "volatility": random.uniform(0.01, 0.05)
        })
        
        return {
            "asset": asset.upper(),
            "data": market_data,
            "timestamp": datetime.now().isoformat(),
            "source": "mock_data"
        }
        
    except Exception as e:
        logger.error(f"❌ Market data error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get market data: {str(e)}")

@router.get("/supported-assets")
async def get_supported_assets() -> Dict[str, Any]:
    """
    Получение списка поддерживаемых активов
    """
    return {
        "assets": list(MOCK_MARKET_DATA.keys()),
        "total_count": len(MOCK_MARKET_DATA),
        "timestamp": datetime.now().isoformat()
    }

@router.post("/batch-predict")
async def batch_predict(assets: List[str], background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """
    Пакетное предсказание для нескольких активов
    """
    try:
        start_time = time.time()
        results = []
        
        for asset in assets:
            try:
                # Создаем mock запрос для каждого актива
                request = PredictionRequest(
                    asset=asset,
                    entry_price=MOCK_MARKET_DATA.get(asset.upper(), {}).get("price", 100),
                    direction="LONG"
                )
                
                # Получаем предсказание
                prediction = await predict_signal(request)
                results.append(prediction.dict())
                
            except Exception as e:
                logger.error(f"❌ Batch prediction error for {asset}: {e}")
                results.append({
                    "asset": asset,
                    "error": str(e),
                    "status": "failed"
                })
        
        processing_time = (time.time() - start_time) * 1000
        
        return {
            "predictions": results,
            "total_processed": len(assets),
            "processing_time_ms": processing_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Batch prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")

@router.get("/model/info", response_model=ModelInfoResponse)
async def get_model_info():
    """
    Получение информации о модели
    """
    return ModelInfoResponse(
        model_version="1.0.0-fixed",
        model_type="simple_rule_based",
        is_trained=True,
        feature_names=["asset_type", "direction_score", "price_ratio", "base_confidence"],
        created_at=datetime.now().isoformat()
    )

@router.get("/health")
async def health_check():
    """
    Health check для predictions API
    """
    return {
        "status": "healthy",
        "service": "predictions",
        "timestamp": datetime.now().isoformat(),
        "model_status": "ready"
    } 