#!/usr/bin/env python3
"""
Простая система оптимизации производительности
"""

import psutil
import time
import os
from datetime import datetime

def analyze_system():
    """Анализ системы"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    print("📊 АНАЛИЗ СИСТЕМЫ:")
    print("=" * 40)
    print(f"CPU: {cpu_percent:.1f}%")
    print(f"Память: {memory.percent:.1f}%")
    print(f"Диск: {(disk.used / disk.total) * 100:.1f}%")
    
    recommendations = []
    
    if cpu_percent > 80:
        recommendations.append("⚠️ Высокое использование CPU")
    
    if memory.percent > 85:
        recommendations.append("⚠️ Высокое использование памяти")
    
    if (disk.used / disk.total) * 100 > 90:
        recommendations.append("⚠️ Мало места на диске")
    
    if recommendations:
        print("\n💡 РЕКОМЕНДАЦИИ:")
        for rec in recommendations:
            print(f"  {rec}")
    else:
        print("\n✅ Система работает нормально")
    
    return {
        'cpu': cpu_percent,
        'memory': memory.percent,
        'disk': (disk.used / disk.total) * 100,
        'recommendations': recommendations
    }

def cleanup_logs():
    """Очистка логов"""
    print("\n🧹 ОЧИСТКА ЛОГОВ:")
    
    log_files = [
        'monitoring/monitoring.log',
        'backend/logs/app.log'
    ]
    
    cleaned = 0
    for log_file in log_files:
        if os.path.exists(log_file):
            try:
                size = os.path.getsize(log_file)
                if size > 1024 * 1024:  # 1MB
                    with open(log_file, 'w') as f:
                        f.write('')
                    print(f"  ✅ Очищен {log_file}")
                    cleaned += 1
            except:
                pass
    
    if cleaned == 0:
        print("  ℹ️ Логи не требуют очистки")
    
    return cleaned

def main():
    print("🚀 ПРОСТАЯ ОПТИМИЗАЦИЯ ПРОИЗВОДИТЕЛЬНОСТИ")
    print("=" * 50)
    
    # Анализируем систему
    analysis = analyze_system()
    
    # Очищаем логи
    cleaned = cleanup_logs()
    
    print("\n" + "=" * 50)
    print("✅ Оптимизация завершена!")
    
    return analysis

if __name__ == "__main__":
    main()
