import urllib.request
import json
import re
from datetime import datetime

def debug_messages():
    """Отладочный парсер для анализа сообщений"""
    
    opener = urllib.request.build_opener()
    opener.addheaders = [
        ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    ]
    
    username = 'CryptoCapoTG'
    url = f"https://t.me/s/{username}"
    
    print(f"🔍 Анализ сообщений канала: {username}")
    
    try:
        with opener.open(url, timeout=15) as response:
            content = response.read().decode('utf-8')
            
            # Извлекаем сообщения
            message_pattern = r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>'
            matches = re.findall(message_pattern, content, re.DOTALL)
            
            print(f"📝 Найдено {len(matches)} сообщений")
            
            # Анализируем первые 10 сообщений
            for i, text_html in enumerate(matches[:10]):
                # Очищаем HTML
                text = re.sub(r'<[^>]+>', '', text_html)
                text = re.sub(r'&nbsp;', ' ', text)
                text = re.sub(r'&amp;', '&', text)
                text = re.sub(r'&#036;', '$', text)
                text = re.sub(r'&#39;', "'", text)
                text = text.strip()
                
                if text and len(text) > 10:
                    print(f"\n📄 Сообщение {i+1}:")
                    print(f"   Текст: {text[:300]}...")
                    
                    # Ищем криптовалюты
                    crypto_patterns = [r'\$(\w+)', r'(\w+)\s+update', r'(\w+)\s+target']
                    found_crypto = []
                    for pattern in crypto_patterns:
                        matches_crypto = re.findall(pattern, text, re.IGNORECASE)
                        found_crypto.extend(matches_crypto)
                    
                    if found_crypto:
                        print(f"   💰 Найдены криптовалюты: {list(set(found_crypto))}")
                    
                    # Ищем направления
                    direction_patterns = [r'(LONG|SHORT|BUY|SELL)', r'(bullish|bearish)', r'(pump|dump)']
                    found_directions = []
                    for pattern in direction_patterns:
                        matches_dir = re.findall(pattern, text, re.IGNORECASE)
                        found_directions.extend(matches_dir)
                    
                    if found_directions:
                        print(f"   📈 Найдены направления: {list(set(found_directions))}")
                    
                    # Ищем цены
                    price_patterns = [r'\$([\d,]+\.?\d*)', r'(\d+\.?\d*)\s*k', r'(\d+\.?\d*)\s*%']
                    found_prices = []
                    for pattern in price_patterns:
                        matches_price = re.findall(pattern, text, re.IGNORECASE)
                        found_prices.extend(matches_price)
                    
                    if found_prices:
                        print(f"   💵 Найдены цены: {list(set(found_prices))}")
                    
                    # Пробуем найти сигналы
                    signal_patterns = [
                        r'(\w+)\s+(LONG|SHORT)\s+\$?([\d,]+\.?\d*)',
                        r'(\w+)\s+(BUY|SELL)\s+\$?([\d,]+\.?\d*)',
                        r'\$(\w+)\s+(LONG|SHORT|BUY|SELL)',
                        r'(\w+)\s+(LONG|SHORT|BUY|SELL)\s+update',
                    ]
                    
                    for pattern in signal_patterns:
                        signal_matches = re.finditer(pattern, text, re.IGNORECASE)
                        for match in signal_matches:
                            print(f"   🎯 НАЙДЕН СИГНАЛ: {match.groups()}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    debug_messages()
