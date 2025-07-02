-- Создание базы данных
CREATE DATABASE crypto_analytics;

-- Подключение к базе данных
\c crypto_analytics;

-- Создание таблицы для каналов
CREATE TABLE IF NOT EXISTS channels (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    platform VARCHAR(50) NOT NULL,
    url VARCHAR(255) NOT NULL UNIQUE,
    category VARCHAR(50),
    description TEXT,
    accuracy FLOAT,
    signals_count INTEGER DEFAULT 0,
    successful_signals INTEGER DEFAULT 0,
    average_roi FLOAT,
    max_drawdown FLOAT,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Создание индексов для таблицы каналов
CREATE INDEX idx_channels_platform ON channels(platform);
CREATE INDEX idx_channels_category ON channels(category);
CREATE INDEX idx_channels_accuracy ON channels(accuracy);

-- Создание перечислений для сигналов
CREATE TYPE signal_direction AS ENUM ('BUY', 'SELL');
CREATE TYPE signal_status AS ENUM ('PENDING', 'SUCCESSFUL', 'FAILED', 'CANCELLED');

-- Создание таблицы для сигналов
CREATE TABLE IF NOT EXISTS signals (
    id SERIAL PRIMARY KEY,
    channel_id INTEGER NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
    asset VARCHAR(20) NOT NULL,
    direction signal_direction NOT NULL,
    entry_price FLOAT NOT NULL,
    target_price FLOAT,
    stop_loss FLOAT,
    original_text TEXT,
    message_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status signal_status DEFAULT 'PENDING',
    exit_price FLOAT,
    exit_timestamp TIMESTAMP WITH TIME ZONE,
    profit_loss FLOAT,
    ml_success_probability FLOAT,
    is_ml_prediction_correct BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Создание индексов для таблицы сигналов
CREATE INDEX idx_signals_channel_id ON signals(channel_id);
CREATE INDEX idx_signals_asset ON signals(asset);
CREATE INDEX idx_signals_status ON signals(status);
CREATE INDEX idx_signals_message_timestamp ON signals(message_timestamp);

-- Создание таблицы для пользователей
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    subscription_tier VARCHAR(20) DEFAULT 'FREE',
    subscription_expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Создание индексов для таблицы пользователей
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_subscription_tier ON users(subscription_tier);

-- Создание таблицы для избранных каналов пользователей
CREATE TABLE IF NOT EXISTS user_favorite_channels (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    channel_id INTEGER NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (user_id, channel_id)
);

-- Создание таблицы для API ключей пользователей
CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key_name VARCHAR(255) NOT NULL,
    api_key VARCHAR(255) NOT NULL UNIQUE,
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Создание индекса для таблицы API ключей
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_api_key ON api_keys(api_key);

-- Добавление тестовых данных для каналов
INSERT INTO channels (name, platform, url, category, description, accuracy, signals_count, successful_signals)
VALUES 
    ('CryptoMaster', 'telegram', 'https://t.me/cryptomaster', 'crypto', 'Leading crypto signals channel', 78.5, 342, 268),
    ('BinanceKillers', 'telegram', 'https://t.me/binancekillers', 'crypto', 'Professional crypto trading signals', 82.1, 256, 210),
    ('CryptoSignals', 'telegram', 'https://t.me/cryptosignals', 'crypto', 'Daily crypto signals and analysis', 65.8, 189, 124);

-- Добавление тестовых данных для сигналов
INSERT INTO signals (channel_id, asset, direction, entry_price, target_price, stop_loss, status, profit_loss)
VALUES 
    (1, 'BTC/USDT', 'BUY', 50000.0, 55000.0, 48000.0, 'SUCCESSFUL', 10.0),
    (1, 'ETH/USDT', 'BUY', 3000.0, 3300.0, 2800.0, 'SUCCESSFUL', 10.0),
    (2, 'BTC/USDT', 'SELL', 60000.0, 55000.0, 62000.0, 'FAILED', -3.3),
    (3, 'SOL/USDT', 'BUY', 100.0, 120.0, 90.0, 'PENDING', NULL); 