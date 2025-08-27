import urllib.request
import json
import re
from datetime import datetime

def get_messages(username):
    """Получает сообщения из канала"""
    try:
        url = f"https://t.me/s/{username}"
        
        opener = urllib.request.build_opener()
        opener.addheaders = [
            ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        ]
        
        with opener.open(url, timeout=10) as response:
            content = response.read().decode('utf-8')
            
            messages = []
            text_pattern = r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>'
            text_matches = re.findall(text_pattern, content, re.DOTALL)
            
            for i, text_html in enumerate(text_matches):
                text = re.sub(r'<[^>]+>', '', text_html)
                text = text.strip()
                
                if text and len(text) > 10:
                    messages.append({
                        'id': f"{username}_{i+1}",
                        'text': text,
                        'date': datetime.now().isoformat()
                    })
            
            return messages
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return []

def find_enhanced_signals(messages):
    """Ищет сигналы с улучшенными паттернами"""
    signals = []
    
    # Новые паттерны на основе реальных сообщений
    patterns = [
        # LONGING $SYS HERE
        r'(LONGING|SHORTING)\s+\$(\w+)\s+HERE',
        
        # Buying / Longing #SYS now
        r'(Buying|Longing)\s+[#\$](\w+)',
        
        # $SYS Breakout confirmed. Buying more
        r'\$(\w+)\s+Breakout.*?(Buying|Longing)',
        
        # Buy side liquidity above 4107
        r'(Buy|Sell)\s+side\s+liquidity\s+(above|below)\s+(\d+)',
        
        # LONG $BTC $110,500
        r'(LONG|SHORT)\s+\$(\w+)\s+\$?([\d,]+\.?\d*)',
        
        # $BTC LONG $110,500
        r'\$(\w+)\s+(LONG|SHORT)\s+\$?([\d,]+\.?\d*)',
        
        # BTC/USDT LONG Entry: $110,500
        r'(\w+)/USDT\s+(LONG|SHORT)\s+Entry:\s*\$?([\d,]+\.?\d*)',
        
        # 🚀 BTC LONG $110,500
        r'[🚀📉🔥]\s*(\w+)\s+(LONG|SHORT)\s+\$?([\d,]+\.?\d*)',
        
        # Entry: $110,500 Target: $116,025 Stop: $107,185
        r'Entry:\s*\$?([\d,]+\.?\d*)\s+Target:\s*\$?([\d,]+\.?\d*)\s+Stop:\s*\$?([\d,]+\.?\d*)',
        
        # Простые форматы
        r'(\w+)\s+(LONG|SHORT)\s+\$?([\d,]+\.?\d*)',
        r'(\w+)\s+\$?([\d,]+\.?\d*)\s+(LONG|SHORT)',
        
        # Форматы с эмодзи
        r'🚀\s*(\w+)\s+\$?([\d,]+\.?\d*)',
        r'📉\s*(\w+)\s+\$?([\d,]+\.?\d*)',
        r'🔥\s*(\w+)\s+\$?([\d,]+\.?\d*)',
        
        # Форматы с @
        r'(\w+)\s+@\s*\$?([\d,]+\.?\d*)',
        
        # Форматы с хештегами
        r'#(\w+)\s+(LONG|SHORT)\s+\$?([\d,]+\.?\d*)',
    ]
    
    for message in messages:
        text = message['text']
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                groups = match.groups()
                
                if len(groups) >= 2:
                    signal = {
                        "pattern_used": pattern[:50] + "...",
                        "message_text": text[:150] + "...",
                        "message_id": message['id'],
                        "full_match": match.group(0)
                    }
                    
                    # Обрабатываем разные форматы
                    if "LONGING" in pattern or "SHORTING" in pattern:
                        signal.update({
                            "direction": groups[0].upper(),
                            "asset": groups[1].upper(),
                            "entry_price": None
                        })
                    elif "Buying" in pattern or "Longing" in pattern:
                        signal.update({
                            "direction": "LONG" if "Longing" in groups[0] else "BUY",
                            "asset": groups[1].upper(),
                            "entry_price": None
                        })
                    elif "liquidity" in pattern:
                        signal.update({
                            "direction": groups[0].upper(),
                            "asset": "UNKNOWN",
                            "entry_price": float(groups[2].replace(',', ''))
                        })
                    elif len(groups) >= 3:
                        # Стандартный формат с ценой
                        try:
                            signal.update({
                                "asset": groups[0].upper(),
                                "direction": groups[1].upper(),
                                "entry_price": float(groups[2].replace(',', ''))
                            })
                        except (ValueError, IndexError):
                            continue
                    else:
                        # Формат с двумя группами
                        try:
                            signal.update({
                                "asset": groups[0].upper(),
                                "direction": "UNKNOWN",
                                "entry_price": float(groups[1].replace(',', ''))
                            })
                        except (ValueError, IndexError):
                            continue
                    
                    signals.append(signal)
                    print(f"✅ Найден сигнал: {signal['asset']} {signal['direction']} @ ${signal['entry_price']}")
                    print(f"   Паттерн: {signal['pattern_used']}")
                    print(f"   Текст: {signal['message_text']}")
                    print()
    
    return signals

def main():
    """Основная функция"""
    print("🚀 УЛУЧШЕННЫЙ ПОИСК СИГНАЛОВ")
    print("=" * 60)
    
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
        
        messages = get_messages(username)
        
        if messages:
            print(f"📊 Найдено {len(messages)} сообщений")
            
            signals = find_enhanced_signals(messages)
            
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
            print(f"     Текст: {signal['message_text']}")
            print()
        
        # Сохраняем результаты
        results = {
            "success": True,
            "total_signals": len(all_signals),
            "signals": all_signals,
            "analysis_time": datetime.now().isoformat()
        }
        
        with open('enhanced_signals.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Результаты сохранены в enhanced_signals.json")
    else:
        print(f"\n⚠️ Сигналы не найдены")
        print("Вывод: Каналы содержат аналитику и комментарии, но не стандартные торговые сигналы")

if __name__ == "__main__":
    main()
