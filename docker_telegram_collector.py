#!/usr/bin/env python3
"""
Сбор РЕАЛЬНЫХ данных через Docker контейнер
Обходит проблемы с виртуальным окружением
"""
import os
import sqlite3
import json
import re
from datetime import datetime, timezone
from pathlib import Path

def load_env():
    """Загружает данные из .env файла"""
    env_path = Path('.env')
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        print("✅ Данные из .env загружены")

def create_dockerfile():
    """Создает Dockerfile для сбора данных"""
    dockerfile_content = '''
FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
RUN pip install telethon requests

# Копирование скрипта
COPY telegram_collector.py .

# Переменные окружения
ENV TELEGRAM_API_ID=${TELEGRAM_API_ID}
ENV TELEGRAM_API_HASH=${TELEGRAM_API_HASH}

# Запуск сборщика
CMD ["python", "telegram_collector.py"]
'''
    
    with open('Dockerfile.collector', 'w') as f:
        f.write(dockerfile_content)
    
    print("✅ Dockerfile создан")

def create_telegram_collector():
    """Создает скрипт для сбора данных"""
    collector_content = '''
#!/usr/bin/env python3
"""
Сборщик РЕАЛЬНЫХ данных из Telegram
Запускается в Docker контейнере
"""
import os
import asyncio
import json
import re
from datetime import datetime, timezone
from telethon import TelegramClient

# Каналы для сбора
CHANNELS = [
    'CryptoPapa', 'FatPigSignals', 'WallstreetQueenOfficial',
    'RocketWalletSignals', 'BinanceKiller', 'WolfOfTrading'
]

async def collect_signals():
    """Собирает сигналы из Telegram"""
    api_id = os.environ.get('TELEGRAM_API_ID')
    api_hash = os.environ.get('TELEGRAM_API_HASH')
    
    if not api_id or not api_hash:
        print("❌ API данные не настроены")
        return []
    
    client = TelegramClient('session', api_id, api_hash)
    
    try:
        await client.start()
        print("✅ Подключение к Telegram успешно")
        
        signals = []
        
        for channel in CHANNELS:
            try:
                print(f"📊 Сбор из {channel}...")
                entity = await client.get_entity(channel)
                messages = await client.get_messages(entity, limit=50)
                
                for msg in messages:
                    if msg.text:
                        signal = extract_signal(msg.text, channel)
                        if signal:
                            signals.append(signal)
                
            except Exception as e:
                print(f"❌ Ошибка сбора из {channel}: {e}")
        
        await client.disconnect()
        return signals
        
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return []

def extract_signal(text, channel):
    """Извлекает сигнал из текста"""
    # Простые паттерны для извлечения
    patterns = [
        r'BTC.*?(\\d{4,6}).*?(\\d{4,6})',
        r'ETH.*?(\\d{3,5}).*?(\\d{3,5})',
        r'SOL.*?(\\d{2,4}).*?(\\d{2,4})'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text.upper())
        for match in matches:
            if len(match) == 2:
                try:
                    entry = float(match[0])
                    target = float(match[1])
                    
                    if entry > 0 and target > 0:
                        return {
                            'asset': 'BTC' if 'BTC' in text.upper() else 'ETH' if 'ETH' in text.upper() else 'SOL',
                            'entry_price': entry,
                            'target_price': target,
                            'direction': 'LONG' if target > entry else 'SHORT',
                            'channel': channel,
                            'timestamp': datetime.now(timezone.utc).isoformat()
                        }
                except:
                    continue
    
    return None

async def main():
    """Основная функция"""
    print("🚀 Сбор РЕАЛЬНЫХ данных из Telegram...")
    
    signals = await collect_signals()
    
    print(f"✅ Собрано {len(signals)} сигналов")
    
    # Сохраняем в JSON
    with open('/app/signals.json', 'w') as f:
        json.dump(signals, f, indent=2)
    
    print("💾 Данные сохранены в signals.json")

if __name__ == '__main__':
    asyncio.run(main())
'''
    
    with open('telegram_collector.py', 'w') as f:
        f.write(collector_content)
    
    print("✅ Скрипт сборщика создан")

def create_docker_commands():
    """Создает команды для Docker"""
    commands = '''
# Команды для запуска в PowerShell:

# 1. Создать образ
docker build -f Dockerfile.collector -t telegram-collector .

# 2. Запустить контейнер
docker run --rm -v ${PWD}:/app telegram-collector

# 3. Проверить результат
docker run --rm -v ${PWD}:/app telegram-collector cat /app/signals.json
'''
    
    with open('docker_commands.txt', 'w') as f:
        f.write(commands)
    
    print("✅ Команды Docker созданы")

def main():
    """Основная функция"""
    print("🔧 СОЗДАНИЕ DOCKER РЕШЕНИЯ")
    print("=" * 40)
    
    # Загружаем данные из .env
    load_env()
    
    # Создаем файлы
    create_dockerfile()
    create_telegram_collector()
    create_docker_commands()
    
    print("\n🎉 Готово!")
    print("\nСледующие шаги:")
    print("1. Откройте PowerShell")
    print("2. Выполните команды из docker_commands.txt")
    print("3. Получите РЕАЛЬНЫЕ данные из Telegram")

if __name__ == '__main__':
    main()
