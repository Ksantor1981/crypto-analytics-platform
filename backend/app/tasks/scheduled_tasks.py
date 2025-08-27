"""
Автоматические задачи для ежечасного обновления сигналов и статистики
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any
import aiohttp
from sqlalchemy.orm import Session
from celery import current_app

from app.core.database import get_db
from app.celery_app import celery_app
from app.models.signal import Signal
from app.api.endpoints.telegram_integration import (
    collect_from_all_sources, 
    parse_6month_real_history,
    analyze_channel_quality
)

logger = logging.getLogger(__name__)

@celery_app.task(name='collect_all_signals_hourly')
def collect_all_signals_hourly():
    """
    🚀 ЕЖЕЧАСНЫЙ СБОР СИГНАЛОВ ИЗ ВСЕХ ИСТОЧНИКОВ
    """
    try:
        logger.info("🚀 ЗАПУСК ЕЖЕЧАСНОГО СБОРА СИГНАЛОВ...")
        
        # Получаем сессию БД
        db = next(get_db())
        
        # Запускаем асинхронный сбор
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(collect_from_all_sources(db))
            logger.info(f"✅ Сбор завершен: {result}")
            return {
                "success": True,
                "message": "Ежечасный сбор сигналов выполнен",
                "timestamp": datetime.utcnow().isoformat(),
                "result": result
            }
        finally:
            loop.close()
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Ошибка ежечасного сбора: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@celery_app.task(name='recalculate_statistics_hourly')
def recalculate_statistics_hourly():
    """
    📊 ЕЖЕЧАСНЫЙ ПЕРЕСЧЕТ СТАТИСТИКИ КАНАЛОВ
    """
    try:
        logger.info("📊 ЗАПУСК ПЕРЕСЧЕТА СТАТИСТИКИ...")
        
        # Получаем сессию БД
        db = next(get_db())
        
        try:
            # Пересчитываем статистику за последний час
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            
            # Получаем сигналы за последний час
            recent_signals = db.query(Signal).filter(
                Signal.created_at >= one_hour_ago
            ).all()
            
            # Группируем по каналам
            channel_stats = {}
            for signal in recent_signals:
                channel_id = signal.channel_id
                if channel_id not in channel_stats:
                    channel_stats[channel_id] = {
                        'total_signals': 0,
                        'pending_signals': 0,
                        'completed_signals': 0,
                        'successful_signals': 0,
                        'last_signal_time': None
                    }
                
                stats = channel_stats[channel_id]
                stats['total_signals'] += 1
                
                if signal.status == 'PENDING':
                    stats['pending_signals'] += 1
                elif signal.status in ['TP1_HIT', 'TP2_HIT', 'TP3_HIT']:
                    stats['completed_signals'] += 1
                    stats['successful_signals'] += 1
                elif signal.status in ['SL_HIT', 'EXPIRED', 'CANCELLED']:
                    stats['completed_signals'] += 1
                
                if not stats['last_signal_time'] or signal.created_at > stats['last_signal_time']:
                    stats['last_signal_time'] = signal.created_at
            
            # Рассчитываем винрейты
            for channel_id, stats in channel_stats.items():
                if stats['completed_signals'] > 0:
                    stats['win_rate'] = (stats['successful_signals'] / stats['completed_signals']) * 100
                else:
                    stats['win_rate'] = 0
            
            logger.info(f"✅ Статистика обновлена для {len(channel_stats)} каналов")
            
            return {
                "success": True,
                "message": f"Статистика пересчитана для {len(channel_stats)} каналов",
                "channel_stats": channel_stats,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Ошибка пересчета статистики: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@celery_app.task(name='analyze_channels_quality_hourly')
def analyze_channels_quality_hourly():
    """
    🔍 ЕЖЕЧАСНЫЙ АНАЛИЗ КАЧЕСТВА КАНАЛОВ
    """
    try:
        logger.info("🔍 ЗАПУСК АНАЛИЗА КАЧЕСТВА КАНАЛОВ...")
        
        # Получаем сессию БД
        db = next(get_db())
        
        # Запускаем асинхронный анализ
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(analyze_channel_quality(db))
            logger.info(f"✅ Анализ завершен: {result.get('message', 'OK')}")
            return {
                "success": True,
                "message": "Анализ качества каналов выполнен",
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        finally:
            loop.close()
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Ошибка анализа каналов: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@celery_app.task(name='deep_historical_analysis')
def deep_historical_analysis():
    """
    📈 ГЛУБОКИЙ АНАЛИЗ ИСТОРИЧЕСКИХ ДАННЫХ (каждые 6 часов)
    """
    try:
        logger.info("📈 ЗАПУСК ГЛУБОКОГО ИСТОРИЧЕСКОГО АНАЛИЗА...")
        
        # Получаем сессию БД
        db = next(get_db())
        
        # Запускаем анализ
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(parse_6month_real_history(db))
            logger.info(f"✅ Исторический анализ завершен: {result.get('message', 'OK')}")
            return {
                "success": True,
                "message": "Глубокий исторический анализ выполнен",
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        finally:
            loop.close()
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Ошибка исторического анализа: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@celery_app.task(name='update_channel_ratings_daily')  
def update_channel_ratings_daily():
    """
    ⭐ ЕЖЕДНЕВНОЕ ОБНОВЛЕНИЕ РЕЙТИНГОВ КАНАЛОВ
    """
    try:
        logger.info("⭐ ЗАПУСК ОБНОВЛЕНИЯ РЕЙТИНГОВ...")
        
        # Получаем сессию БД
        db = next(get_db())
        
        try:
            # Анализируем данные за последние 30 дней
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            
            # Получаем все сигналы за 30 дней
            signals = db.query(Signal).filter(
                Signal.created_at >= thirty_days_ago
            ).all()
            
            # Группируем по каналам и считаем рейтинги
            channel_ratings = {}
            for signal in signals:
                channel_id = signal.channel_id
                if channel_id not in channel_ratings:
                    channel_ratings[channel_id] = {
                        'total_signals': 0,
                        'successful': 0,
                        'failed': 0,
                        'pending': 0,
                        'avg_confidence': 0,
                        'total_confidence': 0
                    }
                
                rating = channel_ratings[channel_id]
                rating['total_signals'] += 1
                rating['total_confidence'] += float(signal.confidence_score or 0)
                
                if signal.status in ['TP1_HIT', 'TP2_HIT', 'TP3_HIT']:
                    rating['successful'] += 1
                elif signal.status in ['SL_HIT', 'EXPIRED', 'CANCELLED']:
                    rating['failed'] += 1
                else:
                    rating['pending'] += 1
            
            # Рассчитываем финальные рейтинги
            for channel_id, rating in channel_ratings.items():
                if rating['total_signals'] > 0:
                    rating['win_rate'] = (rating['successful'] / (rating['successful'] + rating['failed'])) * 100 if (rating['successful'] + rating['failed']) > 0 else 0
                    rating['avg_confidence'] = rating['total_confidence'] / rating['total_signals']
                    
                    # Комплексный рейтинг (винрейт * уверенность * активность)
                    activity_score = min(rating['total_signals'] / 10, 1.0)  # Максимум 1.0 при 10+ сигналов
                    rating['composite_score'] = (rating['win_rate'] / 100) * rating['avg_confidence'] * activity_score
                else:
                    rating['win_rate'] = 0
                    rating['avg_confidence'] = 0
                    rating['composite_score'] = 0
            
            logger.info(f"✅ Рейтинги обновлены для {len(channel_ratings)} каналов")
            
            return {
                "success": True,
                "message": f"Рейтинги обновлены для {len(channel_ratings)} каналов",
                "ratings": channel_ratings,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Ошибка обновления рейтингов: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@celery_app.task(name='cleanup_old_signals')
def cleanup_old_signals():
    """
    🗑️ ЕЖЕДНЕВНАЯ ОЧИСТКА СТАРЫХ СИГНАЛОВ
    """
    try:
        logger.info("🗑️ ЗАПУСК ОЧИСТКИ СТАРЫХ СИГНАЛОВ...")
        
        # Получаем сессию БД
        db = next(get_db())
        
        try:
            # Удаляем сигналы старше 90 дней
            ninety_days_ago = datetime.utcnow() - timedelta(days=90)
            
            # Считаем количество для удаления
            old_signals_count = db.query(Signal).filter(
                Signal.created_at < ninety_days_ago
            ).count()
            
            # Удаляем старые сигналы
            deleted = db.query(Signal).filter(
                Signal.created_at < ninety_days_ago
            ).delete()
            
            db.commit()
            
            logger.info(f"✅ Удалено {deleted} старых сигналов")
            
            return {
                "success": True,
                "message": f"Удалено {deleted} сигналов старше 90 дней",
                "deleted_count": deleted,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Ошибка очистки: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# Мониторинг состояния задач
@celery_app.task(name='system_health_check')
def system_health_check():
    """
    🩺 ПРОВЕРКА СОСТОЯНИЯ СИСТЕМЫ
    """
    try:
        logger.info("🩺 ПРОВЕРКА СОСТОЯНИЯ СИСТЕМЫ...")
        
        health_status = {
            "timestamp": datetime.utcnow().isoformat(),
            "celery_status": "healthy",
            "database_status": "unknown",
            "signal_collection_status": "unknown",
            "last_signals_count": 0
        }
        
        # Проверяем БД
        try:
            db = next(get_db())
            recent_signals = db.query(Signal).filter(
                Signal.created_at >= datetime.utcnow() - timedelta(hours=1)
            ).count()
            
            health_status["database_status"] = "healthy"
            health_status["last_signals_count"] = recent_signals
            
            if recent_signals > 0:
                health_status["signal_collection_status"] = "active"
            else:
                health_status["signal_collection_status"] = "inactive"
                
            db.close()
            
        except Exception as e:
            health_status["database_status"] = f"error: {str(e)}"
        
        logger.info(f"✅ Проверка завершена: {health_status}")
        return health_status
        
    except Exception as e:
        logger.error(f"❌ Ошибка проверки системы: {e}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "celery_status": "error",
            "error": str(e)
        }
