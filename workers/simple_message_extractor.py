import urllib.request
import json
import re
from datetime import datetime

def extract_messages_simple(username):
    """Простой экстрактор сообщений"""
    print(f"🔍 Извлечение сообщений из {username}")
    
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
            
            print(f"Найдено {len(text_matches)} текстовых блоков")
            
            for i, text_html in enumerate(text_matches):
                # Очищаем HTML
                text = re.sub(r'<[^>]+>', '', text_html)
                text = text.strip()
                
                if text:
                    # Ищем ID сообщения
                    message_id = f"{username}_{i+1}"
                    
                    messages.append({
                        'id': message_id,
                        'text': text,
                        'date': datetime.now().isoformat(),
                        'username': username
                    })
                    
                    print(f"Сообщение {i+1}: {text[:100]}...")
            
            return messages
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return []

def extract_signals_from_text(text):
    """Извлекает сигналы из текста"""
    signals = []
    
    # Простые паттерны для поиска сигналов
    patterns = [
        # BTC LONG $110,500
        r'(\w+)\s+(LONG|SHORT)\s+\$?([\d,]+\.?\d*)',
        # 🚀 BTC LONG $110,500
        r'[🚀📉🔥]\s*(\w+)\s+(LONG|SHORT)\s+\$?([\d,]+\.?\d*)',
        # BTC/USDT LONG $110,500
        r'(\w+)/USDT\s+(LONG|SHORT)\s+\$?([\d,]+\.?\d*)',
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            if len(match.groups()) >= 3:
                signal = {
                    "asset": match.group(1).upper(),
                    "direction": match.group(2).upper(),
                    "entry_price": float(match.group(3).replace(',', '')),
                    "pattern_used": pattern[:30] + "..."
                }
                signals.append(signal)
    
    return signals

def main():
    """Основная функция"""
    print("🚀 ПРОСТОЙ ЭКСТРАКТОР СООБЩЕНИЙ")
    print("=" * 60)
    
    # Тестируем один канал
    username = "CryptoCapoTG"
    
    messages = extract_messages_simple(username)
    
    if messages:
        print(f"\n✅ Найдено {len(messages)} сообщений")
        
        all_signals = []
        
        for message in messages:
            signals = extract_signals_from_text(message['text'])
            for signal in signals:
                signal.update({
                    "channel_username": username,
                    "message_id": message['id'],
                    "message_text": message['text'][:200] + "..." if len(message['text']) > 200 else message['text']
                })
                all_signals.append(signal)
        
        print(f"\n📊 Найдено {len(all_signals)} сигналов")
        
        for i, signal in enumerate(all_signals, 1):
            print(f"  {i}. {signal['asset']} {signal['direction']} @ ${signal['entry_price']}")
            print(f"     Текст: {signal['message_text'][:100]}...")
            print()
        
        # Сохраняем результаты
        results = {
            "success": True,
            "total_signals": len(all_signals),
            "signals": all_signals,
            "collection_time": datetime.now().isoformat()
        }
        
        with open('simple_signals.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Результаты сохранены в simple_signals.json")
        
    else:
        print("❌ Сообщения не найдены")

if __name__ == "__main__":
    main()
