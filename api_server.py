#!/usr/bin/env python3
"""
FastAPI сервер для Crypto Analytics Platform Dashboard
Предоставляет API эндпоинты для получения реальных данных
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import os
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Crypto Analytics Platform API", version="1.0.0")

# Настройка CORS для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Путь к базе данных
DB_PATH = "workers/signals.db"

def get_db_connection():
    """Создает соединение с базой данных"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Ошибка подключения к БД: {e}")
        return None

@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "message": "Crypto Analytics Platform API",
        "version": "1.0.0",
        "status": "active",
        "endpoints": {
            "signals": "/api/signals",
            "channels": "/api/channels", 
            "stats": "/api/stats"
        }
    }

@app.get("/api/signals")
async def get_signals():
    """Получение всех сигналов"""
    try:
        conn = get_db_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Ошибка подключения к БД")
        
        cursor = conn.cursor()
        
        # Получаем все сигналы из базы
        cursor.execute("""
            SELECT * FROM signals 
            ORDER BY timestamp DESC 
            LIMIT 100
        """)
        
        signals = []
        for row in cursor.fetchall():
            signal = dict(row)
            
            # Преобразуем timestamp в ISO формат
            if signal.get('timestamp'):
                try:
                    dt = datetime.fromisoformat(signal['timestamp'].replace('Z', '+00:00'))
                    signal['timestamp'] = dt.isoformat()
                except:
                    signal['timestamp'] = datetime.now().isoformat()
            
            # Убеждаемся, что числовые поля корректны
            for field in ['entry_price', 'target_price', 'stop_loss', 'real_confidence', 'calculated_confidence']:
                if signal.get(field) is None:
                    signal[field] = 0.0
                else:
                    try:
                        signal[field] = float(signal[field])
                    except:
                        signal[field] = 0.0
            
            signals.append(signal)
        
        conn.close()
        
        logger.info(f"Загружено {len(signals)} сигналов")
        return signals
        
    except Exception as e:
        logger.error(f"Ошибка получения сигналов: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения сигналов: {str(e)}")

@app.get("/api/channels")
async def get_channels():
    """Получение статистики каналов"""
    try:
        conn = get_db_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Ошибка подключения к БД")
        
        cursor = conn.cursor()
        
        # Получаем статистику каналов
        cursor.execute("""
            SELECT 
                channel as name,
                COUNT(*) as messages_count,
                SUM(CASE WHEN is_valid = 1 THEN 1 ELSE 0 END) as signals_count,
                AVG(real_confidence) as accuracy
            FROM signals 
            GROUP BY channel
            ORDER BY signals_count DESC
        """)
        
        channels = []
        for row in cursor.fetchall():
            channel = dict(row)
            
            # Убеждаемся, что числовые поля корректны
            channel['messages_count'] = int(channel['messages_count'] or 0)
            channel['signals_count'] = int(channel['signals_count'] or 0)
            channel['accuracy'] = float(channel['accuracy'] or 0.0)
            
            channels.append(channel)
        
        conn.close()
        
        logger.info(f"Загружена статистика {len(channels)} каналов")
        return channels
        
    except Exception as e:
        logger.error(f"Ошибка получения каналов: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения каналов: {str(e)}")

@app.get("/api/stats")
async def get_stats():
    """Получение общей статистики"""
    try:
        conn = get_db_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Ошибка подключения к БД")
        
        cursor = conn.cursor()
        
        # Общая статистика
        cursor.execute("SELECT COUNT(*) as total_signals FROM signals")
        total_signals = cursor.fetchone()['total_signals']
        
        cursor.execute("SELECT COUNT(DISTINCT channel) as total_channels FROM signals")
        total_channels = cursor.fetchone()['total_channels']
        
        cursor.execute("SELECT AVG(real_confidence) as avg_accuracy FROM signals WHERE real_confidence > 0")
        avg_accuracy = cursor.fetchone()['avg_accuracy'] or 0.0
        
        # Сигналы за последний час
        hour_ago = datetime.now() - timedelta(hours=1)
        cursor.execute("""
            SELECT COUNT(*) as recent_signals 
            FROM signals 
            WHERE timestamp > ?
        """, (hour_ago.isoformat(),))
        recent_signals = cursor.fetchone()['recent_signals']
        
        conn.close()
        
        stats = {
            "total_signals": total_signals,
            "total_channels": total_channels,
            "avg_accuracy": round(float(avg_accuracy), 1),
            "recent_signals": recent_signals,
            "last_updated": datetime.now().isoformat()
        }
        
        logger.info(f"Загружена статистика: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики: {str(e)}")

@app.get("/health")
async def health_check():
    """Проверка здоровья сервера"""
    try:
        conn = get_db_connection()
        if conn:
            conn.close()
            db_status = "connected"
        else:
            db_status = "disconnected"
    except:
        db_status = "error"
    
    return {
        "status": "healthy",
        "database": db_status,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    
    # Проверяем существование базы данных
    if not os.path.exists(DB_PATH):
        logger.warning(f"База данных не найдена: {DB_PATH}")
        logger.info("Создайте базу данных, запустив парсеры")
    
    logger.info("Запуск API сервера на http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
