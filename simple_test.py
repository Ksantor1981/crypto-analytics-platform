import requests
import json

# Тестирование ML сервиса
def test_ml_simple():
    url = "http://localhost:8001/api/v1/predictions/signal"
    
    # Добавляем все обязательные поля
    data = {
        "asset": "BTC",
        "direction": "LONG", 
        "entry_price": 45000.0,
        "target_price": 47000.0,
        "stop_loss": 43000.0,
        "channel_id": 1,
        "channel_accuracy": 0.75,
        "confidence": 0.8
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Статус: {response.status_code}")
        print(f"Ответ: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Успех! Вероятность: {result['success_probability']:.1%}")
            print(f"🎯 Рекомендация: {result['recommendation']}")
        else:
            print(f"❌ Ошибка: {response.status_code}")
            print(f"Детали: {response.text}")
            
    except Exception as e:
        print(f"❌ Исключение: {e}")

if __name__ == "__main__":
    test_ml_simple() 