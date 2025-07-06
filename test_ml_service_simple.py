#!/usr/bin/env python3
"""
Простой тест ML сервиса
"""

import asyncio
import httpx
import json
from datetime import datetime

async def test_ml_service():
    """Тест ML сервиса"""
    print("🤖 Тестирование ML Service...")
    print("=" * 60)
    
    # Тестовые данные для сигнала
    test_signal = {
        "asset": "BTCUSDT",
        "direction": "LONG",
        "entry_price": 45000.0,
        "target_price": 47000.0,
        "stop_loss": 43000.0,
        "channel_id": 1,
        "channel_accuracy": 0.75,
        "confidence": 0.8
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Тест 1: Health check
            print("📊 Тест 1: Health Check")
            response = await client.get("http://localhost:8001/api/v1/health/")
            print(f"   Статус: {response.status_code}")
            if response.status_code == 200:
                print(f"   Ответ: {response.json()}")
            print()
            
            # Тест 2: Информация о модели
            print("📊 Тест 2: Информация о модели")
            response = await client.get("http://localhost:8001/api/v1/predictions/model/info")
            print(f"   Статус: {response.status_code}")
            if response.status_code == 200:
                model_info = response.json()
                print(f"   Версия модели: {model_info.get('model_version', 'N/A')}")
                print(f"   Количество признаков: {model_info.get('features_count', 'N/A')}")
                print(f"   Тип модели: {model_info.get('model_type', 'N/A')}")
            print()
            
            # Тест 3: Предсказание для сигнала
            print("📊 Тест 3: Предсказание для сигнала")
            response = await client.post(
                "http://localhost:8001/api/v1/predictions/signal",
                json=test_signal
            )
            print(f"   Статус: {response.status_code}")
            
            if response.status_code == 200:
                prediction = response.json()
                print(f"   Вероятность успеха: {prediction.get('success_probability', 'N/A'):.2%}")
                print(f"   Уверенность: {prediction.get('confidence', 'N/A'):.2%}")
                print(f"   Рекомендация: {prediction.get('recommendation', 'N/A')}")
                print(f"   Риск-скор: {prediction.get('risk_score', 'N/A'):.2f}")
                print(f"   Версия модели: {prediction.get('model_version', 'N/A')}")
                
                # Показать важность признаков
                features_importance = prediction.get('features_importance', {})
                if features_importance:
                    print("   Важность признаков:")
                    for feature, importance in features_importance.items():
                        print(f"     - {feature}: {importance:.2%}")
            else:
                print(f"   Ошибка: {response.text}")
            print()
            
            # Тест 4: Пакетное предсказание
            print("📊 Тест 4: Пакетное предсказание")
            batch_request = {
                "signals": [
                    test_signal,
                    {
                        "asset": "ETHUSDT",
                        "direction": "SHORT",
                        "entry_price": 3000.0,
                        "target_price": 2800.0,
                        "stop_loss": 3200.0,
                        "channel_id": 2,
                        "channel_accuracy": 0.65,
                        "confidence": 0.6
                    }
                ]
            }
            
            response = await client.post(
                "http://localhost:8001/api/v1/predictions/batch",
                json=batch_request
            )
            print(f"   Статус: {response.status_code}")
            
            if response.status_code == 200:
                batch_result = response.json()
                predictions = batch_result.get('predictions', [])
                print(f"   Обработано предсказаний: {len(predictions)}")
                
                for i, pred in enumerate(predictions):
                    print(f"   Сигнал {i+1}:")
                    print(f"     - Вероятность успеха: {pred.get('success_probability', 'N/A'):.2%}")
                    print(f"     - Рекомендация: {pred.get('recommendation', 'N/A')}")
            else:
                print(f"   Ошибка: {response.text}")
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {str(e)}")
        return False
    
    print("=" * 60)
    print("✅ Тестирование ML Service завершено")
    return True

if __name__ == "__main__":
    asyncio.run(test_ml_service()) 