"""
ML Prediction API endpoints - управление ML-моделью предсказания сигналов
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime

from app.core.database import get_db
from app.services.signal_prediction_service import signal_prediction_service
from app.models.signal import Signal
from app.models.channel import Channel

router = APIRouter()


@router.post("/train", response_model=Dict[str, Any])
async def train_model(db: Session = Depends(get_db)):
    """
    Обучает ML-модель на исторических данных сигналов
    """
    try:
        result = signal_prediction_service.train_model(db)
        
        if result['success']:
            return {
                "status": "success",
                "message": "Модель успешно обучена",
                "data": result
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ошибка обучения модели: {result['error']}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера: {str(e)}"
        )


@router.get("/model-status", response_model=Dict[str, Any])
async def get_model_status():
    """
    Возвращает статус ML-модели
    """
    try:
        status_data = signal_prediction_service.get_model_status()
        return {
            "status": "success",
            "data": status_data
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения статуса модели: {str(e)}"
        )


@router.post("/predict/{signal_id}", response_model=Dict[str, Any])
async def predict_signal_success(signal_id: int, db: Session = Depends(get_db)):
    """
    Предсказывает успешность конкретного сигнала
    """
    try:
        # Получаем сигнал
        signal = db.query(Signal).filter(Signal.id == signal_id).first()
        if not signal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Сигнал с ID {signal_id} не найден"
            )
        
        # Получаем канал
        channel = db.query(Channel).filter(Channel.id == signal.channel_id).first()
        if not channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Канал для сигнала {signal_id} не найден"
            )
        
        # Делаем предсказание
        prediction = signal_prediction_service.predict_signal_success(signal, channel, db)
        
        if prediction['success']:
            return {
                "status": "success",
                "signal_id": signal_id,
                "prediction": prediction
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ошибка предсказания: {prediction['error']}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера: {str(e)}"
        )


@router.post("/batch-predict", response_model=Dict[str, Any])
async def batch_predict_signals(signal_ids: List[int], db: Session = Depends(get_db)):
    """
    Предсказывает успешность для списка сигналов
    """
    try:
        if not signal_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Список ID сигналов не может быть пустым"
            )
        
        if len(signal_ids) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Максимальное количество сигналов для предсказания: 100"
            )
        
        # Получаем сигналы
        signals = db.query(Signal).filter(Signal.id.in_(signal_ids)).all()
        
        if len(signals) != len(signal_ids):
            found_ids = [s.id for s in signals]
            missing_ids = [sid for sid in signal_ids if sid not in found_ids]
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Следующие сигналы не найдены: {missing_ids}"
            )
        
        # Делаем batch предсказание
        predictions = signal_prediction_service.batch_predict(signals, db)
        
        return {
            "status": "success",
            "predictions": predictions,
            "total_signals": len(predictions)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера: {str(e)}"
        )


@router.get("/feature-importance", response_model=Dict[str, Any])
async def get_feature_importance():
    """
    Возвращает важность признаков модели
    """
    try:
        status_data = signal_prediction_service.get_model_status()
        
        if not status_data['is_trained']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Модель не обучена"
            )
        
        # Получаем важность признаков из модели
        if signal_prediction_service.model is not None:
            feature_importance = dict(zip(
                signal_prediction_service.feature_names,
                signal_prediction_service.model.feature_importances_
            ))
            
            # Сортируем по важности
            sorted_features = sorted(
                feature_importance.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            return {
                "status": "success",
                "feature_importance": dict(sorted_features),
                "model_accuracy": status_data['model_accuracy']
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Модель не инициализирована"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения важности признаков: {str(e)}"
        )


@router.post("/save-model", response_model=Dict[str, Any])
async def save_model(filepath: str = "models/signal_prediction_model.pkl"):
    """
    Сохраняет обученную модель в файл
    """
    try:
        if not signal_prediction_service.is_trained:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Модель не обучена"
            )
        
        success = signal_prediction_service.save_model(filepath)
        
        if success:
            return {
                "status": "success",
                "message": f"Модель успешно сохранена в {filepath}",
                "filepath": filepath
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка сохранения модели"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сохранения модели: {str(e)}"
        )


@router.post("/load-model", response_model=Dict[str, Any])
async def load_model(filepath: str = "models/signal_prediction_model.pkl"):
    """
    Загружает модель из файла
    """
    try:
        success = signal_prediction_service.load_model(filepath)
        
        if success:
            return {
                "status": "success",
                "message": f"Модель успешно загружена из {filepath}",
                "filepath": filepath,
                "model_status": signal_prediction_service.get_model_status()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ошибка загрузки модели из {filepath}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка загрузки модели: {str(e)}"
        )


@router.get("/health", response_model=Dict[str, Any])
async def ml_health_check():
    """
    Проверка здоровья ML-сервиса
    """
    try:
        status_data = signal_prediction_service.get_model_status()
        
        return {
            "status": "healthy",
            "service": "ML Signal Prediction Service",
            "model_status": status_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "ML Signal Prediction Service",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        } 