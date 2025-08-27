import urllib.request
import json
import re

def debug_channel_content(username):
    """Отладочная функция для проверки содержимого канала"""
    print(f"🔍 Отладка канала: {username}")
    print("=" * 50)
    
    try:
        url = f"https://t.me/s/{username}"
        print(f"URL: {url}")
        
        opener = urllib.request.build_opener()
        opener.addheaders = [
            ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        ]
        
        with opener.open(url, timeout=10) as response:
            content = response.read().decode('utf-8')
            
            print(f"Статус ответа: {response.status}")
            print(f"Размер контента: {len(content)} символов")
            
            # Проверяем, есть ли признаки приватного канала
            if "This channel is private" in content:
                print("❌ Канал приватный")
                return False
            
            if "This group is private" in content:
                print("❌ Группа приватная")
                return False
            
            if "Channel not found" in content:
                print("❌ Канал не найден")
                return False
            
            # Ищем сообщения
            message_count = len(re.findall(r'class="tgme_widget_message', content))
            print(f"Найдено блоков сообщений: {message_count}")
            
            # Ищем текст сообщений
            text_blocks = len(re.findall(r'class="tgme_widget_message_text', content))
            print(f"Найдено блоков текста: {text_blocks}")
            
            # Показываем первые 1000 символов контента
            print(f"\nПервые 1000 символов контента:")
            print("-" * 30)
            print(content[:1000])
            print("-" * 30)
            
            # Ищем любые упоминания криптовалют
            crypto_patterns = [
                r'BTC', r'ETH', r'SOL', r'BNB', r'XRP', r'DOGE', r'DOT', r'ADA', r'MATIC'
            ]
            
            found_crypto = []
            for pattern in crypto_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    found_crypto.extend(matches)
            
            if found_crypto:
                print(f"\nНайдены упоминания криптовалют: {list(set(found_crypto))}")
            else:
                print(f"\nКриптовалюты не найдены")
            
            return True
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def main():
    """Основная функция"""
    print("🚀 ОТЛАДКА TELEGRAM КАНАЛОВ")
    print("=" * 60)
    
    # Список каналов для проверки
    channels = [
        "signalsbitcoinandethereum",
        "CryptoCapoTG",
        "cryptosignals",
        "binance_signals",
        "crypto_analytics"
    ]
    
    results = {}
    
    for username in channels:
        print(f"\n{'='*60}")
        success = debug_channel_content(username)
        results[username] = {
            "accessible": success,
            "checked_at": "2025-01-23"
        }
        
        if not success:
            print(f"💡 Рекомендация: Проверьте канал вручную на https://t.me/{username}")
    
    # Сохраняем результаты
    with open('debug_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print("📊 ИТОГИ ОТЛАДКИ:")
    
    accessible = [k for k, v in results.items() if v['accessible']]
    inaccessible = [k for k, v in results.items() if not v['accessible']]
    
    print(f"Доступных каналов: {len(accessible)}")
    print(f"Недоступных каналов: {len(inaccessible)}")
    
    if accessible:
        print(f"\n✅ Доступные каналы:")
        for channel in accessible:
            print(f"  - {channel}")
    
    if inaccessible:
        print(f"\n❌ Недоступные каналы:")
        for channel in inaccessible:
            print(f"  - {channel}")
    
    print(f"\n💾 Результаты сохранены в debug_results.json")

if __name__ == "__main__":
    main()
