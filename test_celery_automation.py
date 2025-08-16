#!/usr/bin/env python3
"""
Тест полной автоматизации Celery
"""

import sys
import os
import asyncio
from datetime import datetime

# Добавляем пути для импорта
sys.path.append(os.path.join(os.path.dirname(__file__), 'workers'))

def test_celery_tasks():
    """Тест всех Celery задач"""
    print("🔍 Тест Celery задач...")
    
    try:
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

def test_periodic_tasks():
    """Тест настройки периодических задач"""
    print("\n🔍 Тест периодических задач...")
    
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

def test_worker_health():
    """Тест здоровья worker'а"""
    print("\n🔍 Тест здоровья worker'а...")
    
    try:
        from workers.tasks import app
        
        # Проверяем конфигурацию
        broker_url = app.conf.broker_url
        backend_url = app.conf.result_backend
        
        print(f"✅ Broker: {broker_url}")
        print(f"✅ Backend: {backend_url}")
        
        # Проверяем доступность Redis
        import redis
        try:
            r = redis.from_url(broker_url)
            r.ping()
            print("✅ Redis доступен")
            return True
        except Exception as e:
            print(f"❌ Redis недоступен: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка проверки здоровья: {e}")
        return False

def main():
    """Основная функция"""
    print("🚀 ТЕСТ ПОЛНОЙ АВТОМАТИЗАЦИИ CELERY")
    print("=" * 50)
    print(f"Время: {datetime.now()}")
    print("=" * 50)
    
    # Тест здоровья
    health_ok = test_worker_health()
    
    if health_ok:
        # Тест задач
        task_results = test_celery_tasks()
        
        # Тест периодических задач
        periodic_ok = test_periodic_tasks()
        
        # Анализ результатов
        print("\n" + "=" * 50)
        print("📊 РЕЗУЛЬТАТЫ:")
        
        successful_tasks = sum(1 for _, success, _ in task_results if success)
        total_tasks = len(task_results)
        
        print(f"   Задачи: {successful_tasks}/{total_tasks} работают")
        print(f"   Периодические задачи: {'✅' if periodic_ok else '❌'}")
        print(f"   Worker здоровье: {'✅' if health_ok else '❌'}")
        
        if successful_tasks == total_tasks and periodic_ok and health_ok:
            print("\n🎉 ПОЛНАЯ АВТОМАТИЗАЦИЯ CELERY РАБОТАЕТ!")
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
    else:
        print("\n❌ Worker не готов к работе")
    
    print("=" * 50)

if __name__ == "__main__":
    main()
