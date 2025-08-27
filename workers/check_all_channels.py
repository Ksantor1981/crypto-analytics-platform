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
        return []

def find_signals(messages):
    """Ищет сигналы в сообщениях"""
    signals = []
    
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
        
        # Дополнительные форматы
        r'(\w+)\s+(BUY|SELL)\s+\$?([\d,]+\.?\d*)',
        r'(\w+)\s+(BUY|SELL)\s+@\s*\$?([\d,]+\.?\d*)',
        r'(\w+)\s+(BUY|SELL)\s+Entry:\s*\$?([\d,]+\.?\d*)',
        
        # Форматы с Take Profit
        r'(\w+)\s+(LONG|SHORT)\s+TP:\s*\$?([\d,]+\.?\d*)',
        r'(\w+)\s+(LONG|SHORT)\s+Target:\s*\$?([\d,]+\.?\d*)',
        
        # Форматы с Stop Loss
        r'(\w+)\s+(LONG|SHORT)\s+SL:\s*\$?([\d,]+\.?\d*)',
        r'(\w+)\s+(LONG|SHORT)\s+Stop:\s*\$?([\d,]+\.?\d*)',
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
    
    return signals

def main():
    """Основная функция"""
    print("🚀 ПРОВЕРКА ВСЕХ ДОСТУПНЫХ КАНАЛОВ")
    print("=" * 60)
    
    # Все каналы для проверки
    all_channels = [
        # Текущие каналы
        "CryptoCapoTG",
        "cryptosignals", 
        "binance_signals",
        
        # Дополнительные каналы
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
    
    results = {
        "accessible_channels": [],
        "inaccessible_channels": [],
        "channels_with_signals": [],
        "total_signals": 0,
        "all_signals": [],
        "check_time": datetime.now().isoformat()
    }
    
    for username in all_channels:
        print(f"\n📡 Проверка канала: {username}")
        
        messages = get_messages(username)
        
        if messages:
            print(f"   ✅ Доступен ({len(messages)} сообщений)")
            results["accessible_channels"].append({
                "username": username,
                "message_count": len(messages)
            })
            
            signals = find_signals(messages)
            
            if signals:
                print(f"   🎯 Найдено {len(signals)} сигналов!")
                results["channels_with_signals"].append({
                    "username": username,
                    "signal_count": len(signals)
                })
                
                for signal in signals:
                    signal['channel_username'] = username
                    results["all_signals"].append(signal)
                
                results["total_signals"] += len(signals)
                
                # Показываем первые 3 сигнала
                for i, signal in enumerate(signals[:3], 1):
                    print(f"      {i}. {signal['asset']} {signal['direction']} @ ${signal['entry_price']}")
            else:
                print(f"   ⚠️ Сигналы не найдены")
        else:
            print(f"   ❌ Недоступен")
            results["inaccessible_channels"].append(username)
    
    # Итоговый отчет
    print(f"\n{'='*60}")
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print(f"{'='*60}")
    
    print(f"Всего проверено каналов: {len(all_channels)}")
    print(f"Доступных каналов: {len(results['accessible_channels'])}")
    print(f"Недоступных каналов: {len(results['inaccessible_channels'])}")
    print(f"Каналов с сигналами: {len(results['channels_with_signals'])}")
    print(f"Всего найдено сигналов: {results['total_signals']}")
    
    if results["channels_with_signals"]:
        print(f"\n🎯 КАНАЛЫ С СИГНАЛАМИ:")
        for channel in results["channels_with_signals"]:
            print(f"  - {channel['username']}: {channel['signal_count']} сигналов")
    
    if results["all_signals"]:
        print(f"\n🎯 ВСЕ НАЙДЕННЫЕ СИГНАЛЫ:")
        for i, signal in enumerate(results["all_signals"], 1):
            print(f"  {i:2d}. {signal['asset']} {signal['direction']} @ ${signal['entry_price']}")
            print(f"      Канал: {signal['channel_username']}")
            print(f"      Текст: {signal['message_text']}")
            print()
    
    if results["inaccessible_channels"]:
        print(f"\n❌ НЕДОСТУПНЫЕ КАНАЛЫ:")
        for channel in results["inaccessible_channels"]:
            print(f"  - {channel}")
    
    # Сохраняем результаты
    with open('all_channels_check.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Результаты сохранены в all_channels_check.json")

if __name__ == "__main__":
    main()
