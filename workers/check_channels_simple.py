import requests
import json
from datetime import datetime

def check_channel_availability():
    """Проверяет доступность каналов через веб-интерфейс"""
    print("🔍 Проверка доступности Telegram каналов...")
    
    # Список каналов для проверки
    channels = [
        "signalsbitcoinandethereum",
        "CryptoCapoTG", 
        "cryptosignals",
        "binance_signals",
        "crypto_analytics",
        "bitcoin_analysis",
        "ethereum_signals",
        "trading_signals_pro",
        "crypto_insights",
        "altcoin_signals",
        "defi_signals",
        "crypto_trading_pro",
        "market_analysis",
        "crypto_alerts",
        "binance_signals"
    ]
    
    accessible_channels = []
    inaccessible_channels = []
    
    for username in channels:
        try:
            print(f"🔍 Проверка: {username}")
            
            # Пытаемся получить информацию о канале через веб-интерфейс
            url = f"https://t.me/{username}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                # Проверяем, есть ли признаки приватного канала
                if "This channel is private" in response.text or "This group is private" in response.text:
                    print(f"❌ {username} - приватный канал")
                    inaccessible_channels.append({
                        "username": username,
                        "error": "Приватный канал",
                        "accessible": False
                    })
                else:
                    print(f"✅ {username} - доступен")
                    accessible_channels.append({
                        "username": username,
                        "accessible": True,
                        "url": url
                    })
            else:
                print(f"❌ {username} - недоступен (код: {response.status_code})")
                inaccessible_channels.append({
                    "username": username,
                    "error": f"HTTP {response.status_code}",
                    "accessible": False
                })
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {username} - ошибка сети: {e}")
            inaccessible_channels.append({
                "username": username,
                "error": f"Ошибка сети: {e}",
                "accessible": False
            })
        except Exception as e:
            print(f"❌ {username} - ошибка: {e}")
            inaccessible_channels.append({
                "username": username,
                "error": str(e),
                "accessible": False
            })
    
    return accessible_channels, inaccessible_channels

def suggest_alternative_channels():
    """Предлагает альтернативные каналы"""
    print("\n📋 АЛЬТЕРНАТИВНЫЕ КАНАЛЫ ДЛЯ ПРОВЕРКИ:")
    
    alternative_channels = [
        "binance_signals_official",
        "coinbase_signals", 
        "kraken_signals",
        "crypto_signals_daily",
        "bitcoin_signals",
        "ethereum_signals_daily",
        "altcoin_signals_pro",
        "defi_signals_daily",
        "trading_signals_24_7",
        "crypto_analytics_pro",
        "market_signals",
        "price_alerts",
        "crypto_news_signals",
        "technical_analysis_signals",
        "fundamental_analysis_signals"
    ]
    
    for i, channel in enumerate(alternative_channels, 1):
        print(f"  {i:2d}. {channel}")
    
    return alternative_channels

def main():
    """Основная функция"""
    print("🚀 ПРОВЕРКА ДОСТУПНОСТИ TELEGRAM КАНАЛОВ")
    print("=" * 60)
    
    # Проверяем доступность каналов
    accessible, inaccessible = check_channel_availability()
    
    print(f"\n📊 РЕЗУЛЬТАТЫ:")
    print(f"Доступных каналов: {len(accessible)}")
    print(f"Недоступных каналов: {len(inaccessible)}")
    
    if accessible:
        print("\n✅ ДОСТУПНЫЕ КАНАЛЫ:")
        for channel in accessible:
            print(f"  - {channel['username']}")
    
    if inaccessible:
        print("\n❌ НЕДОСТУПНЫЕ КАНАЛЫ:")
        for channel in inaccessible:
            print(f"  - {channel['username']}: {channel['error']}")
    
    # Предлагаем альтернативы
    alternatives = suggest_alternative_channels()
    
    # Сохраняем результаты
    results = {
        "check_time": datetime.now().isoformat(),
        "accessible_channels": accessible,
        "inaccessible_channels": inaccessible,
        "alternative_channels": alternatives,
        "total_accessible": len(accessible),
        "total_inaccessible": len(inaccessible),
        "total_alternatives": len(alternatives)
    }
    
    with open('channel_availability_check.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Результаты сохранены в channel_availability_check.json")
    
    if accessible:
        print(f"\n🎯 РЕКОМЕНДАЦИИ:")
        print(f"1. Доступно каналов: {len(accessible)}")
        print(f"2. Можно попробовать парсить эти каналы")
        print(f"3. Для приватных каналов нужна подписка")
    else:
        print(f"\n⚠️ ПРОБЛЕМЫ:")
        print(f"1. Нет доступных каналов из списка")
        print(f"2. Нужно подписаться на каналы или найти другие")
        print(f"3. Проверьте альтернативные каналы из списка выше")

if __name__ == "__main__":
    main()
