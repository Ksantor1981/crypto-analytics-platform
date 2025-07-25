from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ...core.database import get_db
from ...services.signal_prediction_service import SignalPredictionService
from ...schemas.ml_schemas import PredictionRequest, PredictionResponse, BatchPredictionRequest, BatchPredictionResponse, ModelStatusResponse, TrainResponse

router = APIRouter()

@router.post("/train", response_model=TrainResponse)
def train_model(db: Session = Depends(get_db)):
    """Запускает обучение ML-модели на всех доступных данных SignalResult."""
    service = SignalPredictionService(db)
    try:
        result = service.train_model()
        return {"status": "success", "message": "Model training completed successfully.", "details": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model training failed: {str(e)}")

@router.get("/model-status", response_model=ModelStatusResponse)
def get_model_status(db: Session = Depends(get_db)):
    """Возвращает статус текущей ML-модели."""
    service = SignalPredictionService(db)
    status = service.get_model_status()
    return status

@router.post("/predict", response_model=PredictionResponse)
def predict_signal_success(request: PredictionRequest, db: Session = Depends(get_db)):
    """Предсказывает вероятность успеха для одного сигнала."""
    service = SignalPredictionService(db)
    try:
        prediction = service.predict(request.signal_id)
        return {"signal_id": request.signal_id, "prediction": prediction}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@router.post("/batch-predict", response_model=BatchPredictionResponse)
def batch_predict_signal_success(request: BatchPredictionRequest, db: Session = Depends(get_db)):
    """Предсказывает вероятность успеха для списка сигналов."""
    service = SignalPredictionService(db)
    try:
        predictions = service.batch_predict(request.signal_ids)
        return {"predictions": predictions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")
