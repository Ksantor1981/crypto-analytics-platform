"""
ML Predictions API
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import time
import logging
import sys
import os

# Add workers to path for real data integration
sys.path.append(os.path.join(os.path.dirname(__file__), '../../workers'))

try:
    from workers.exchange.bybit_client import BybitClient
    from workers.real_data_config import CRYPTO_SYMBOLS
    REAL_DATA_AVAILABLE = True
    print("✅ Real data integration: AVAILABLE")
except ImportError as e:
    REAL_DATA_AVAILABLE = False
    print(f"⚠️ Real data integration: NOT AVAILABLE ({e})")

# Fallback: try alternative import path
if not REAL_DATA_AVAILABLE:
    try:
        # Try from project root
        sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
        from workers.exchange.bybit_client import BybitClient
        from workers.real_data_config import CRYPTO_SYMBOLS
        REAL_DATA_AVAILABLE = True
        print("✅ Real data integration: AVAILABLE (fallback path)")
    except ImportError as e:
        print(f"❌ Real data integration: FAILED ({e})")

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

@router.post("/predict", response_model=PredictionResponse)
async def predict_signal(request: PredictionRequest) -> PredictionResponse:
    """
    Предсказание успешности торгового сигнала с использованием реальных данных
    """
    try:
        # Получаем реальные рыночные данные если доступно
        market_data = {}
        current_price = request.entry_price
        
        if REAL_DATA_AVAILABLE:
            try:
                async with BybitClient() as client:
                    # Нормализуем символ для Bybit
                    bybit_symbol = request.asset.replace("/", "").upper()
                    if not bybit_symbol.endswith("USDT"):
                        bybit_symbol += "USDT"
                    
                    # Получаем реальные рыночные данные
                    real_market_data = await client.get_market_data([bybit_symbol])
                    
                    if bybit_symbol in real_market_data:
                        data = real_market_data[bybit_symbol]
                        current_price = float(data.get('current_price', request.entry_price))
                        
                        market_data = {
                            "current_price": current_price,
                            "change_24h": float(data.get('change_24h', 0)),
                            "high_24h": float(data.get('high_24h', current_price)),
                            "low_24h": float(data.get('low_24h', current_price)),
                            "volume_24h": float(data.get('volume_24h', 0)),
                            "source": "bybit_real",
                            "timestamp": data.get('timestamp')
                        }
                        
                        logger.info(f"✅ Got real market data for {bybit_symbol}: ${current_price}")
                    else:
                        logger.warning(f"⚠️ No real data for {bybit_symbol}, using provided price")
                        
            except Exception as e:
                logger.error(f"Error getting real market data: {e}")
                
        # Если реальные данные недоступны, используем переданные
        if not market_data:
            market_data = {
                "current_price": current_price,
                "source": "provided",
                "timestamp": None
            }
        
        # Подготавливаем данные для предсказания
        signal_data = {
            'asset': request.asset,
            'entry_price': request.entry_price,
            'current_price': current_price,
            'target_price': request.target_price,
            'stop_loss': request.stop_loss,
            'direction': request.direction.upper(),
            'market_data': market_data
        }
        
        # Делаем предсказание с исправленным предиктором
        prediction_result = predictor.predict(signal_data)
        
        # Преобразуем результат в нужный формат
        success_prob = prediction_result.get('success_probability', 0.5)
        
        # Определяем prediction как SUCCESS/FAIL
        prediction_status = "SUCCESS" if success_prob >= 0.5 else "FAIL"
        
        # Вычисляем ожидаемую доходность
        expected_return = 0.0
        if request.target_price and request.entry_price > 0:
            if request.direction.upper() == "LONG":
                expected_return = ((request.target_price - request.entry_price) / request.entry_price) * 100 * success_prob
            else:
                expected_return = ((request.entry_price - request.target_price) / request.entry_price) * 100 * success_prob
        
        # Определяем уровень риска
        risk_score = prediction_result.get('risk_score', 0.5)
        if risk_score < 0.3:
            risk_level = "LOW"
        elif risk_score < 0.7:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"
        
        # Определяем рекомендацию на основе реальных данных
        recommendation = prediction_result.get('recommendation', 'НЕЙТРАЛЬНО')
        if market_data.get('change_24h', 0) > 0 and success_prob > 0.7:
            recommendation = "STRONG_BUY"
        elif success_prob > 0.6:
            recommendation = "BUY"
        elif success_prob < 0.4:
            recommendation = "SELL"
        else:
            recommendation = "HOLD"
        
        return PredictionResponse(
            asset=request.asset,
            prediction=prediction_status,
            confidence=prediction_result.get('confidence', 0.5),
            expected_return=expected_return,
            risk_level=risk_level,
            market_data=market_data,
            recommendation=recommendation
        )
        
    except Exception as e:
        logger.error(f"Error in prediction: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

@router.get("/market-data/{asset}")
async def get_market_data(asset: str) -> Dict[str, Any]:
    """
    Получение реальных рыночных данных для актива
    """
    try:
        if not REAL_DATA_AVAILABLE:
            raise HTTPException(status_code=503, detail="Real data integration not available")
            
        async with BybitClient() as client:
            # Нормализуем символ
            bybit_symbol = asset.replace("/", "").upper()
            if not bybit_symbol.endswith("USDT"):
                bybit_symbol += "USDT"
            
            # Получаем данные
            market_data = await client.get_market_data([bybit_symbol])
            
            if bybit_symbol in market_data:
                return {
                    "success": True,
                    "data": market_data[bybit_symbol]
                }
            else:
                raise HTTPException(status_code=404, detail=f"Market data not found for {asset}")
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting market data: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/supported-assets")
async def get_supported_assets() -> Dict[str, Any]:
    """
    Получение списка поддерживаемых активов
    """
    try:
        assets = CRYPTO_SYMBOLS if REAL_DATA_AVAILABLE else [
            "BTCUSDT", "ETHUSDT", "ADAUSDT", "BNBUSDT", "SOLUSDT",
            "DOGEUSDT", "DOTUSDT", "AVAXUSDT", "LINKUSDT", "XRPUSDT"
        ]
        
        # Проверяем доступность реальных данных
        real_data_status = "available" if REAL_DATA_AVAILABLE else "mock_only"
        
        return {
            "supported_assets": assets,
            "total_count": len(assets),
            "real_data_status": real_data_status,
            "data_source": "bybit" if REAL_DATA_AVAILABLE else "mock"
        }
        
    except Exception as e:
        logger.error(f"Error getting supported assets: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.post("/batch-predict")
async def batch_predict(assets: List[str], background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """
    Массовое предсказание для нескольких активов
    """
    try:
        if not REAL_DATA_AVAILABLE:
            raise HTTPException(status_code=503, detail="Real data required for batch predictions")
            
        results = {}
        
        async with BybitClient() as client:
            # Получаем рыночные данные для всех активов
            bybit_symbols = []
            for asset in assets:
                bybit_symbol = asset.replace("/", "").upper()
                if not bybit_symbol.endswith("USDT"):
                    bybit_symbol += "USDT"
                bybit_symbols.append(bybit_symbol)
            
            market_data = await client.get_market_data(bybit_symbols)
            
            # Делаем предсказания для каждого актива
            for i, asset in enumerate(assets):
                bybit_symbol = bybit_symbols[i]
                
                if bybit_symbol in market_data:
                    data = market_data[bybit_symbol]
                    current_price = float(data.get('current_price', 0))
                    
                    # Простое предсказание на основе рыночных данных
                    change_24h = float(data.get('change_24h', 0))
                    volume_24h = float(data.get('volume_24h', 0))
                    
                    # Оценка тренда
                    trend = "BULLISH" if change_24h > 2 else "BEARISH" if change_24h < -2 else "NEUTRAL"
                    
                    # Оценка волатильности
                    high_24h = float(data.get('high_24h', current_price))
                    low_24h = float(data.get('low_24h', current_price))
                    volatility = ((high_24h - low_24h) / current_price * 100) if current_price > 0 else 0
                    
                    results[asset] = {
                        "current_price": current_price,
                        "change_24h": change_24h,
                        "trend": trend,
                        "volatility": f"{volatility:.2f}%",
                        "volume_24h": volume_24h,
                        "recommendation": "BUY" if change_24h > 1 else "SELL" if change_24h < -1 else "HOLD"
                    }
                else:
                    results[asset] = {"error": "Market data not available"}
        
        return {
            "success": True,
            "results": results,
            "total_analyzed": len(results),
            "timestamp": market_data.get(bybit_symbols[0], {}).get('timestamp') if bybit_symbols else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch prediction: {e}")
        raise HTTPException(status_code=500, detail=f"Batch prediction error: {str(e)}")

@router.get("/model/info", response_model=ModelInfoResponse)
async def get_model_info():
    """
    Информация о модели
    """
    try:
        model_info = predictor.get_model_info()
        return ModelInfoResponse(**model_info)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Model info error: {str(e)}"
        ) 