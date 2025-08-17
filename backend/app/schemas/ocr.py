"""
OCR API schemas
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

class OCRSignal(BaseModel):
    """Схема извлеченного сигнала"""
    id: Optional[int] = None
    trading_pair: str
    direction: str
    entry_price: float
    target_price: float
    stop_loss: float
    confidence: float
    source: str

class ImageUploadResponse(BaseModel):
    """Ответ на загрузку изображения"""
    success: bool
    message: str
    signals_count: int
    signals: List[OCRSignal]

class OCRStatistics(BaseModel):
    """Статистика OCR работы"""
    total_ocr_signals: int
    channel_statistics: List[Dict[str, Any]]
    ocr_available: bool
    nlp_available: bool
    model_loaded: bool

class OCRResponse(BaseModel):
    """Общий ответ OCR API"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
