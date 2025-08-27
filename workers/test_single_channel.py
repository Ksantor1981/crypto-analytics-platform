import urllib.request
import json
import re
from datetime import datetime

def test_single_channel():
    """Тестируем парсинг одного канала"""
    
    # Настройка запроса
    opener = urllib.request.build_opener()
    opener.addheaders = [
        ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    ]
    
    # Тестируем другой канал
    username = 'CryptoCapoTG'
    url = f"https://t.me/s/{username}"
    
    print(f"🔍 Тестируем канал: {username}")
    print(f"📡 URL: {url}")
    
    try:
        print("⏳ Отправляем запрос...")
        with opener.open(url, timeout=10) as response:
            content = response.read().decode('utf-8')
            print(f"✅ Получено {len(content)} символов")
            
            # Сохраняем сырой HTML для анализа
            with open('test_channel_raw.html', 'w', encoding='utf-8') as f:
                f.write(content)
            print("📁 Сырой HTML сохранен в test_channel_raw.html")
            
            # Ищем сообщения
            message_pattern = r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>'
            messages = re.findall(message_pattern, content, re.DOTALL)
            
            print(f"📝 Найдено {len(messages)} сообщений")
            
            # Обрабатываем первые 5 сообщений
            processed_messages = []
            for i, msg_html in enumerate(messages[:5]):
                # Очищаем HTML
                text = re.sub(r'<[^>]+>', '', msg_html)
                text = re.sub(r'&nbsp;', ' ', text)
                text = text.strip()
                
                if text and len(text) > 10:
                    processed_messages.append({
                        'id': i,
                        'text': text[:200] + "..." if len(text) > 200 else text
                    })
            
            # Ищем сигналы в обработанных сообщениях
            signals = []
            for msg in processed_messages:
                # Простые паттерны для сигналов
                patterns = [
                    r'(\w+)\s+(LONG|SHORT)\s+\$?([\d,]+\.?\d*)',
                    r'(\w+)\s+(BUY|SELL)\s+\$?([\d,]+\.?\d*)',
                    r'[🚀📉🔥]\s*(\w+)\s+(LONG|SHORT|BUY|SELL)',
                ]
                
                for pattern in patterns:
                    matches = re.finditer(pattern, msg['text'], re.IGNORECASE)
                    for match in matches:
                        signal = {
                            'asset': match.group(1).upper(),
                            'direction': match.group(2).upper(),
                            'entry_price': float(match.group(3).replace(',', '')) if len(match.groups()) > 2 and match.group(3).replace(',', '').replace('.', '').isdigit() else None,
                            'original_text': msg['text'],
                            'pattern': pattern
                        }
                        signals.append(signal)
            
            # Результат
            result = {
                'channel': username,
                'total_messages': len(messages),
                'processed_messages': len(processed_messages),
                'signals_found': len(signals),
                'signals': signals,
                'test_time': datetime.now().isoformat()
            }
            
            with open('test_channel_result.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"\n📊 Результат:")
            print(f"   Сообщений: {len(messages)}")
            print(f"   Обработано: {len(processed_messages)}")
            print(f"   Сигналов: {len(signals)}")
            print(f"📁 Результат сохранен в test_channel_result.json")
            
            if signals:
                print("\n🎯 Найденные сигналы:")
                for i, signal in enumerate(signals, 1):
                    print(f"   {i}. {signal['asset']} {signal['direction']} ${signal['entry_price'] if signal['entry_price'] else 'N/A'}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_single_channel()
