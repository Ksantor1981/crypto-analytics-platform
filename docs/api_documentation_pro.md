# 🔌 API Documentation для Pro пользователей

## 📋 Обзор

Данная документация предназначена для Pro пользователей Crypto Analytics Platform и содержит подробную информацию о всех доступных API endpoints, методах аутентификации и примерах использования.

## 🔑 Аутентификация

### API Key аутентификация

Pro пользователи получают персональный API ключ для доступа к расширенным функциям.

```bash
# Пример заголовка авторизации
Authorization: Bearer YOUR_API_KEY
```

### Получение API ключа

1. Войдите в свой аккаунт
2. Перейдите в раздел "Настройки" → "API ключи"
3. Создайте новый API ключ
4. Сохраните ключ в безопасном месте

**⚠️ Важно:** API ключ предоставляет полный доступ к вашему аккаунту. Храните его в безопасности!

## 🌐 Базовый URL

```
Production: https://api.cryptoanalytics.com/v1
Staging: https://staging-api.cryptoanalytics.com/v1
```

## 📊 Endpoints

### Аутентификация

#### POST /auth/refresh
Обновление токена доступа

```bash
curl -X POST "https://api.cryptoanalytics.com/v1/auth/refresh" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

**Ответ:**
```json
{
  "access_token": "new_access_token",
  "refresh_token": "new_refresh_token",
  "expires_in": 3600
}
```

### Пользователи

#### GET /users/me
Получение информации о текущем пользователе

```bash
curl -X GET "https://api.cryptoanalytics.com/v1/users/me" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Ответ:**
```json
{
  "id": 123,
  "email": "user@example.com",
  "username": "trader123",
  "subscription_plan": "pro",
  "subscription_expires": "2025-12-31T23:59:59Z",
  "api_quota": {
    "used": 1500,
    "limit": 10000,
    "reset_date": "2025-09-01T00:00:00Z"
  },
  "created_at": "2025-01-01T00:00:00Z",
  "last_login": "2025-08-16T10:30:00Z"
}
```

#### PUT /users/me
Обновление профиля пользователя

```bash
curl -X PUT "https://api.cryptoanalytics.com/v1/users/me" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "new_username",
    "timezone": "UTC",
    "notifications": {
      "email": true,
      "telegram": false,
      "webhook": true
    }
  }'
```

### Каналы

#### GET /channels
Получение списка каналов с расширенной фильтрацией

```bash
curl -X GET "https://api.cryptoanalytics.com/v1/channels?category=crypto&min_accuracy=80&limit=50&offset=0" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Параметры запроса:**
- `category` - категория канала (crypto, forex, stocks)
- `min_accuracy` - минимальная точность (0-100)
- `min_signals` - минимальное количество сигналов
- `sort_by` - сортировка (accuracy, signals_count, created_at)
- `order` - порядок сортировки (asc, desc)
- `limit` - количество записей (максимум 100)
- `offset` - смещение для пагинации

**Ответ:**
```json
{
  "channels": [
    {
      "id": 1,
      "name": "Crypto Signals Pro",
      "url": "https://t.me/cryptosignalspro",
      "category": "crypto",
      "accuracy": 87.5,
      "signals_count": 1250,
      "roi": 15.3,
      "max_drawdown": -8.2,
      "sharpe_ratio": 1.8,
      "last_signal": "2025-08-16T10:00:00Z",
      "status": "active",
      "ml_prediction": {
        "success_probability": 0.85,
        "confidence": 0.92,
        "risk_score": 0.15
      }
    }
  ],
  "pagination": {
    "total": 150,
    "page": 1,
    "per_page": 50,
    "pages": 3
  }
}
```

#### GET /channels/{id}
Получение детальной информации о канале

```bash
curl -X GET "https://api.cryptoanalytics.com/v1/channels/1" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Ответ:**
```json
{
  "id": 1,
  "name": "Crypto Signals Pro",
  "url": "https://t.me/cryptosignalspro",
  "category": "crypto",
  "description": "Professional crypto trading signals",
  "accuracy": 87.5,
  "signals_count": 1250,
  "roi": 15.3,
  "max_drawdown": -8.2,
  "sharpe_ratio": 1.8,
  "win_rate": 0.72,
  "avg_profit": 2.1,
  "avg_loss": -1.3,
  "profit_factor": 1.62,
  "recovery_factor": 1.87,
  "last_signal": "2025-08-16T10:00:00Z",
  "status": "active",
  "subscribers_count": 15000,
  "created_at": "2024-01-01T00:00:00Z",
  "performance_history": [
    {
      "date": "2025-08-01",
      "accuracy": 85.2,
      "roi": 12.1,
      "signals_count": 45
    }
  ],
  "ml_analysis": {
    "success_probability": 0.85,
    "confidence": 0.92,
    "risk_score": 0.15,
    "trend_prediction": "bullish",
    "volatility_forecast": "medium"
  }
}
```

#### POST /channels
Добавление нового канала

```bash
curl -X POST "https://api.cryptoanalytics.com/v1/channels" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Crypto Channel",
    "url": "https://t.me/newcryptochannel",
    "category": "crypto",
    "description": "New professional crypto signals"
  }'
```

### Сигналы

#### GET /signals
Получение списка сигналов с расширенной фильтрацией

```bash
curl -X GET "https://api.cryptoanalytics.com/v1/signals?channel_id=1&type=BUY&status=active&limit=100&offset=0" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Параметры запроса:**
- `channel_id` - ID канала
- `type` - тип сигнала (BUY, SELL)
- `status` - статус сигнала (active, completed, failed)
- `pair` - торговая пара (BTC/USDT, ETH/USDT)
- `min_accuracy` - минимальная точность канала
- `date_from` - дата начала (ISO 8601)
- `date_to` - дата окончания (ISO 8601)
- `sort_by` - сортировка (created_at, accuracy, price)
- `order` - порядок сортировки (asc, desc)
- `limit` - количество записей (максимум 200)
- `offset` - смещение для пагинации

**Ответ:**
```json
{
  "signals": [
    {
      "id": 12345,
      "channel_id": 1,
      "channel_name": "Crypto Signals Pro",
      "pair": "BTC/USDT",
      "type": "BUY",
      "price": 45000.0,
      "target": 46000.0,
      "stop_loss": 44000.0,
      "status": "active",
      "accuracy": 87.5,
      "created_at": "2025-08-16T10:00:00Z",
      "expires_at": "2025-08-16T22:00:00Z",
      "current_price": 45200.0,
      "pnl_percentage": 0.44,
      "ml_prediction": {
        "success_probability": 0.85,
        "confidence": 0.92,
        "risk_score": 0.15,
        "expected_return": 2.2,
        "max_loss": -2.2
      },
      "market_data": {
        "volume_24h": 2500000000,
        "price_change_24h": 2.1,
        "rsi": 65.2,
        "macd": "bullish",
        "support_level": 44800,
        "resistance_level": 45500
      }
    }
  ],
  "pagination": {
    "total": 1250,
    "page": 1,
    "per_page": 100,
    "pages": 13
  }
}
```

#### GET /signals/{id}
Получение детальной информации о сигнале

```bash
curl -X GET "https://api.cryptoanalytics.com/v1/signals/12345" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Ответ:**
```json
{
  "id": 12345,
  "channel_id": 1,
  "channel_name": "Crypto Signals Pro",
  "pair": "BTC/USDT",
  "type": "BUY",
  "price": 45000.0,
  "target": 46000.0,
  "stop_loss": 44000.0,
  "status": "active",
  "accuracy": 87.5,
  "created_at": "2025-08-16T10:00:00Z",
  "expires_at": "2025-08-16T22:00:00Z",
  "current_price": 45200.0,
  "pnl_percentage": 0.44,
  "volume": 1.0,
  "description": "Strong bullish momentum on BTC/USDT",
  "ml_prediction": {
    "success_probability": 0.85,
    "confidence": 0.92,
    "risk_score": 0.15,
    "expected_return": 2.2,
    "max_loss": -2.2,
    "model_version": "v2.1.0",
    "features_used": ["price_action", "volume", "rsi", "macd"]
  },
  "market_data": {
    "volume_24h": 2500000000,
    "price_change_24h": 2.1,
    "price_change_1h": 0.5,
    "rsi": 65.2,
    "macd": "bullish",
    "bollinger_bands": {
      "upper": 45500,
      "middle": 45000,
      "lower": 44500
    },
    "support_level": 44800,
    "resistance_level": 45500,
    "trend": "uptrend"
  },
  "price_history": [
    {
      "timestamp": "2025-08-16T10:00:00Z",
      "price": 45000.0
    },
    {
      "timestamp": "2025-08-16T10:15:00Z",
      "price": 45100.0
    }
  ],
  "similar_signals": [
    {
      "id": 12344,
      "pair": "BTC/USDT",
      "type": "BUY",
      "result": "success",
      "roi": 2.1
    }
  ]
}
```

### ML Предсказания

#### POST /ml/predict
Получение ML предсказания для сигнала

```bash
curl -X POST "https://api.cryptoanalytics.com/v1/ml/predict" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "pair": "BTC/USDT",
    "type": "BUY",
    "price": 45000.0,
    "target": 46000.0,
    "stop_loss": 44000.0,
    "channel_accuracy": 87.5,
    "market_data": {
      "volume_24h": 2500000000,
      "rsi": 65.2,
      "macd": "bullish"
    }
  }'
```

**Ответ:**
```json
{
  "prediction": {
    "success_probability": 0.85,
    "confidence": 0.92,
    "risk_score": 0.15,
    "expected_return": 2.2,
    "max_loss": -2.2,
    "model_version": "v2.1.0",
    "ensemble_weights": {
      "random_forest": 0.4,
      "xgboost": 0.35,
      "neural_network": 0.25
    },
    "feature_importance": {
      "channel_accuracy": 0.25,
      "price_action": 0.20,
      "volume": 0.15,
      "rsi": 0.12,
      "macd": 0.10,
      "market_sentiment": 0.08,
      "volatility": 0.10
    }
  },
  "risk_analysis": {
    "var_95": -1.8,
    "expected_shortfall": -2.5,
    "sharpe_ratio": 1.2,
    "max_drawdown": -3.0
  },
  "recommendations": {
    "position_size": "medium",
    "risk_level": "moderate",
    "timeframe": "4h",
    "stop_loss_adjustment": "none"
  }
}
```

#### GET /ml/models
Получение информации о доступных ML моделях

```bash
curl -X GET "https://api.cryptoanalytics.com/v1/ml/models" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Ответ:**
```json
{
  "models": [
    {
      "name": "ensemble_v2.1.0",
      "version": "2.1.0",
      "accuracy": 87.2,
      "precision": 0.89,
      "recall": 0.85,
      "f1_score": 0.87,
      "last_updated": "2025-08-01T00:00:00Z",
      "components": [
        {
          "name": "random_forest",
          "weight": 0.4,
          "accuracy": 85.1
        },
        {
          "name": "xgboost",
          "weight": 0.35,
          "accuracy": 86.8
        },
        {
          "name": "neural_network",
          "weight": 0.25,
          "accuracy": 88.5
        }
      ]
    }
  ]
}
```

### Аналитика

#### GET /analytics/portfolio
Получение аналитики портфеля

```bash
curl -X GET "https://api.cryptoanalytics.com/v1/analytics/portfolio?date_from=2025-08-01&date_to=2025-08-16" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Ответ:**
```json
{
  "summary": {
    "total_signals": 150,
    "successful_signals": 108,
    "failed_signals": 42,
    "win_rate": 0.72,
    "total_roi": 15.3,
    "avg_roi_per_signal": 0.102,
    "max_drawdown": -8.2,
    "sharpe_ratio": 1.8,
    "profit_factor": 1.62,
    "recovery_factor": 1.87
  },
  "performance_by_channel": [
    {
      "channel_id": 1,
      "channel_name": "Crypto Signals Pro",
      "signals_count": 75,
      "win_rate": 0.76,
      "roi": 18.2
    }
  ],
  "performance_by_pair": [
    {
      "pair": "BTC/USDT",
      "signals_count": 45,
      "win_rate": 0.78,
      "roi": 12.1
    }
  ],
  "daily_performance": [
    {
      "date": "2025-08-01",
      "signals_count": 10,
      "roi": 2.1,
      "win_rate": 0.8
    }
  ]
}
```

#### GET /analytics/backtest
Запуск backtesting для стратегии

```bash
curl -X POST "https://api.cryptoanalytics.com/v1/analytics/backtest" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": {
      "min_accuracy": 80,
      "min_signals": 10,
      "position_size": 0.1,
      "stop_loss": 0.02,
      "take_profit": 0.04
    },
    "date_from": "2025-01-01",
    "date_to": "2025-08-16",
    "initial_capital": 10000
  }'
```

**Ответ:**
```json
{
  "backtest_results": {
    "initial_capital": 10000,
    "final_capital": 11530,
    "total_return": 15.3,
    "annualized_return": 18.2,
    "max_drawdown": -8.2,
    "sharpe_ratio": 1.8,
    "sortino_ratio": 2.1,
    "calmar_ratio": 2.2,
    "win_rate": 0.72,
    "profit_factor": 1.62,
    "total_trades": 150,
    "winning_trades": 108,
    "losing_trades": 42,
    "avg_win": 0.025,
    "avg_loss": -0.015,
    "largest_win": 0.08,
    "largest_loss": -0.04
  },
  "equity_curve": [
    {
      "date": "2025-01-01",
      "equity": 10000
    }
  ],
  "monthly_returns": [
    {
      "month": "2025-01",
      "return": 2.1
    }
  ]
}
```

### Уведомления

#### GET /notifications
Получение списка уведомлений

```bash
curl -X GET "https://api.cryptoanalytics.com/v1/notifications?limit=50&offset=0" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Ответ:**
```json
{
  "notifications": [
    {
      "id": 123,
      "type": "signal_alert",
      "title": "New signal from Crypto Signals Pro",
      "message": "BUY BTC/USDT at 45000",
      "data": {
        "signal_id": 12345,
        "channel_id": 1,
        "pair": "BTC/USDT",
        "type": "BUY",
        "price": 45000.0
      },
      "read": false,
      "created_at": "2025-08-16T10:00:00Z"
    }
  ],
  "pagination": {
    "total": 150,
    "page": 1,
    "per_page": 50,
    "pages": 3
  }
}
```

#### POST /notifications/webhook
Настройка webhook уведомлений

```bash
curl -X POST "https://api.cryptoanalytics.com/v1/notifications/webhook" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-server.com/webhook",
    "events": ["signal_created", "signal_completed"],
    "secret": "your_webhook_secret"
  }'
```

### Экспорт данных

#### GET /export/signals
Экспорт сигналов в различных форматах

```bash
curl -X GET "https://api.cryptoanalytics.com/v1/export/signals?format=csv&date_from=2025-08-01&date_to=2025-08-16" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Поддерживаемые форматы:**
- `csv` - CSV файл
- `json` - JSON файл
- `excel` - Excel файл (.xlsx)

## 📊 Rate Limiting

Pro пользователи имеют следующие лимиты:

- **Запросы в минуту:** 1000
- **Запросы в час:** 10000
- **Запросы в день:** 100000

При превышении лимитов возвращается статус `429 Too Many Requests`.

## 🔒 Безопасность

### HTTPS
Все API запросы должны выполняться через HTTPS.

### API Key Rotation
Рекомендуется регулярно обновлять API ключи (каждые 90 дней).

### IP Whitelist
Можно настроить whitelist IP адресов для дополнительной безопасности.

## 📝 Примеры использования

### Python

```python
import requests
import json

class CryptoAnalyticsAPI:
    def __init__(self, api_key, base_url="https://api.cryptoanalytics.com/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def get_signals(self, **params):
        response = requests.get(
            f"{self.base_url}/signals",
            headers=self.headers,
            params=params
        )
        return response.json()
    
    def get_ml_prediction(self, signal_data):
        response = requests.post(
            f"{self.base_url}/ml/predict",
            headers=self.headers,
            json=signal_data
        )
        return response.json()
    
    def export_signals(self, format="csv", **params):
        response = requests.get(
            f"{self.base_url}/export/signals",
            headers=self.headers,
            params={"format": format, **params}
        )
        return response.content

# Использование
api = CryptoAnalyticsAPI("YOUR_API_KEY")

# Получение сигналов
signals = api.get_signals(channel_id=1, type="BUY", limit=50)

# ML предсказание
prediction = api.get_ml_prediction({
    "pair": "BTC/USDT",
    "type": "BUY",
    "price": 45000.0,
    "target": 46000.0,
    "stop_loss": 44000.0
})

# Экспорт данных
csv_data = api.export_signals(format="csv", date_from="2025-08-01")
```

### JavaScript

```javascript
class CryptoAnalyticsAPI {
    constructor(apiKey, baseUrl = "https://api.cryptoanalytics.com/v1") {
        this.apiKey = apiKey;
        this.baseUrl = baseUrl;
        this.headers = {
            "Authorization": `Bearer ${apiKey}`,
            "Content-Type": "application/json"
        };
    }
    
    async getSignals(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const response = await fetch(`${this.baseUrl}/signals?${queryString}`, {
            headers: this.headers
        });
        return response.json();
    }
    
    async getMLPrediction(signalData) {
        const response = await fetch(`${this.baseUrl}/ml/predict`, {
            method: "POST",
            headers: this.headers,
            body: JSON.stringify(signalData)
        });
        return response.json();
    }
    
    async exportSignals(format = "csv", params = {}) {
        const queryString = new URLSearchParams({format, ...params}).toString();
        const response = await fetch(`${this.baseUrl}/export/signals?${queryString}`, {
            headers: this.headers
        });
        return response.blob();
    }
}

// Использование
const api = new CryptoAnalyticsAPI("YOUR_API_KEY");

// Получение сигналов
const signals = await api.getSignals({channel_id: 1, type: "BUY", limit: 50});

// ML предсказание
const prediction = await api.getMLPrediction({
    pair: "BTC/USDT",
    type: "BUY",
    price: 45000.0,
    target: 46000.0,
    stop_loss: 44000.0
});

// Экспорт данных
const csvBlob = await api.exportSignals("csv", {date_from: "2025-08-01"});
```

## 🚨 Обработка ошибок

### Коды ошибок

- `400 Bad Request` - Неверный запрос
- `401 Unauthorized` - Неверный API ключ
- `403 Forbidden` - Недостаточно прав
- `404 Not Found` - Ресурс не найден
- `429 Too Many Requests` - Превышен лимит запросов
- `500 Internal Server Error` - Внутренняя ошибка сервера

### Пример ответа с ошибкой

```json
{
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "Invalid parameter: min_accuracy must be between 0 and 100",
    "details": {
      "parameter": "min_accuracy",
      "value": 150,
      "constraints": {
        "min": 0,
        "max": 100
      }
    }
  }
}
```

## 📞 Поддержка

Для получения поддержки по API:

- **Email:** api-support@cryptoanalytics.com
- **Документация:** https://docs.cryptoanalytics.com/api
- **Status Page:** https://status.cryptoanalytics.com
- **Reddit:** https://reddit.com/r/cryptocurrency

## 🔄 Changelog

### v1.2.0 (2025-08-16)
- Добавлен endpoint для backtesting
- Улучшена ML аналитика
- Добавлена поддержка webhook уведомлений

### v1.1.0 (2025-07-01)
- Добавлен экспорт данных
- Улучшена фильтрация сигналов
- Добавлена аналитика портфеля

### v1.0.0 (2025-06-01)
- Первоначальный релиз API
- Базовые endpoints для сигналов и каналов
- ML предсказания
