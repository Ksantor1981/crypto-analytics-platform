#!/bin/bash
# Загрузить исторические данные и техиндикаторы

echo "=== Загрузка исторических данных с Binance ==="

# Загружаем данные через Python API
python3 << 'EOF'
import requests
import json
from datetime import datetime, timezone, timedelta
from decimal import Decimal

# Binance API
BINANCE_API = "https://api.binance.com/api/v3"

symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
days = 90
interval = "4h"

for symbol in symbols:
    print(f"\nГружу {symbol} за {days} дней...")

    start_time = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp() * 1000)
    end_time = int(datetime.now(timezone.utc).timestamp() * 1000)

    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1000
    }

    try:
        response = requests.get(f"{BINANCE_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        candles = response.json()

        print(f"Получено {len(candles)} свечей")

        # Сохраняем в JSON
        with open(f"/tmp/{symbol}_candles.json", "w") as f:
            json.dump(candles, f)
    except Exception as e:
        print(f"Ошибка: {e}")

EOF

echo "Данные загружены в /tmp/"
