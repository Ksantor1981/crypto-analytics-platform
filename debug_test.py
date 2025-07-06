import requests
import json

def debug_ml_service():
    print("🔍 Отладка ML сервиса")
    
    # Минимальные данные
    data = {
        "asset": "BTC",
        "direction": "LONG",
        "entry_price": 45000.0,
        "channel_id": 1
    }
    
    print(f"📤 Отправляем: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(
            "http://localhost:8001/api/v1/predictions/signal",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📥 Статус: {response.status_code}")
        print(f"📥 Заголовки: {dict(response.headers)}")
        print(f"📥 Ответ: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Успешный ответ!")
            for key, value in result.items():
                print(f"   {key}: {value}")
        
    except Exception as e:
        print(f"❌ Исключение: {e}")

if __name__ == "__main__":
    debug_ml_service() 