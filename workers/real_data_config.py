# Конфигурация для интеграции реальных данных
# API ключи из проекта analyst_crypto

# Telegram API Configuration
TELEGRAM_API_ID = 21073808
TELEGRAM_API_HASH = "2e3adb8940912dd295fe20c1d2ce5368"
TELEGRAM_BOT_TOKEN = "7926974097:AAEsGt_YQxp_o7TdbkyYUjQo2hCHw3DPSAw"

# Reddit API Configuration
REDDIT_CLIENT_ID = "unyb6-1Dn5-Z_ZPZasRtaw"
REDDIT_CLIENT_SECRET = "kJz3lMVPlnpzRzsxBvcoq2zzOF03w"
REDDIT_REDIRECT_URI = "http://localhost:8000"
REDDIT_USER_AGENT = "crypto app by /u/Ksantor1981"

# Bybit API Configuration
BYBIT_API_KEY = "PfKXE4pNT9CGTAFqoa"
BYBIT_API_SECRET = "WqBEwhiRWT1rL1URKxfRc60EWr9c88vPxNkP"

# Database Configuration
DATABASE_URL = "sqlite+aiosqlite:///crypto_forecasts.db"

# Backend Configuration
BACKEND_URL = "http://localhost:8000"
ML_SERVICE_URL = "http://localhost:8001"

# Список реальных Telegram каналов для парсинга
REAL_TELEGRAM_CHANNELS = [
    "@cryptosignals",
    "@binancesignals", 
    "@cryptotradingview",
    "@cryptowhales",
    "@bitcoinsignals"
]

# Список криптовалют для мониторинга
CRYPTO_SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT", 
    "ADAUSDT",
    "BNBUSDT",
    "XRPUSDT",
    "SOLUSDT",
    "DOGEUSDT",
    "DOTUSDT",
    "AVAXUSDT",
    "LINKUSDT"
]

# Настройки для парсинга
PARSE_INTERVAL_MINUTES = 5  # Интервал парсинга в минутах
MAX_MESSAGES_PER_CHANNEL = 100  # Максимум сообщений за раз
SIGNAL_CONFIDENCE_THRESHOLD = 0.7  # Порог уверенности для сигналов 