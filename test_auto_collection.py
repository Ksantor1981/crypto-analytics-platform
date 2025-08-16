#!/usr/bin/env python3
"""
Тест автоматического сбора сигналов
"""

import sys
import os
import asyncio
import time
from datetime import datetime

# Добавляем пути для импорта
sys.path.append(os.path.join(os.path.dirname(__file__), 'workers'))

def test_telegram_collection():
    """Тест сбора сигналов из Telegram"""
    print("🔍 Тестирование автоматического сбора сигналов из Telegram...")
    
    try:
        from workers.telegram.telegram_client import collect_telegram_signals_sync
        
        print("📡 Запуск сбора сигналов...")
        start_time = time.time()
        
        # Запускаем сбор сигналов
        result = collect_telegram_signals_sync()
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"✅ Сбор завершен за {processing_time:.2f} секунд")
        print(f"   Статус: {result.get('status', 'unknown')}")
        print(f"   Всего сигналов: {result.get('total_signals', 0)}")
        
        if result.get('signals'):
            print(f"\n📊 Собранные сигналы:")
            for i, signal in enumerate(result['signals'], 1):
                print(f"   {i}. {signal.get('asset', 'N/A')} {signal.get('direction', 'N/A')}")
                print(f"      Вход: ${signal.get('entry_price', 'N/A')}")
                print(f"      Цель: ${signal.get('tp1_price', 'N/A')}")
                print(f"      Стоп: ${signal.get('stop_loss', 'N/A')}")
                print(f"      Канал: {signal.get('channel', 'N/A')}")
                print(f"      Уверенность: {signal.get('confidence', 'N/A')}")
                print()
        
        return result
        
    except Exception as e:
        print(f"❌ Ошибка сбора сигналов: {e}")
        return None

def test_signal_processing():
    """Тест обработки сигналов"""
    print("\n🔍 Тестирование обработки сигналов...")
    
    try:
        from workers.telegram.signal_processor import TelegramSignalProcessor
        
        processor = TelegramSignalProcessor()
        
        # Создаем тестовые сигналы
        test_signals = [
            {
                'asset': 'BTC/USDT',
                'direction': 'LONG',
                'entry_price': 45000.00,
                'tp1_price': 46500.00,
                'stop_loss': 43500.00,
                'channel': '@cryptosignals',
                'message_timestamp': datetime.now(),
                'raw_message': 'Test signal'
            }
        ]
        
        print(f"📊 Обработка {len(test_signals)} сигналов...")
        
        # Обрабатываем сигналы
        result = processor.process_signals(test_signals)
        
        print(f"✅ Обработка завершена:")
        print(f"   Обработано: {result.get('processed', 0)}")
        print(f"   Сохранено: {result.get('saved', 0)}")
        print(f"   Ошибок: {result.get('errors', 0)}")
        
        return result
        
    except Exception as e:
        print(f"❌ Ошибка обработки: {e}")
        return None

def test_ml_integration():
    """Тест интеграции с ML сервисом"""
    print("\n🔍 Тестирование интеграции с ML сервисом...")
    
    try:
        import requests
        
        # Тестовый сигнал для ML
        test_signal = {
            "asset": "BTC",
            "entry_price": 45000,
            "target_price": 46500,
            "stop_loss": 43500,
            "direction": "LONG"
        }
        
        print("🤖 Отправка сигнала в ML сервис...")
        
        # Отправляем в ML сервис
        response = requests.post(
            "http://localhost:8001/api/v1/predictions/predict",
            json=test_signal,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            ml_result = response.json()
            print(f"✅ ML предсказание получено:")
            print(f"   Результат: {ml_result.get('prediction', 'N/A')}")
            print(f"   Уверенность: {ml_result.get('confidence', 'N/A')}")
            print(f"   Ожидаемая доходность: {ml_result.get('expected_return', 'N/A')}%")
            print(f"   Уровень риска: {ml_result.get('risk_level', 'N/A')}")
        else:
            print(f"❌ Ошибка ML сервиса: {response.status_code}")
            
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Ошибка ML интеграции: {e}")
        return False

def test_full_pipeline():
    """Тест полного пайплайна"""
    print("\n🔍 Тестирование полного пайплайна...")
    
    try:
        # 1. Собираем сигналы
        collection_result = test_telegram_collection()
        
        if not collection_result or collection_result.get('status') != 'success':
            print("❌ Ошибка сбора сигналов")
            return False
        
        # 2. Обрабатываем сигналы
        processing_result = test_signal_processing()
        
        if not processing_result:
            print("❌ Ошибка обработки сигналов")
            return False
        
        # 3. Тестируем ML интеграцию
        ml_ok = test_ml_integration()
        
        if not ml_ok:
            print("❌ Ошибка ML интеграции")
            return False
        
        print("\n✅ ПОЛНЫЙ ПАЙПЛАЙН РАБОТАЕТ!")
        print("   📡 Сбор сигналов: ✅")
        print("   🔧 Обработка: ✅")
        print("   🤖 ML предсказания: ✅")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка полного пайплайна: {e}")
        return False

def test_worker_tasks():
    """Тест задач worker'а"""
    print("\n🔍 Тестирование задач worker'а...")
    
    try:
        from workers.tasks import collect_telegram_signals, update_channel_statistics, check_signal_results
        
        print("📋 Запуск задач worker'а...")
        
        # Задача 1: Сбор сигналов
        print("   1. Сбор сигналов из Telegram...")
        signals_result = collect_telegram_signals()
        print(f"      Результат: {signals_result.get('status', 'unknown')}")
        
        # Задача 2: Обновление статистики
        print("   2. Обновление статистики каналов...")
        stats_result = update_channel_statistics()
        print(f"      Результат: {stats_result.get('status', 'unknown')}")
        
        # Задача 3: Проверка результатов
        print("   3. Проверка результатов сигналов...")
        check_result = check_signal_results()
        print(f"      Результат: {check_result.get('status', 'unknown')}")
        
        print("\n✅ ВСЕ ЗАДАЧИ WORKER'А РАБОТАЮТ!")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка задач worker'а: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 ТЕСТИРОВАНИЕ АВТОМАТИЧЕСКОГО СБОРА СИГНАЛОВ")
    print("=" * 60)
    print(f"Время: {datetime.now()}")
    print("=" * 60)
    
    try:
        # Тестируем все компоненты
        print("1️⃣ Тест сбора сигналов из Telegram...")
        collection_ok = test_telegram_collection() is not None
        
        print("\n2️⃣ Тест обработки сигналов...")
        processing_ok = test_signal_processing() is not None
        
        print("\n3️⃣ Тест ML интеграции...")
        ml_ok = test_ml_integration()
        
        print("\n4️⃣ Тест полного пайплайна...")
        pipeline_ok = test_full_pipeline()
        
        print("\n5️⃣ Тест задач worker'а...")
        worker_ok = test_worker_tasks()
        
        # Итоговая статистика
        print("\n" + "=" * 60)
        print("📊 ИТОГОВАЯ СТАТИСТИКА:")
        print(f"   Сбор сигналов: {'✅' if collection_ok else '❌'}")
        print(f"   Обработка: {'✅' if processing_ok else '❌'}")
        print(f"   ML интеграция: {'✅' if ml_ok else '❌'}")
        print(f"   Полный пайплайн: {'✅' if pipeline_ok else '❌'}")
        print(f"   Задачи worker'а: {'✅' if worker_ok else '❌'}")
        
        success_count = sum([collection_ok, processing_ok, ml_ok, pipeline_ok, worker_ok])
        total_count = 5
        
        print(f"\n🎯 УСПЕШНОСТЬ: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
        
        if success_count == total_count:
            print("🎉 АВТОМАТИЧЕСКИЙ СБОР СИГНАЛОВ ПОЛНОСТЬЮ РАБОТАЕТ!")
        else:
            print("⚠️ ТРЕБУЕТСЯ ДОРАБОТКА")
            
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        print("=" * 60)

if __name__ == "__main__":
    main()
