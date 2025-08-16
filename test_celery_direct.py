#!/usr/bin/env python3
"""
Прямой тест Celery задач без Redis
"""

import sys
import os
from datetime import datetime

# Добавляем пути для импорта
sys.path.append(os.path.join(os.path.dirname(__file__), 'workers'))

def test_tasks_directly():
    """Тест задач напрямую"""
    print("🔍 Прямой тест задач...")
    
    try:
        # Импортируем задачи напрямую
        from workers.tasks import (
            collect_telegram_signals,
            update_channel_statistics,
            check_signal_results,
            get_ml_predictions,
            monitor_prices,
            get_telegram_stats
        )
        
        print("✅ Все задачи импортированы успешно")
        
        # Тестируем каждую задачу
        tasks = [
            ("Сбор сигналов", collect_telegram_signals),
            ("Обновление статистики", update_channel_statistics),
            ("Проверка результатов", check_signal_results),
            ("ML предсказания", get_ml_predictions),
            ("Мониторинг цен", monitor_prices),
            ("Статистика Telegram", get_telegram_stats)
        ]
        
        results = []
        for name, task in tasks:
            print(f"\n📡 Тестируем: {name}")
            try:
                result = task()
                status = result.get('status', 'unknown')
                print(f"   ✅ {name}: {status}")
                results.append((name, True, result))
            except Exception as e:
                print(f"   ❌ {name}: {e}")
                results.append((name, False, str(e)))
        
        return results
        
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        return []

def test_periodic_config():
    """Тест конфигурации периодических задач"""
    print("\n🔍 Тест конфигурации периодических задач...")
    
    try:
        from workers.tasks import app
        
        # Проверяем настройки периодических задач
        periodic_tasks = app.conf.beat_schedule
        
        if periodic_tasks:
            print("✅ Периодические задачи настроены:")
            for task_name, task_config in periodic_tasks.items():
                interval = task_config.get('schedule', 'unknown')
                print(f"   • {task_name}: каждые {interval} секунд")
        else:
            print("⚠️ Периодические задачи не настроены")
            
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки периодических задач: {e}")
        return False

def main():
    """Основная функция"""
    print("🚀 ПРЯМОЙ ТЕСТ CELERY ЗАДАЧ")
    print("=" * 50)
    print(f"Время: {datetime.now()}")
    print("=" * 50)
    
    # Тест задач
    task_results = test_tasks_directly()
    
    # Тест конфигурации
    config_ok = test_periodic_config()
    
    # Анализ результатов
    print("\n" + "=" * 50)
    print("📊 РЕЗУЛЬТАТЫ:")
    
    successful_tasks = sum(1 for _, success, _ in task_results if success)
    total_tasks = len(task_results)
    
    print(f"   Задачи: {successful_tasks}/{total_tasks} работают")
    print(f"   Конфигурация: {'✅' if config_ok else '❌'}")
    
    if successful_tasks == total_tasks and config_ok:
        print("\n🎉 ПОЛНАЯ АВТОМАТИЗАЦИЯ CELERY ГОТОВА!")
    else:
        print("\n⚠️ Есть проблемы с автоматизацией")
        
    # Детали по задачам
    print("\n📋 Детали по задачам:")
    for name, success, result in task_results:
        status = "✅" if success else "❌"
        print(f"   {name}: {status}")
        if success and isinstance(result, dict):
            details = result.get('status', 'unknown')
            print(f"      Статус: {details}")
    
    print("=" * 50)

if __name__ == "__main__":
    main()
