import requests
import json

# Тест ML сервиса
url = "http://localhost:8001/api/v1/predictions/predict"

data = {
    "asset": "BTC",
    "entry_price": 50000,
    "target_price": 55000,
    "stop_loss": 48000,
    "direction": "LONG"
}

try:
    response = requests.post(url, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}") 