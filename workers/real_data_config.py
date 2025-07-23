# Enhanced configuration for real data integration
# API keys and channel configurations from analyst_crypto project

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

# Enhanced Telegram channel configurations with metadata
REAL_TELEGRAM_CHANNELS = [
    {
        "username": "@cryptosignals",
        "name": "Crypto Signals Pro",
        "category": "premium",
        "confidence_multiplier": 1.2,
        "active": True,
        "priority": 1,
        "languages": ["en"],
        "signal_types": ["spot", "futures"],
        "avg_signals_per_day": 15,
        "success_rate": 0.72
    },
    {
        "username": "@binancesignals", 
        "name": "Binance Trading Signals",
        "category": "exchange_specific",
        "confidence_multiplier": 1.1,
        "active": True,
        "priority": 2,
        "languages": ["en"],
        "signal_types": ["spot", "futures"],
        "avg_signals_per_day": 20,
        "success_rate": 0.68
    },
    {
        "username": "@cryptotradingview",
        "name": "Crypto TradingView Analysis", 
        "category": "analysis",
        "confidence_multiplier": 1.0,
        "active": True,
        "priority": 3,
        "languages": ["en"],
        "signal_types": ["spot", "analysis"],
        "avg_signals_per_day": 8,
        "success_rate": 0.65
    },
    {
        "username": "@cryptowhales",
        "name": "Crypto Whales Signals",
        "category": "whale_tracking",
        "confidence_multiplier": 1.15,
        "active": True,
        "priority": 2,
        "languages": ["en"],
        "signal_types": ["spot", "whale_moves"],
        "avg_signals_per_day": 12,
        "success_rate": 0.70
    },
    {
        "username": "@bitcoinsignals",
        "name": "Bitcoin Trading Signals",
        "category": "btc_focused",
        "confidence_multiplier": 1.05,
        "active": True,
        "priority": 3,
        "languages": ["en"],
        "signal_types": ["spot", "futures"],
        "avg_signals_per_day": 10,
        "success_rate": 0.63
    },
    {
        "username": "@altcoinsignals",
        "name": "Altcoin Trading Hub",
        "category": "altcoins",
        "confidence_multiplier": 0.95,
        "active": True,
        "priority": 4,
        "languages": ["en"],
        "signal_types": ["spot"],
        "avg_signals_per_day": 25,
        "success_rate": 0.58
    },
    {
        "username": "@defitrading",
        "name": "DeFi Trading Signals",
        "category": "defi",
        "confidence_multiplier": 0.9,
        "active": True,
        "priority": 4,
        "languages": ["en"],
        "signal_types": ["spot", "defi"],
        "avg_signals_per_day": 18,
        "success_rate": 0.55
    }
]

# Enhanced cryptocurrency symbols with metadata
CRYPTO_SYMBOLS = [
    # Major cryptocurrencies (Tier 1)
    "BTCUSDT",    # Bitcoin
    "ETHUSDT",    # Ethereum
    "BNBUSDT",    # Binance Coin
    
    # Large cap altcoins (Tier 2)
    "ADAUSDT",    # Cardano
    "XRPUSDT",    # Ripple
    "SOLUSDT",    # Solana
    "DOGEUSDT",   # Dogecoin
    "DOTUSDT",    # Polkadot
    "AVAXUSDT",   # Avalanche
    "LINKUSDT",   # Chainlink
    "MATICUSDT",  # Polygon
    "LTCUSDT",    # Litecoin
    "UNIUSDT",    # Uniswap
    "ATOMUSDT",   # Cosmos
    
    # Mid cap altcoins (Tier 3)
    "VETUSDT",    # VeChain
    "FILUSDT",    # Filecoin
    "TRXUSDT",    # Tron
    "ETCUSDT",    # Ethereum Classic
    "XLMUSDT",    # Stellar
    "ALGOUSDT",   # Algorand
    "HBARUSDT",   # Hedera
    "EGLDUSDT",   # MultiversX
    "SANDUSDT",   # The Sandbox
    "MANAUSDT",   # Decentraland
    
    # DeFi tokens
    "AAVEUSDT",   # Aave
    "COMPUSDT",   # Compound
    "MKRUSDT",    # Maker
    "SUSHIUSDT",  # SushiSwap
    "CRVUSDT",    # Curve
    "1INCHUSDT",  # 1inch
    
    # Layer 2 and scaling
    "OPUSDT",     # Optimism
    "ARBUSDT",    # Arbitrum
    "IMXUSDT",    # Immutable X
    
    # Meme coins (high volatility)
    "SHIBUSDT",   # Shiba Inu
    "PEPEUSDT",   # Pepe
    "FLOKIUSDT",  # Floki
]

# Symbol metadata for enhanced analysis
SYMBOL_METADATA = {
    "BTCUSDT": {
        "tier": 1,
        "category": "store_of_value",
        "volatility": "medium",
        "liquidity": "very_high",
        "market_cap_rank": 1
    },
    "ETHUSDT": {
        "tier": 1,
        "category": "smart_contract",
        "volatility": "medium",
        "liquidity": "very_high", 
        "market_cap_rank": 2
    },
    "ADAUSDT": {
        "tier": 2,
        "category": "smart_contract",
        "volatility": "high",
        "liquidity": "high",
        "market_cap_rank": 8
    },
    "SOLUSDT": {
        "tier": 2,
        "category": "smart_contract",
        "volatility": "very_high",
        "liquidity": "high",
        "market_cap_rank": 5
    },
    "DOGEUSDT": {
        "tier": 2,
        "category": "meme",
        "volatility": "very_high",
        "liquidity": "medium",
        "market_cap_rank": 10
    }
}

# Trading pair preferences by channel type
CHANNEL_PAIR_PREFERENCES = {
    "premium": ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "SOLUSDT"],
    "exchange_specific": ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "XRPUSDT", "DOGEUSDT"],
    "analysis": ["BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT", "LINKUSDT"],
    "whale_tracking": ["BTCUSDT", "ETHUSDT", "BNBUSDT", "UNIUSDT", "AAVEUSDT"],
    "btc_focused": ["BTCUSDT"],
    "altcoins": ["ADAUSDT", "SOLUSDT", "DOTUSDT", "LINKUSDT", "MATICUSDT", "VETUSDT"],
    "defi": ["ETHUSDT", "UNIUSDT", "AAVEUSDT", "COMPUSDT", "MKRUSDT", "SUSHIUSDT"]
}

# Enhanced parsing settings
PARSE_INTERVAL_MINUTES = 5  # Interval for parsing messages
MAX_MESSAGES_PER_CHANNEL = 100  # Maximum messages to fetch per channel
SIGNAL_CONFIDENCE_THRESHOLD = 0.7  # Minimum confidence for signal acceptance

# Signal processing settings
SIGNAL_PROCESSING_CONFIG = {
    "min_entry_price": 0.000001,  # Minimum valid entry price
    "max_entry_price": 1000000,   # Maximum valid entry price
    "min_target_distance": 0.01,  # Minimum 1% distance for targets
    "max_target_distance": 0.50,  # Maximum 50% distance for targets
    "min_sl_distance": 0.005,     # Minimum 0.5% distance for stop loss
    "max_sl_distance": 0.20,      # Maximum 20% distance for stop loss
    "max_leverage": 20,           # Maximum allowed leverage
    "signal_expiry_hours": 48,    # Hours after which signal expires
    "duplicate_detection_window": 3600,  # Seconds to check for duplicates
}

# Rate limiting settings
RATE_LIMITING_CONFIG = {
    "telegram_requests_per_minute": 20,
    "bybit_requests_per_second": 10,
    "binance_requests_per_second": 20,
    "max_concurrent_requests": 5,
    "request_timeout_seconds": 30,
    "retry_attempts": 3,
    "backoff_multiplier": 2.0
}

# Cache settings
CACHE_CONFIG = {
    "price_cache_ttl": 30,        # Price cache TTL in seconds
    "signal_cache_ttl": 300,      # Signal cache TTL in seconds  
    "channel_cache_ttl": 3600,    # Channel data cache TTL
    "max_cache_size": 1000,       # Maximum cache entries
    "cache_cleanup_interval": 600 # Cache cleanup interval in seconds
}

# Monitoring and alerting
MONITORING_CONFIG = {
    "health_check_interval": 60,  # Health check interval in seconds
    "max_consecutive_failures": 5, # Max failures before marking unhealthy
    "alert_on_low_signals": True,  # Alert if signal rate drops
    "min_signals_per_hour": 2,     # Minimum expected signals per hour
    "performance_tracking": True,   # Enable performance metrics
    "log_level": "INFO"            # Logging level
}

# Channel validation function
def validate_channel_config(channel_config: dict) -> bool:
    """Validate a channel configuration"""
    required_fields = ["username", "name", "category", "active"]
    
    for field in required_fields:
        if field not in channel_config:
            return False
    
    # Validate category
    valid_categories = ["premium", "exchange_specific", "analysis", "whale_tracking", 
                       "btc_focused", "altcoins", "defi"]
    if channel_config["category"] not in valid_categories:
        return False
    
    # Validate confidence multiplier
    confidence_mult = channel_config.get("confidence_multiplier", 1.0)
    if not 0.5 <= confidence_mult <= 2.0:
        return False
    
    return True

# Get active channels
def get_active_channels():
    """Get list of active channel configurations"""
    return [ch for ch in REAL_TELEGRAM_CHANNELS if ch.get("active", False)]

# Get channels by category
def get_channels_by_category(category: str):
    """Get channels filtered by category"""
    return [ch for ch in REAL_TELEGRAM_CHANNELS 
            if ch.get("category") == category and ch.get("active", False)]

# Get preferred symbols for channel
def get_channel_preferred_symbols(channel_category: str):
    """Get preferred trading symbols for a channel category"""
    return CHANNEL_PAIR_PREFERENCES.get(channel_category, CRYPTO_SYMBOLS[:10])

# Configuration validation
def validate_configuration():
    """Validate the entire configuration"""
    errors = []
    
    # Validate channels
    for i, channel in enumerate(REAL_TELEGRAM_CHANNELS):
        if not validate_channel_config(channel):
            errors.append(f"Invalid channel config at index {i}: {channel.get('username', 'unknown')}")
    
    # Validate symbols
    if len(CRYPTO_SYMBOLS) < 5:
        errors.append("Too few crypto symbols configured")
    
    # Validate thresholds
    if not 0.1 <= SIGNAL_CONFIDENCE_THRESHOLD <= 1.0:
        errors.append("Invalid signal confidence threshold")
    
    return errors

# Run validation on import
_validation_errors = validate_configuration()
if _validation_errors:
    print("Configuration validation warnings:")
    for error in _validation_errors:
        print(f"  - {error}")
else:
    print("✅ Configuration validation passed") 