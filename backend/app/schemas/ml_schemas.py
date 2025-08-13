from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class TrainResponse(BaseModel):
    status: str
    message: str
    details: Dict[str, Any]

class ModelStatusResponse(BaseModel):
    model_trained: bool
    last_trained: Optional[datetime] = None
    model_version: Optional[str] = None
    training_accuracy: Optional[float] = None
    
    # Add model config to resolve namespace conflicts
    model_config = {
        "protected_namespaces": ()
    }

class PredictionRequest(BaseModel):
    signal_id: int

class PredictionResponse(BaseModel):
    signal_id: int
    prediction: float = Field(..., ge=0, le=1, description="Вероятность успеха сигнала от 0.0 до 1.0")

class BatchPredictionRequest(BaseModel):
    signal_ids: List[int]

class BatchPredictionResponse(BaseModel):
    predictions: List[PredictionResponse]
