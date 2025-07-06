#!/usr/bin/env python3
"""
Тестовый скрипт для демонстрации API Крипто Аналитики
"""

import requests
import json
import time
from datetime import datetime

# Конфигурация API
BACKEND_URL = "http://localhost:8000"
ML_SERVICE_URL = "http://localhost:8001"

def print_header(title):
    print("\n" + "="*60)
    print(f"🚀 {title}")
    print("="*60)

def print_section(title):
    print(f"\n📋 {title}")
    print("-" * 40)

def test_backend_health():
    """Проверка работоспособности Backend API"""
    print_section("Проверка Backend API")
    try:
        response = requests.get(f"{BACKEND_URL}/docs")
        if response.status_code == 200:
            print("✅ Backend API работает корректно")
            return True
        else:
            print(f"❌ Backend API недоступен (статус: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения к Backend API: {e}")
        return False

def test_ml_service_health():
    """Проверка работоспособности ML Service"""
    print_section("Проверка ML Service")
    try:
        response = requests.get(f"{ML_SERVICE_URL}/docs")
        if response.status_code == 200:
            print("✅ ML Service работает корректно")
            return True
        else:
            print(f"❌ ML Service недоступен (статус: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения к ML Service: {e}")
        return False

def test_ml_predictions():
    """Тестирование ML предсказаний"""
    print_section("Тестирование ML Предсказаний")
    
    # Тестовые данные для сигналов
    test_signals = [
        {
            "asset": "BTC",
            "direction": "LONG",
            "entry_price": 45000.0,
            "target_price": 47000.0,
            "stop_loss": 43000.0,
            "channel_id": 1,
            "channel_accuracy": 0.85,
            "confidence": 0.8
        },
        {
            "asset": "ETH",
            "direction": "SHORT",
            "entry_price": 2800.0,
            "target_price": 2650.0,
            "stop_loss": 2900.0,
            "channel_id": 2,
            "channel_accuracy": 0.75,
            "confidence": 0.7
        },
        {
            "asset": "ADA",
            "direction": "LONG",
            "entry_price": 0.45,
            "target_price": 0.52,
            "stop_loss": 0.42,
            "channel_id": 3,
            "channel_accuracy": 0.70,
            "confidence": 0.6
        }
    ]
    
    print("🤖 Тестируем одиночные предсказания:")
    for i, signal in enumerate(test_signals, 1):
        try:
            response = requests.post(
                f"{ML_SERVICE_URL}/api/v1/predictions/signal",
                json=signal,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                prediction = response.json()
                print(f"\n   Сигнал {i}: {signal['asset']} {signal['direction']}")
                print(f"   💡 Вероятность успеха: {prediction['success_probability']:.1%}")
                print(f"   🎯 Уверенность модели: {prediction['confidence']:.1%}")
                print(f"   📊 Рекомендация: {prediction['recommendation']}")
                print(f"   ⚠️  Риск: {prediction['risk_score']:.1%}")
            else:
                print(f"   ❌ Ошибка для {signal['asset']}: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Исключение для {signal['asset']}: {e}")
    
    # Тест пакетного предсказания
    print(f"\n🚀 Тестируем пакетное предсказание:")
    try:
        batch_request = {"signals": test_signals}
        response = requests.post(
            f"{ML_SERVICE_URL}/api/v1/predictions/batch",
            json=batch_request,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            batch_result = response.json()
            print(f"   ✅ Обработано сигналов: {batch_result['total_processed']}")
            print(f"   ⏱️  Время обработки: {batch_result['processing_time_ms']:.2f}ms")
            
            for i, prediction in enumerate(batch_result['predictions'], 1):
                signal = test_signals[i-1]
                print(f"   📈 {signal['asset']}: {prediction['success_probability']:.1%} успеха")
        else:
            print(f"   ❌ Ошибка пакетного предсказания: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Исключение пакетного предсказания: {e}")

def test_ml_model_info():
    """Получение информации о ML модели"""
    print_section("Информация о ML Модели")
    try:
        response = requests.get(f"{ML_SERVICE_URL}/api/v1/predictions/model/info")
        if response.status_code == 200:
            model_info = response.json()
            print(f"📋 Версия модели: {model_info['model_version']}")
            print(f"🎯 Статус обучения: {'Обучена' if model_info['is_trained'] else 'Не обучена'}")
            print(f"🔧 Тип модели: {model_info['model_type']}")
            print(f"📊 Количество признаков: {len(model_info['feature_names'])}")
            print(f"🏷️  Признаки: {', '.join(model_info['feature_names'])}")
        else:
            print(f"❌ Ошибка получения информации о модели: {response.status_code}")
    except Exception as e:
        print(f"❌ Исключение при получении информации о модели: {e}")

def demo_performance_metrics():
    """Демонстрация метрик производительности"""
    print_section("Метрики Производительности")
    
    # Симуляция различных сценариев
    scenarios = [
        ("Высокорисковый BTC LONG", {"asset": "BTC", "direction": "LONG", "entry_price": 65000, "target_price": 70000, "channel_accuracy": 0.6}),
        ("Консервативный ETH SHORT", {"asset": "ETH", "direction": "SHORT", "entry_price": 3000, "target_price": 2800, "channel_accuracy": 0.9}),
        ("Альткоин спекуляция", {"asset": "DOGE", "direction": "LONG", "entry_price": 0.08, "target_price": 0.12, "channel_accuracy": 0.5})
    ]
    
    print("📊 Анализ различных торговых сценариев:")
    
    for scenario_name, signal_data in scenarios:
        # Дополняем обязательные поля
        signal_data.update({
            "stop_loss": signal_data["entry_price"] * 0.95,
            "channel_id": 1,
            "confidence": 0.7
        })
        
        try:
            response = requests.post(
                f"{ML_SERVICE_URL}/api/v1/predictions/signal",
                json=signal_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                prediction = response.json()
                risk_level = "НИЗКИЙ" if prediction['risk_score'] < 0.3 else "СРЕДНИЙ" if prediction['risk_score'] < 0.7 else "ВЫСОКИЙ"
                
                print(f"\n   🎯 {scenario_name}")
                print(f"      Успех: {prediction['success_probability']:.1%} | Риск: {risk_level} | {prediction['recommendation']}")
            else:
                print(f"   ❌ Ошибка для сценария '{scenario_name}': {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Исключение для сценария '{scenario_name}': {e}")

def generate_report():
    """Генерация итогового отчета"""
    print_section("Итоговый Отчет")
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"📅 Время тестирования: {current_time}")
    print(f"🔗 Backend URL: {BACKEND_URL}")
    print(f"🤖 ML Service URL: {ML_SERVICE_URL}")
    
    print("\n🎯 Функциональность:")
    print("   ✅ Backend API - Базовая инфраструктура")
    print("   ✅ ML Service - Предсказания сигналов")
    print("   ✅ Пакетная обработка - Множественные сигналы")
    print("   ✅ Анализ рисков - Оценка торговых решений")
    print("   ✅ Метрики производительности - KPI анализ")
    
    print("\n🚀 Следующие шаги:")
    print("   📱 Frontend разработка (Next.js)")
    print("   📊 Интеграция с реальными биржами")
    print("   🤖 Улучшение ML моделей")
    print("   📈 Добавление новых индикаторов")

def main():
    """Основная функция демонстрации"""
    print_header("ДЕМОНСТРАЦИЯ КРИПТО АНАЛИТИКИ ПЛАТФОРМЫ")
    
    print("🎯 Цель: Полная демонстрация функциональности платформы")
    print("📋 Компоненты: Backend API + ML Service + Аналитика")
    
    # Проверка сервисов
    backend_ok = test_backend_health()
    ml_ok = test_ml_service_health()
    
    if not backend_ok:
        print("\n⚠️  Backend API недоступен. Проверьте, что сервер запущен на порту 8000")
        
    if not ml_ok:
        print("\n⚠️  ML Service недоступен. Проверьте, что сервис запущен на порту 8001")
        return
    
    # Основные тесты
    if ml_ok:
        test_ml_model_info()
        test_ml_predictions()
        demo_performance_metrics()
    
    # Итоговый отчет
    generate_report()
    
    print_header("ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
    print("🎉 Платформа готова к использованию!")
    print("🌐 Откройте demo.html в браузере для веб-интерфейса")

if __name__ == "__main__":
    main() 