#!/usr/bin/env python3
"""
Система оптимизации производительности
"""

import asyncio
import time
import psutil
import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Optional
import httpx
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceOptimizer:
    def __init__(self):
        self.optimization_db = "optimization/performance_optimization.db"
        self.init_database()
        
    def init_database(self):
        try:
            os.makedirs("optimization", exist_ok=True)
            conn = sqlite3.connect(self.optimization_db)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS optimization_recommendations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    category TEXT NOT NULL,
                    recommendation TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    impact_score REAL,
                    implemented BOOLEAN DEFAULT FALSE
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auto_optimizations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    optimization_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    improvement_percent REAL
                )
            """)
            
            conn.commit()
            conn.close()
            logger.info("База данных оптимизации инициализирована")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации БД: {e}")
    
    async def analyze_performance(self) -> Dict:
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            analysis = {
                'timestamp': datetime.now().isoformat(),
                'system': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'disk_percent': (disk.used / disk.total) * 100
                },
                'recommendations': []
            }
            
            # Генерируем рекомендации
            if cpu_percent > 80:
                analysis['recommendations'].append({
                    'category': 'system',
                    'recommendation': 'Высокое использование CPU. Рассмотрите оптимизацию.',
                    'priority': 'high',
                    'impact_score': 0.9
                })
            
            if memory.percent > 85:
                analysis['recommendations'].append({
                    'category': 'system',
                    'recommendation': 'Высокое использование памяти. Проверьте утечки.',
                    'priority': 'high',
                    'impact_score': 0.8
                })
            
            return analysis
            
        except Exception as e:
            logger.error(f"Ошибка анализа: {e}")
            return {}
    
    async def apply_optimizations(self) -> List[Dict]:
        optimizations = []
        
        try:
            # Очистка временных файлов
            temp_cleanup = await self.cleanup_temp_files()
            if temp_cleanup:
                optimizations.append(temp_cleanup)
            
            # Очистка логов
            log_cleanup = await self.cleanup_logs()
            if log_cleanup:
                optimizations.append(log_cleanup)
            
            self.save_optimizations(optimizations)
            return optimizations
            
        except Exception as e:
            logger.error(f"Ошибка оптимизации: {e}")
            return []
    
    async def cleanup_temp_files(self) -> Optional[Dict]:
        try:
            files_removed = 0
            temp_dirs = ['./temp', './logs']
            
            for temp_dir in temp_dirs:
                if os.path.exists(temp_dir):
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            if os.path.exists(file_path):
                                file_age = time.time() - os.path.getmtime(file_path)
                                if file_age > 7 * 24 * 3600:  # 7 дней
                                    try:
                                        os.remove(file_path)
                                        files_removed += 1
                                    except:
                                        pass
            
            if files_removed > 0:
                return {
                    'type': 'temp_cleanup',
                    'description': f'Удалено {files_removed} старых файлов',
                    'improvement_percent': 100.0
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка очистки: {e}")
            return None
    
    async def cleanup_logs(self) -> Optional[Dict]:
        try:
            log_files = [
                'monitoring/monitoring.log',
                'backend/logs/app.log'
            ]
            
            files_cleaned = 0
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    file_size = os.path.getsize(log_file)
                    if file_size > 10 * 1024 * 1024:  # 10MB
                        try:
                            with open(log_file, 'w') as f:
                                f.write('')
                            files_cleaned += 1
                        except:
                            pass
            
            if files_cleaned > 0:
                return {
                    'type': 'log_cleanup',
                    'description': f'Очищено {files_cleaned} лог файлов',
                    'improvement_percent': 100.0
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка очистки логов: {e}")
            return None
    
    def save_optimizations(self, optimizations: List[Dict]):
        try:
            conn = sqlite3.connect(self.optimization_db)
            cursor = conn.cursor()
            
            for opt in optimizations:
                cursor.execute("""
                    INSERT INTO auto_optimizations 
                    (timestamp, optimization_type, description, improvement_percent)
                    VALUES (?, ?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    opt['type'],
                    opt['description'],
                    opt['improvement_percent']
                ))
            
            conn.commit()
            conn.close()
            logger.info(f"Сохранено {len(optimizations)} оптимизаций")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения: {e}")

async def main():
    optimizer = PerformanceOptimizer()
    
    logger.info("🚀 Запуск оптимизации производительности...")
    
    # Анализируем производительность
    analysis = await optimizer.analyze_performance()
    
    # Применяем оптимизации
    optimizations = await optimizer.apply_optimizations()
    
    # Выводим результаты
    print("\n📊 АНАЛИЗ ПРОИЗВОДИТЕЛЬНОСТИ:")
    print("=" * 50)
    
    if analysis.get('system'):
        sys = analysis['system']
        print(f"💻 СИСТЕМНЫЕ МЕТРИКИ:")
        print(f"  CPU: {sys.get('cpu_percent', 0):.1f}%")
        print(f"  Память: {sys.get('memory_percent', 0):.1f}%")
        print(f"  Диск: {sys.get('disk_percent', 0):.1f}%")
    
    if analysis.get('recommendations'):
        print(f"\n💡 РЕКОМЕНДАЦИИ ({len(analysis['recommendations'])}):")
        for i, rec in enumerate(analysis['recommendations'][:3], 1):
            print(f"  {i}. [{rec['priority'].upper()}] {rec['recommendation']}")
    
    if optimizations:
        print(f"\n⚡ АВТОМАТИЧЕСКИЕ ОПТИМИЗАЦИИ ({len(optimizations)}):")
        for opt in optimizations:
            print(f"  ✅ {opt['description']}")
    
    print("=" * 50)
    
    return analysis

if __name__ == "__main__":
    asyncio.run(main())
