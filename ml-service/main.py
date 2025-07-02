from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
import joblib
import os
from datetime import datetime

app = FastAPI(
    title="Crypto Analytics ML Service",
    description="ML service for crypto signal analysis",
    version="1.0.0",
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене заменить на конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Модели данных
class SignalPredictionRequest(BaseModel):
    asset: str
    direction: str
    entry_price: float
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    channel_id: int
    channel_accuracy: Optional[float] = None
    market_volatility: Optional[float] = None
    
class SignalPredictionResponse(BaseModel):
    success_probability: float
    confidence: float
    recommendation: str
    features_importance: Dict[str, float]

# Заглушка для модели (в реальном проекте здесь будет загрузка обученной модели)
def get_model():
    # В реальном проекте:
    # return joblib.load("models/signal_prediction_model.pkl")
    return "dummy_model"

# Эндпоинты
@app.get("/")
async def root():
    return {"message": "Welcome to Crypto Analytics ML Service"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/predict/signal", response_model=SignalPredictionResponse)
async def predict_signal_success(
    signal: SignalPredictionRequest,
    model=Depends(get_model)
):
    """
    Predict the probability of a trading signal being successful
    """
    try:
        # В реальном проекте здесь будет предобработка данных и вызов модели
        # features = preprocess_signal_data(signal)
        # prediction = model.predict_proba(features)
        
        # Заглушка для демонстрации
        success_probability = 0.75  # В реальном проекте это будет результат модели
        
        # Формируем рекомендацию на основе вероятности
        if success_probability > 0.8:
            recommendation = "STRONG_BUY"
        elif success_probability > 0.6:
            recommendation = "BUY"
        elif success_probability > 0.4:
            recommendation = "NEUTRAL"
        elif success_probability > 0.2:
            recommendation = "SELL"
        else:
            recommendation = "STRONG_SELL"
            
        # Заглушка для важности признаков
        features_importance = {
            "channel_accuracy": 0.35,
            "asset_volatility": 0.25,
            "risk_reward_ratio": 0.20,
            "market_trend": 0.15,
            "time_of_day": 0.05
        }
        
        return SignalPredictionResponse(
            success_probability=success_probability,
            confidence=0.85,  # В реальном проекте это будет метрика доверия к предсказанию
            recommendation=recommendation,
            features_importance=features_importance
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

# Запуск приложения
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 