#!/usr/bin/env python3
"""
Система сбора метрик производительности
"""

import time
import psutil
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import asyncio
import httpx

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

class PerformanceMetrics:
    """Класс для сбора метрик производительности"""
    
    def __init__(self):
        self.metrics_db = "monitoring/performance_metrics.db"
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных для метрик"""
        try:
            conn = sqlite3.connect(self.metrics_db)
            cursor = conn.cursor()
            
            # Таблица для системных метрик
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    cpu_percent REAL,
                    memory_percent REAL,
                    disk_usage_percent REAL,
                    network_io_bytes INTEGER,
                    active_connections INTEGER
                )
            """)
            
            # Таблица для метрик API
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    response_time REAL,
                    status_code INTEGER,
                    request_count INTEGER
                )
            """)
            
            # Таблица для метрик базы данных
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS db_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    table_name TEXT NOT NULL,
                    row_count INTEGER,
                    size_bytes INTEGER,
                    query_time REAL
                )
            """)
            
            conn.commit()
            conn.close()
            logger.info("База данных метрик инициализирована")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации БД метрик: {e}")
    
    def get_system_metrics(self) -> Dict:
        """Сбор системных метрик"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk
            disk = psutil.disk_usage('/')
            disk_usage_percent = (disk.used / disk.total) * 100
            
            # Network
            network = psutil.net_io_counters()
            network_io_bytes = network.bytes_sent + network.bytes_recv
            
            # Active connections (приблизительно)
            active_connections = len(psutil.net_connections())
            
            return {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'disk_usage_percent': disk_usage_percent,
                'network_io_bytes': network_io_bytes,
                'active_connections': active_connections
            }
        except Exception as e:
            logger.error(f"Ошибка сбора системных метрик: {e}")
            return {}
    
    async def get_api_metrics(self) -> List[Dict]:
        """Сбор метрик API"""
        endpoints = [
            'http://localhost:8000/health',
            'http://localhost:8001/health',
            'http://localhost:8000/api/v1/signals',
            'http://localhost:8001/api/v1/predictions/model-info'
        ]
        
        metrics = []
        
        for endpoint in endpoints:
            try:
                start_time = time.time()
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(endpoint)
                    response_time = time.time() - start_time
                    
                    metrics.append({
                        'timestamp': datetime.now().isoformat(),
                        'endpoint': endpoint,
                        'response_time': response_time,
                        'status_code': response.status_code,
                        'request_count': 1
                    })
            except Exception as e:
                metrics.append({
                    'timestamp': datetime.now().isoformat(),
                    'endpoint': endpoint,
                    'response_time': None,
                    'status_code': None,
                    'request_count': 0,
                    'error': str(e)
                })
        
        return metrics
    
    def get_database_metrics(self) -> List[Dict]:
        """Сбор метрик базы данных"""
        try:
            # Подключаемся к основной БД
            conn = sqlite3.connect('backend/crypto_analytics.db')
            cursor = conn.cursor()
            
            metrics = []
            tables = ['users', 'channels', 'signals', 'subscriptions']
            
            for table in tables:
                try:
                    # Время запроса
                    start_time = time.time()
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    row_count = cursor.fetchone()[0]
                    query_time = time.time() - start_time
                    
                    # Размер таблицы (приблизительно)
                    cursor.execute(f"SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='{table}'")
                    if cursor.fetchone()[0] > 0:
                        size_bytes = row_count * 100  # Приблизительная оценка
                    else:
                        size_bytes = 0
                    
                    metrics.append({
                        'timestamp': datetime.now().isoformat(),
                        'table_name': table,
                        'row_count': row_count,
                        'size_bytes': size_bytes,
                        'query_time': query_time
                    })
                    
                except Exception as e:
                    logger.warning(f"Не удалось получить метрики для таблицы {table}: {e}")
            
            conn.close()
            return metrics
            
        except Exception as e:
            logger.error(f"Ошибка сбора метрик БД: {e}")
            return []
    
    def save_metrics(self, system_metrics: Dict, api_metrics: List[Dict], db_metrics: List[Dict]):
        """Сохранение метрик в базу данных"""
        try:
            conn = sqlite3.connect(self.metrics_db)
            cursor = conn.cursor()
            
            # Сохраняем системные метрики
            if system_metrics:
                cursor.execute("""
                    INSERT INTO system_metrics 
                    (timestamp, cpu_percent, memory_percent, disk_usage_percent, network_io_bytes, active_connections)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    system_metrics['timestamp'],
                    system_metrics.get('cpu_percent'),
                    system_metrics.get('memory_percent'),
                    system_metrics.get('disk_usage_percent'),
                    system_metrics.get('network_io_bytes'),
                    system_metrics.get('active_connections')
                ))
            
            # Сохраняем API метрики
            for metric in api_metrics:
                cursor.execute("""
                    INSERT INTO api_metrics 
                    (timestamp, endpoint, response_time, status_code, request_count)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    metric['timestamp'],
                    metric['endpoint'],
                    metric.get('response_time'),
                    metric.get('status_code'),
                    metric.get('request_count', 1)
                ))
            
            # Сохраняем метрики БД
            for metric in db_metrics:
                cursor.execute("""
                    INSERT INTO db_metrics 
                    (timestamp, table_name, row_count, size_bytes, query_time)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    metric['timestamp'],
                    metric['table_name'],
                    metric['row_count'],
                    metric['size_bytes'],
                    metric['query_time']
                ))
            
            conn.commit()
            conn.close()
            logger.info("Метрики сохранены в базу данных")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения метрик: {e}")
    
    def get_metrics_summary(self, hours: int = 1) -> Dict:
        """Получение сводки метрик за последние N часов"""
        try:
            conn = sqlite3.connect(self.metrics_db)
            cursor = conn.cursor()
            
            # Время N часов назад
            cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            # Системные метрики
            cursor.execute("""
                SELECT 
                    AVG(cpu_percent) as avg_cpu,
                    AVG(memory_percent) as avg_memory,
                    AVG(disk_usage_percent) as avg_disk,
                    MAX(cpu_percent) as max_cpu,
                    MAX(memory_percent) as max_memory
                FROM system_metrics 
                WHERE timestamp > ?
            """, (cutoff_time,))
            
            system_summary = cursor.fetchone()
            
            # API метрики
            cursor.execute("""
                SELECT 
                    endpoint,
                    AVG(response_time) as avg_response_time,
                    COUNT(*) as total_requests,
                    SUM(CASE WHEN status_code = 200 THEN 1 ELSE 0 END) as successful_requests
                FROM api_metrics 
                WHERE timestamp > ?
                GROUP BY endpoint
            """, (cutoff_time,))
            
            api_summary = cursor.fetchall()
            
            # Метрики БД
            cursor.execute("""
                SELECT 
                    table_name,
                    AVG(row_count) as avg_rows,
                    AVG(query_time) as avg_query_time,
                    MAX(row_count) as max_rows
                FROM db_metrics 
                WHERE timestamp > ?
                GROUP BY table_name
            """, (cutoff_time,))
            
            db_summary = cursor.fetchall()
            
            conn.close()
            
            return {
                'period_hours': hours,
                'system': {
                    'avg_cpu_percent': system_summary[0] if system_summary[0] else 0,
                    'avg_memory_percent': system_summary[1] if system_summary[1] else 0,
                    'avg_disk_percent': system_summary[2] if system_summary[2] else 0,
                    'max_cpu_percent': system_summary[3] if system_summary[3] else 0,
                    'max_memory_percent': system_summary[4] if system_summary[4] else 0
                },
                'api': [
                    {
                        'endpoint': row[0],
                        'avg_response_time': row[1] if row[1] else 0,
                        'total_requests': row[2],
                        'success_rate': (row[3] / row[2] * 100) if row[2] > 0 else 0
                    }
                    for row in api_summary
                ],
                'database': [
                    {
                        'table_name': row[0],
                        'avg_rows': row[1] if row[1] else 0,
                        'avg_query_time': row[2] if row[2] else 0,
                        'max_rows': row[3] if row[3] else 0
                    }
                    for row in db_summary
                ]
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения сводки метрик: {e}")
            return {}

async def main():
    """Основная функция сбора метрик"""
    metrics_collector = PerformanceMetrics()
    
    logger.info("📊 Запуск сбора метрик производительности...")
    
    # Собираем метрики
    system_metrics = metrics_collector.get_system_metrics()
    api_metrics = await metrics_collector.get_api_metrics()
    db_metrics = metrics_collector.get_database_metrics()
    
    # Сохраняем метрики
    metrics_collector.save_metrics(system_metrics, api_metrics, db_metrics)
    
    # Получаем сводку
    summary = metrics_collector.get_metrics_summary(hours=1)
    
    # Выводим результаты
    print("\n📊 МЕТРИКИ ПРОИЗВОДИТЕЛЬНОСТИ:")
    print("=" * 50)
    
    if system_metrics:
        print(f"💻 СИСТЕМНЫЕ МЕТРИКИ:")
        print(f"  CPU: {system_metrics.get('cpu_percent', 0):.1f}%")
        print(f"  Память: {system_metrics.get('memory_percent', 0):.1f}%")
        print(f"  Диск: {system_metrics.get('disk_usage_percent', 0):.1f}%")
        print(f"  Сеть: {system_metrics.get('network_io_bytes', 0) / 1024 / 1024:.1f} MB")
        print(f"  Активные соединения: {system_metrics.get('active_connections', 0)}")
    
    if api_metrics:
        print(f"\n🌐 API МЕТРИКИ:")
        for metric in api_metrics:
            endpoint = metric['endpoint'].split('/')[-1]
            status = "✅" if metric.get('status_code') == 200 else "❌"
            response_time = metric.get('response_time', 0)
            print(f"  {status} {endpoint}: {response_time:.3f}с")
    
    if db_metrics:
        print(f"\n🗄️ БАЗА ДАННЫХ:")
        for metric in db_metrics:
            print(f"  📋 {metric['table_name']}: {metric['row_count']} записей")
    
    print("=" * 50)
    
    return summary

if __name__ == "__main__":
    asyncio.run(main())
