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
                "http://localhost:8001/api/v1/predictions/predict",
                json=test_signal
            )
            print(f"   Статус: {response.status_code}")
            
            if response.status_code == 200:
                prediction = response.json()
                success_prob = prediction.get('success_probability', 'N/A')
                confidence = prediction.get('confidence', 'N/A')
                print(f"   Вероятность успеха: {success_prob}")
                print(f"   Уверенность: {confidence}")
                print(f"   Рекомендация: {prediction.get('recommendation', 'N/A')}")
                print(f"   Риск-скор: {prediction.get('risk_score', 'N/A')}")
                print(f"   Версия модели: {prediction.get('model_version', 'N/A')}")
                
                # Показать важность признаков
                features_importance = prediction.get('features_importance', {})
                if features_importance:
                    print("   Важность признаков:")
                    for feature, importance in features_importance.items():
                        print(f"     - {feature}: {importance}")
            else:
                print(f"   Ошибка: {response.text}")
            print()
            
            # Тест 4: Пакетное предсказание
            print("📊 Тест 4: Пакетное предсказание")
            batch_request = ["BTCUSDT", "ETHUSDT"]
            
            response = await client.post(
                "http://localhost:8001/api/v1/predictions/batch-predict",
                json=batch_request
            )
            print(f"   Статус: {response.status_code}")
            
            if response.status_code == 200:
                batch_result = response.json()
                results = batch_result.get('results', {})
                print(f"   Обработано активов: {len(results)}")
                
                for asset, result in results.items():
                    print(f"   {asset}:")
                    if 'error' not in result:
                        print(f"     - Текущая цена: ${result.get('current_price', 'N/A')}")
                        print(f"     - Изменение 24ч: {result.get('change_24h', 'N/A')}%")
                        print(f"     - Тренд: {result.get('trend', 'N/A')}")
                        print(f"     - Рекомендация: {result.get('recommendation', 'N/A')}")
                    else:
                        print(f"     - Ошибка: {result.get('error', 'N/A')}")
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