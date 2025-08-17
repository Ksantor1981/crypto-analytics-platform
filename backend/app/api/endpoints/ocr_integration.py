"""
OCR Integration API endpoints
"""
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...services.ocr_service import AdvancedOCRService
from ...schemas.ocr import OCRResponse, OCRStatistics, ImageUploadResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ocr", tags=["OCR Integration"])

@router.post("/extract-signals", response_model=ImageUploadResponse)
async def extract_signals_from_image(
    image: UploadFile = File(...),
    channel_id: int = Form(...),
    message_id: str = Form(None),
    db: Session = Depends(get_db)
):
    """
    Извлечение крипто-сигналов из изображения с помощью OCR
    
    Args:
        image: Загруженное изображение
        channel_id: ID канала
        message_id: ID сообщения (опционально)
        
    Returns:
        Список извлеченных сигналов
    """
    try:
        # Проверяем тип файла
        if not image.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400, 
                detail="Файл должен быть изображением"
            )
        
        # Читаем изображение
        image_data = await image.read()
        
        # Инициализируем OCR сервис
        ocr_service = AdvancedOCRService(db)
        
        # Извлекаем сигналы
        extracted_signals = await ocr_service.extract_signals_from_image(
            image_data=image_data,
            channel_id=channel_id,
            message_id=message_id
        )
        
        # Сохраняем сигналы в базу данных
        saved_signals = await ocr_service.save_extracted_signals(extracted_signals)
        
        return ImageUploadResponse(
            success=True,
            message=f"Извлечено {len(saved_signals)} сигналов из изображения",
            signals_count=len(saved_signals),
            signals=[
                {
                    'id': signal.id,
                    'trading_pair': signal.trading_pair,
                    'direction': signal.direction.value,
                    'entry_price': signal.entry_price,
                    'target_price': signal.target_price,
                    'stop_loss': signal.stop_loss,
                    'confidence': signal.confidence,
                    'source': signal.source
                }
                for signal in saved_signals
            ]
        )
        
    except Exception as e:
        logger.error(f"Ошибка обработки изображения: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка обработки изображения: {str(e)}"
        )

@router.get("/statistics", response_model=OCRStatistics)
async def get_ocr_statistics(db: Session = Depends(get_db)):
    """
    Получение статистики работы OCR
    
    Returns:
        Статистика OCR работы
    """
    try:
        ocr_service = AdvancedOCRService(db)
        stats = await ocr_service.get_ocr_statistics()
        
        return OCRStatistics(**stats)
        
    except Exception as e:
        logger.error(f"Ошибка получения OCR статистики: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка получения статистики: {str(e)}"
        )

@router.post("/test-ocr")
async def test_ocr_capabilities(
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Тестирование возможностей OCR без сохранения сигналов
    
    Args:
        image: Тестовое изображение
        
    Returns:
        Результаты OCR анализа
    """
    try:
        # Проверяем тип файла
        if not image.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400, 
                detail="Файл должен быть изображением"
            )
        
        # Читаем изображение
        image_data = await image.read()
        
        # Инициализируем OCR сервис
        ocr_service = AdvancedOCRService(db)
        
        # Извлекаем сигналы (без сохранения)
        extracted_signals = await ocr_service.extract_signals_from_image(
            image_data=image_data,
            channel_id=0,  # Тестовый канал
            message_id="test"
        )
        
        return {
            "success": True,
            "message": "OCR тест выполнен успешно",
            "signals_found": len(extracted_signals),
            "signals": extracted_signals,
            "ocr_available": ocr_service.reader is not None,
            "nlp_available": ocr_service.nlp is not None
        }
        
    except Exception as e:
        logger.error(f"Ошибка тестирования OCR: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка тестирования OCR: {str(e)}"
        )

@router.get("/health")
async def ocr_health_check(db: Session = Depends(get_db)):
    """
    Проверка состояния OCR сервиса
    
    Returns:
        Статус OCR компонентов
    """
    try:
        ocr_service = AdvancedOCRService(db)
        
        return {
            "status": "healthy",
            "ocr_available": ocr_service.reader is not None,
            "nlp_available": ocr_service.nlp is not None,
            "supported_languages": ocr_service.languages,
            "supported_pairs_count": len(ocr_service.supported_pairs)
        }
        
    except Exception as e:
        logger.error(f"Ошибка проверки здоровья OCR: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "ocr_available": False,
            "nlp_available": False
        }
