"""
API endpoints для пользовательских источников сигналов
Позволяет пользователям добавлять свои источники и автоматически анализирует их качество
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging
import asyncio
import aiohttp
import re
from datetime import datetime, timezone, timedelta

from ...core.database import get_db
from ...core.auth import get_current_active_user, require_admin
from ...models.channel import Channel
from ...models.user import User
from ...models.signal import Signal
from ...models.performance_metric import PerformanceMetric
try:
    from .telegram_integration import get_coingecko_price, analyze_channel_metrics
except ImportError:
    get_coingecko_price = None
    analyze_channel_metrics = None

router = APIRouter(tags=["User Sources"])
logger = logging.getLogger(__name__)

@router.post("/init-db")
async def init_db(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Инициализация таблиц базы данных"""
    try:
        from ...models.base import Base
        from ...core.database import engine
        
        # Пересоздаем таблицы
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        
        return {
            "success": True,
            "message": "База данных пересоздана",
            "tables_created": True
        }
        
    except Exception as e:
        logger.error(f"Ошибка инициализации БД: {e}")
        return {
            "success": False,
            "message": f"Ошибка: {str(e)}"
        }

@router.post("/add-source")
async def add_user_source(
    source_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Добавляет пользовательский источник сигналов и запускает его анализ
    
    source_data:
    {
        "platform": "telegram",  # telegram, discord, twitter, reddit, website
        "source_url": "https://t.me/crypto_signals_pro",
        "name": "Crypto Signals Pro",
        "description": "Professional crypto trading signals",
        "expected_accuracy": "high"  # high, medium, low, unknown
    }
    """
    try:
        logger.info(f"🔍 ДОБАВЛЕНИЕ ПОЛЬЗОВАТЕЛЬСКОГО ИСТОЧНИКА: {source_data.get('name')}")
        
        # Валидация входных данных
        required_fields = ["platform", "source_url", "name"]
        for field in required_fields:
            if field not in source_data:
                raise HTTPException(status_code=400, detail=f"Поле '{field}' обязательно")
        
        # Извлекаем username из URL
        username = extract_username_from_url(source_data["source_url"], source_data["platform"])
        if not username:
            raise HTTPException(status_code=400, detail="Не удалось извлечь username из URL")
        
        # Проверяем, не существует ли уже такой источник
        existing_channel = db.query(Channel).filter(Channel.username == username).first()
        if existing_channel:
            return {
                "success": False,
                "message": f"Источник {username} уже существует в системе",
                "existing_channel_id": existing_channel.id,
                "status": "duplicate"
            }
        
        # Создаем новый канал
        new_channel = Channel(
            owner_id=current_user.id,
            username=username,
            name=source_data["name"],
            description=source_data.get("description", ""),
            platform=source_data["platform"],
            is_active=True,
            is_verified=False,  # Будет проверен автоматически
            expected_accuracy=source_data.get("expected_accuracy", "unknown"),
            status="analyzing"  # Новый статус - анализируется
        )
        
        db.add(new_channel)
        db.flush()  # Получаем ID для анализа
        
        # Запускаем автоматический анализ источника
        analysis_result = await analyze_user_source(
            new_channel.id, 
            source_data["platform"], 
            source_data["source_url"], 
            db
        )
        
        # Обновляем статус канала на основе анализа
        new_channel.status = "active" if analysis_result["is_quality"] else "low_quality"
        new_channel.is_verified = analysis_result["is_quality"]
        new_channel.subscribers_count = analysis_result.get("subscribers_count")
        new_channel.category = analysis_result.get("category", "user_added")
        
        # Устанавливаем приоритет на основе качества
        if analysis_result["quality_score"] >= 0.8:
            new_channel.priority = 5  # Высокий приоритет
        elif analysis_result["quality_score"] >= 0.6:
            new_channel.priority = 3  # Средний приоритет
        else:
            new_channel.priority = 1  # Низкий приоритет
        
        db.commit()
        
        logger.info(f"✅ Пользовательский источник добавлен: {new_channel.id}")
        
        return {
            "success": True,
            "message": f"Источник '{new_channel.name}' успешно добавлен и проанализирован",
            "channel_id": new_channel.id,
            "analysis": analysis_result,
            "status": "added",
            "recommendation": get_quality_recommendation(analysis_result)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка добавления источника: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка добавления источника: {str(e)}")

async def analyze_user_source(channel_id: int, platform: str, source_url: str, db: Session) -> Dict[str, Any]:
    """
    Автоматически анализирует качество пользовательского источника
    """
    try:
        logger.info(f"🔍 АНАЛИЗ ИСТОЧНИКА: {source_url}")
        
        analysis_result = {
            "quality_score": 0.0,
            "is_quality": False,
            "signals_found": 0,
            "structured_signals": 0,
            "subscribers_count": 0,
            "activity_level": "unknown",
            "category": "user_added",
            "strengths": [],
            "weaknesses": [],
            "recommendation": ""
        }
        
        if platform == "telegram":
            analysis_result = await analyze_telegram_source(source_url, db)
        elif platform == "discord":
            analysis_result = await analyze_discord_source(source_url, db)
        elif platform == "reddit":
            analysis_result = await analyze_reddit_source(source_url, db)
        elif platform == "twitter":
            analysis_result = await analyze_twitter_source(source_url, db)
        else:
            analysis_result = await analyze_generic_source(source_url, db)
        
        # Сохраняем результаты анализа
        await save_analysis_results(channel_id, analysis_result, db)
        
        return analysis_result
        
    except Exception as e:
        logger.error(f"❌ Ошибка анализа источника: {e}")
        return {
            "quality_score": 0.0,
            "is_quality": False,
            "error": str(e),
            "signals_found": 0,
            "structured_signals": 0
        }

async def analyze_telegram_source(source_url: str, db: Session) -> Dict[str, Any]:
    """
    Анализирует качество Telegram канала
    """
    try:
        # Извлекаем username из URL
        username = source_url.split('/')[-1].replace('@', '')
        
        # Используем существующую логику анализа каналов
        web_url = f"https://t.me/s/{username}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(web_url, timeout=10) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Используем существующую функцию анализа
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Анализируем канал с помощью существующей функции
                    metrics = await analyze_channel_metrics(soup, username)
                    
                    # Дополнительный анализ качества сигналов
                    signals_analysis = await analyze_signals_quality(soup, username)
                    
                    # Объединяем результаты
                    quality_score = calculate_quality_score(metrics, signals_analysis)
                    
                    return {
                        "quality_score": quality_score,
                        "is_quality": quality_score >= 0.6,
                        "signals_found": signals_analysis["total_signals"],
                        "structured_signals": signals_analysis["structured_signals"],
                        "subscribers_count": metrics.get("subscribers_count", 0),
                        "activity_level": metrics.get("activity_level", "unknown"),
                        "category": "telegram",
                        "strengths": get_strengths(metrics, signals_analysis),
                        "weaknesses": get_weaknesses(metrics, signals_analysis),
                        "detailed_metrics": metrics,
                        "signals_analysis": signals_analysis
                    }
                else:
                    return {
                        "quality_score": 0.0,
                        "is_quality": False,
                        "error": f"Не удалось получить доступ к каналу: {response.status}",
                        "signals_found": 0,
                        "structured_signals": 0
                    }
                    
    except Exception as e:
        logger.error(f"❌ Ошибка анализа Telegram: {e}")
        return {
            "quality_score": 0.0,
            "is_quality": False,
            "error": str(e),
            "signals_found": 0,
            "structured_signals": 0
        }

async def analyze_signals_quality(soup, channel_name: str) -> Dict[str, Any]:
    """
    Анализирует качество сигналов в канале
    """
    try:
        messages = soup.find_all('div', class_='tgme_widget_message_text')
        
        total_signals = 0
        structured_signals = 0
        price_mentions = 0
        trading_terms = 0
        
        # Паттерны для поиска торговых сигналов
        signal_patterns = [
            r'\b(ENTRY|ВХОД)[:\s]*\$?[\d,]+\.?\d*',
            r'\b(TARGET|TP|ЦЕЛЬ)[:\s]*\$?[\d,]+\.?\d*', 
            r'\b(STOP|SL|СТОП)[:\s]*\$?[\d,]+\.?\d*',
            r'\b(BUY|LONG|SHORT|SELL)\b',
            r'\b(BTC|ETH|SOL|ADA|DOGE)\b.*\$[\d,]+',
        ]
        
        # Термины качественных сигналов
        quality_terms = [
            'ANALYSIS', 'TECHNICAL', 'SUPPORT', 'RESISTANCE', 'FIBONACCI',
            'RSI', 'MACD', 'VOLUME', 'BREAKOUT', 'PATTERN'
        ]
        
        # Плохие индикаторы
        bad_indicators = [
            'MOON', 'ROCKET', '🚀', 'PUMP', 'LAMBO', 'TO THE MOON',
            'EASY MONEY', 'GET RICH', 'GUARANTEED'
        ]
        
        for message in messages[:50]:  # Анализируем последние 50 сообщений
            text = message.get_text().upper()
            
            # Проверяем на наличие сигналов
            signal_found = False
            for pattern in signal_patterns:
                if re.search(pattern, text):
                    signal_found = True
                    break
                    
            if signal_found:
                total_signals += 1
                
                # Проверяем структурированность
                has_entry = bool(re.search(r'\b(ENTRY|ВХОД)', text))
                has_target = bool(re.search(r'\b(TARGET|TP|ЦЕЛЬ)', text))
                has_stop = bool(re.search(r'\b(STOP|SL|СТОП)', text))
                
                if (has_entry and has_target) or (has_entry and has_stop):
                    structured_signals += 1
                    
            # Подсчитываем качественные индикаторы
            for term in quality_terms:
                if term in text:
                    trading_terms += 1
                    
            # Подсчитываем ценовые упоминания
            if re.search(r'\$[\d,]+', text):
                price_mentions += 1
        
        # Рассчитываем метрики качества
        structure_ratio = structured_signals / max(total_signals, 1)
        quality_terms_ratio = trading_terms / max(len(messages), 1)
        
        return {
            "total_signals": total_signals,
            "structured_signals": structured_signals,
            "structure_ratio": structure_ratio,
            "price_mentions": price_mentions,
            "trading_terms": trading_terms,
            "quality_terms_ratio": quality_terms_ratio,
            "messages_analyzed": len(messages)
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка анализа сигналов: {e}")
        return {
            "total_signals": 0,
            "structured_signals": 0,
            "structure_ratio": 0,
            "price_mentions": 0,
            "trading_terms": 0,
            "quality_terms_ratio": 0
        }

def calculate_quality_score(metrics: Dict, signals_analysis: Dict) -> float:
    """
    Рассчитывает общий балл качества источника (0.0 - 1.0)
    """
    try:
        score = 0.0
        
        # 1. Количество подписчиков (макс 0.2)
        subscribers = metrics.get("subscribers_count", 0)
        if subscribers >= 10000:
            score += 0.2
        elif subscribers >= 1000:
            score += 0.15
        elif subscribers >= 100:
            score += 0.1
        
        # 2. Активность канала (макс 0.2)
        activity = metrics.get("activity_level", "low")
        if activity == "high":
            score += 0.2
        elif activity == "medium":
            score += 0.15
        elif activity == "low":
            score += 0.1
        
        # 3. Качество сигналов (макс 0.3)
        structure_ratio = signals_analysis.get("structure_ratio", 0)
        score += min(structure_ratio * 0.3, 0.3)
        
        # 4. Количество сигналов (макс 0.15)
        total_signals = signals_analysis.get("total_signals", 0)
        if total_signals >= 10:
            score += 0.15
        elif total_signals >= 5:
            score += 0.1
        elif total_signals >= 1:
            score += 0.05
        
        # 5. Использование технических терминов (макс 0.15)
        quality_terms_ratio = signals_analysis.get("quality_terms_ratio", 0)
        score += min(quality_terms_ratio * 0.15, 0.15)
        
        return min(score, 1.0)
        
    except Exception as e:
        logger.error(f"❌ Ошибка расчета качества: {e}")
        return 0.0

def get_strengths(metrics: Dict, signals_analysis: Dict) -> List[str]:
    """Определяет сильные стороны источника"""
    strengths = []
    
    if metrics.get("subscribers_count", 0) >= 1000:
        strengths.append(f"Большая аудитория ({metrics['subscribers_count']} подписчиков)")
    
    if signals_analysis.get("structure_ratio", 0) >= 0.7:
        strengths.append("Высокое качество структурированных сигналов")
    
    if signals_analysis.get("total_signals", 0) >= 10:
        strengths.append("Активно публикует торговые сигналы")
    
    if signals_analysis.get("quality_terms_ratio", 0) >= 0.1:
        strengths.append("Использует технический анализ")
    
    if metrics.get("activity_level") == "high":
        strengths.append("Высокая активность канала")
    
    return strengths

def get_weaknesses(metrics: Dict, signals_analysis: Dict) -> List[str]:
    """Определяет слабые стороны источника"""
    weaknesses = []
    
    if metrics.get("subscribers_count", 0) < 100:
        weaknesses.append("Малая аудитория")
    
    if signals_analysis.get("structure_ratio", 0) < 0.3:
        weaknesses.append("Неструктурированные сигналы")
    
    if signals_analysis.get("total_signals", 0) < 3:
        weaknesses.append("Мало торговых сигналов")
    
    if signals_analysis.get("quality_terms_ratio", 0) < 0.05:
        weaknesses.append("Отсутствие технического анализа")
    
    if metrics.get("activity_level") == "low":
        weaknesses.append("Низкая активность")
    
    return weaknesses

def get_quality_recommendation(analysis_result: Dict) -> str:
    """Дает рекомендацию по использованию источника"""
    score = analysis_result.get("quality_score", 0)
    
    if score >= 0.8:
        return "🟢 ОТЛИЧНЫЙ источник! Рекомендуется для постоянного мониторинга с высоким приоритетом."
    elif score >= 0.6:
        return "🟡 ХОРОШИЙ источник. Можно использовать с осторожностью и проверкой сигналов."
    elif score >= 0.4:
        return "🟠 СРЕДНИЙ источник. Требует дополнительной проверки и низкий приоритет."
    else:
        return "🔴 СЛАБЫЙ источник. НЕ рекомендуется для торговли, только для справки."

async def analyze_discord_source(source_url: str, db: Session) -> Dict[str, Any]:
    """Анализ Discord сервера (заглушка)"""
    return {
        "quality_score": 0.5,
        "is_quality": True,
        "signals_found": 5,
        "structured_signals": 3,
        "category": "discord",
        "note": "Discord анализ в разработке"
    }

async def analyze_reddit_source(source_url: str, db: Session) -> Dict[str, Any]:
    """Анализ Reddit источника (заглушка)"""
    return {
        "quality_score": 0.6,
        "is_quality": True,
        "signals_found": 8,
        "structured_signals": 4,
        "category": "reddit",
        "note": "Reddit анализ в разработке"
    }

async def analyze_twitter_source(source_url: str, db: Session) -> Dict[str, Any]:
    """Анализ Twitter аккаунта (заглушка)"""
    return {
        "quality_score": 0.7,
        "is_quality": True,
        "signals_found": 12,
        "structured_signals": 6,
        "category": "twitter",
        "note": "Twitter анализ в разработке"
    }

async def analyze_generic_source(source_url: str, db: Session) -> Dict[str, Any]:
    """Анализ веб-сайта или другого источника (заглушка)"""
    return {
        "quality_score": 0.4,
        "is_quality": False,
        "signals_found": 2,
        "structured_signals": 1,
        "category": "website",
        "note": "Веб-сайт анализ в разработке"
    }

async def save_analysis_results(channel_id: int, analysis_result: Dict, db: Session):
    """Сохраняет результаты анализа в базу данных"""
    try:
        # Создаем запись в PerformanceMetric
        performance_metric = PerformanceMetric(
            channel_id=channel_id,
            total_signals=analysis_result.get("signals_found", 0),
            successful_signals=analysis_result.get("structured_signals", 0),
            win_rate=analysis_result.get("structure_ratio", 0) * 100,
            total_return=0.0,  # Будет рассчитано позже
            max_drawdown=0.0,
            sharpe_ratio=0.0,
            quality_score=analysis_result.get("quality_score", 0),
            analysis_data=str(analysis_result),  # JSON как строка
            period_start=datetime.now(timezone.utc) - timedelta(days=30),
            period_end=datetime.now(timezone.utc)
        )
        
        db.add(performance_metric)
        db.commit()
        logger.info(f"✅ Результаты анализа сохранены для канала {channel_id}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения анализа: {e}")

def extract_username_from_url(url: str, platform: str) -> Optional[str]:
    """Извлекает username из URL различных платформ"""
    try:
        if platform == "telegram":
            # https://t.me/channel_name или @channel_name
            if 't.me/' in url:
                return url.split('/')[-1]
            elif url.startswith('@'):
                return url[1:]
            else:
                return url
                
        elif platform == "discord":
            # https://discord.gg/server_id
            if 'discord.gg/' in url:
                return url.split('/')[-1]
                
        elif platform == "reddit":
            # https://reddit.com/r/subreddit
            if '/r/' in url:
                return url.split('/r/')[-1].split('/')[0]
                
        elif platform == "twitter":
            # https://twitter.com/username
            if 'twitter.com/' in url or 'x.com/' in url:
                return url.split('/')[-1]
                
        return url.split('/')[-1]  # Fallback
        
    except Exception as e:
        logger.error(f"❌ Ошибка извлечения username: {e}")
        return None

@router.get("/my-sources")
async def get_user_sources(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Получает список источников пользователя"""
    try:
        channels = db.query(Channel).filter(Channel.owner_id == current_user.id).all()
        
        sources_data = []
        for channel in channels:
            # Получаем последние метрики
            latest_metric = db.query(PerformanceMetric).filter(
                PerformanceMetric.channel_id == channel.id
            ).order_by(PerformanceMetric.created_at.desc()).first()
            
            sources_data.append({
                "id": channel.id,
                "name": channel.name,
                "username": channel.username,
                "platform": channel.platform,
                "status": channel.status,
                "is_verified": channel.is_verified,
                "priority": channel.priority,
                "subscribers_count": channel.subscribers_count,
                "category": channel.category,
                "quality_score": latest_metric.quality_score if latest_metric else 0,
                "total_signals": latest_metric.total_signals if latest_metric else 0,
                "win_rate": latest_metric.win_rate if latest_metric else 0,
                "created_at": channel.created_at,
                "updated_at": channel.updated_at
            })
        
        return {
            "success": True,
            "sources": sources_data,
            "total_count": len(sources_data)
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения источников: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reanalyze/{channel_id}")
async def reanalyze_source(
    channel_id: int,
    db: Session = Depends(get_db)
):
    """Повторно анализирует источник"""
    try:
        channel = db.query(Channel).filter(Channel.id == channel_id).first()
        if not channel:
            raise HTTPException(status_code=404, detail="Источник не найден")
        
        # Строим URL для анализа
        if channel.platform == "telegram":
            source_url = f"https://t.me/{channel.username}"
        else:
            source_url = channel.username  # Fallback
            
        # Запускаем повторный анализ
        analysis_result = await analyze_user_source(
            channel_id, 
            channel.platform, 
            source_url, 
            db
        )
        
        # Обновляем статус
        channel.status = "active" if analysis_result["is_quality"] else "low_quality"
        channel.is_verified = analysis_result["is_quality"]
        channel.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Источник '{channel.name}' повторно проанализирован",
            "analysis": analysis_result,
            "recommendation": get_quality_recommendation(analysis_result)
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка повторного анализа: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/remove/{channel_id}")
async def remove_user_source(
    channel_id: int,
    db: Session = Depends(get_db)
):
    """Удаляет пользовательский источник"""
    try:
        channel = db.query(Channel).filter(Channel.id == channel_id).first()
        if not channel:
            raise HTTPException(status_code=404, detail="Источник не найден")
        
        channel_name = channel.name
        db.delete(channel)
        db.commit()
        
        return {
            "success": True,
            "message": f"Источник '{channel_name}' удален"
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка удаления источника: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
