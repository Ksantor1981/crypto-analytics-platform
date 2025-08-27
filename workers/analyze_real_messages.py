import urllib.request
import json
import re
from datetime import datetime

def get_real_messages(username):
    """Получает реальные сообщения из канала"""
    try:
        url = f"https://t.me/s/{username}"
        
        opener = urllib.request.build_opener()
        opener.addheaders = [
            ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        ]
        
        with opener.open(url, timeout=10) as response:
            content = response.read().decode('utf-8')
            
            messages = []
            
            # Ищем все блоки с текстом сообщений
            text_pattern = r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>'
            text_matches = re.findall(text_pattern, content, re.DOTALL)
            
            for i, text_html in enumerate(text_matches):
                # Очищаем HTML
                text = re.sub(r'<[^>]+>', '', text_html)
                text = text.strip()
                
                if text and len(text) > 10:  # Только сообщения с содержанием
                    messages.append({
                        'id': f"{username}_{i+1}",
                        'text': text,
                        'date': datetime.now().isoformat()
                    })
            
            return messages
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return []

def analyze_message_patterns(messages):
    """Анализирует сообщения и ищет паттерны сигналов"""
    print(f"🔍 АНАЛИЗ {len(messages)} СООБЩЕНИЙ")
    print("=" * 60)
    
    # Собираем все возможные паттерны
    all_patterns = []
    
    for i, message in enumerate(messages[:10]):  # Анализируем первые 10
        text = message['text']
        print(f"\n📝 Сообщение {i+1}:")
        print(f"   {text[:200]}...")
        
        # Ищем любые упоминания криптовалют с ценами
        crypto_price_patterns = [
            r'\$(\w+)\s*[=:]\s*\$?([\d,]+\.?\d*)',  # $BTC = $110,500
            r'(\w+)\s*[=:]\s*\$?([\d,]+\.?\d*)',    # BTC = $110,500
            r'\$(\w+)\s*\$?([\d,]+\.?\d*)',         # $BTC $110,500
            r'(\w+)\s*\$?([\d,]+\.?\d*)',           # BTC $110,500
            r'(\w+)/USDT\s*\$?([\d,]+\.?\d*)',      # BTC/USDT $110,500
        ]
        
        for pattern in crypto_price_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                print(f"   ✅ Найдены цены: {matches}")
                all_patterns.extend(matches)
        
        # Ищем торговые термины
        trading_terms = [
            'long', 'short', 'buy', 'sell', 'entry', 'target', 'stop', 'take profit',
            '🚀', '📉', '🔥', '📈', '💎', '🎯', '🛑', '⚡'
        ]
        
        found_terms = []
        for term in trading_terms:
            if term.lower() in text.lower():
                found_terms.append(term)
        
        if found_terms:
            print(f"   🎯 Торговые термины: {found_terms}")
        
        # Ищем проценты
        percent_pattern = r'[+-]?\d+%'
        percents = re.findall(percent_pattern, text)
        if percents:
            print(f"   📊 Проценты: {percents}")
        
        # Ищем числа (возможные цены)
        number_pattern = r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)'
        numbers = re.findall(number_pattern, text)
        if numbers:
            print(f"   💰 Числа (цены): {numbers[:5]}")  # Показываем первые 5
    
    return all_patterns

def search_for_signals(messages):
    """Ищет сигналы с расширенными паттернами"""
    print(f"\n🔍 ПОИСК СИГНАЛОВ В {len(messages)} СООБЩЕНИЯХ")
    print("=" * 60)
    
    signals = []
    
    # Расширенные паттерны для поиска сигналов
    patterns = [
        # Стандартные форматы
        r'(\w+)\s+(LONG|SHORT)\s+\$?([\d,]+\.?\d*)',
        r'(\w+)/USDT\s+(LONG|SHORT)\s+\$?([\d,]+\.?\d*)',
        r'[🚀📉🔥]\s*(\w+)\s+(LONG|SHORT)\s+\$?([\d,]+\.?\d*)',
        
        # Форматы с Entry/Target/Stop
        r'(\w+)\s+(LONG|SHORT)\s+Entry:\s*\$?([\d,]+\.?\d*)',
        r'(\w+)\s+(LONG|SHORT)\s+Target:\s*\$?([\d,]+\.?\d*)',
        r'(\w+)\s+(LONG|SHORT)\s+Stop:\s*\$?([\d,]+\.?\d*)',
        
        # Форматы с эмодзи
        r'🚀\s*(\w+)\s+\$?([\d,]+\.?\d*)',
        r'📉\s*(\w+)\s+\$?([\d,]+\.?\d*)',
        r'🔥\s*(\w+)\s+\$?([\d,]+\.?\d*)',
        
        # Форматы с процентами
        r'(\w+)\s+(LONG|SHORT)\s+[+-]\d+%\s+\$?([\d,]+\.?\d*)',
        
        # Простые форматы с ценами
        r'(\w+)\s+\$?([\d,]+\.?\d*)\s+(LONG|SHORT)',
        r'(\w+)\s+\$?([\d,]+\.?\d*)\s+(BUY|SELL)',
        
        # Форматы с @
        r'(\w+)\s+@\s*\$?([\d,]+\.?\d*)',
        
        # Форматы с точками
        r'(\w+)\.(LONG|SHORT)\.\$?([\d,]+\.?\d*)',
        
        # Форматы с подчеркиваниями
        r'(\w+)_(LONG|SHORT)_\$?([\d,]+\.?\d*)',
    ]
    
    for message in messages:
        text = message['text']
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) >= 2:
                    signal = {
                        "asset": match.group(1).upper(),
                        "direction": match.group(2).upper() if len(match.groups()) >= 3 else "UNKNOWN",
                        "entry_price": float(match.group(len(match.groups())).replace(',', '')),
                        "pattern_used": pattern[:50] + "...",
                        "message_text": text[:100] + "...",
                        "message_id": message['id']
                    }
                    signals.append(signal)
                    print(f"✅ Найден сигнал: {signal['asset']} {signal['direction']} @ ${signal['entry_price']}")
                    print(f"   Паттерн: {signal['pattern_used']}")
                    print(f"   Текст: {signal['message_text']}")
                    print()
    
    return signals

def main():
    """Основная функция"""
    print("🚀 АНАЛИЗ РЕАЛЬНЫХ СООБЩЕНИЙ И ПОИСК СИГНАЛОВ")
    print("=" * 60)
    
    # Анализируем каналы с сообщениями
    channels = [
        "CryptoCapoTG",
        "cryptosignals", 
        "binance_signals"
    ]
    
    all_signals = []
    
    for username in channels:
        print(f"\n{'='*60}")
        print(f"📡 АНАЛИЗ КАНАЛА: {username}")
        print(f"{'='*60}")
        
        messages = get_real_messages(username)
        
        if messages:
            print(f"📊 Найдено {len(messages)} сообщений")
            
            # Анализируем паттерны
            patterns = analyze_message_patterns(messages)
            
            # Ищем сигналы
            signals = search_for_signals(messages)
            
            for signal in signals:
                signal['channel_username'] = username
                all_signals.append(signal)
            
            print(f"🎯 Найдено {len(signals)} сигналов в канале {username}")
        else:
            print(f"❌ Сообщения не найдены")
    
    # Итоговый отчет
    print(f"\n{'='*60}")
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print(f"{'='*60}")
    
    print(f"Всего проанализировано каналов: {len(channels)}")
    print(f"Всего найдено сигналов: {len(all_signals)}")
    
    if all_signals:
        print(f"\n🎯 НАЙДЕННЫЕ СИГНАЛЫ:")
        for i, signal in enumerate(all_signals, 1):
            print(f"  {i}. {signal['asset']} {signal['direction']} @ ${signal['entry_price']}")
            print(f"     Канал: {signal['channel_username']}")
            print(f"     Паттерн: {signal['pattern_used']}")
            print()
        
        # Сохраняем результаты
        results = {
            "success": True,
            "total_signals": len(all_signals),
            "signals": all_signals,
            "analysis_time": datetime.now().isoformat()
        }
        
        with open('real_signals_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Результаты сохранены в real_signals_analysis.json")
    else:
        print(f"\n⚠️ Сигналы не найдены")
        print("Возможные причины:")
        print("- Каналы используют нестандартные форматы сигналов")
        print("- Сигналы закодированы в изображениях")
        print("- Нужны дополнительные паттерны поиска")
        print("- Каналы публикуют только аналитику, а не торговые сигналы")

if __name__ == "__main__":
    main()
