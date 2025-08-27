import urllib.request
import json
import re
from datetime import datetime
import time

class ImprovedTelegramParser:
    """Улучшенный парсер Telegram каналов"""
    
    def __init__(self):
        self.opener = urllib.request.build_opener()
        self.opener.addheaders = [
            ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        ]
    
    def get_channel_content(self, username):
        """Получает содержимое канала"""
        try:
            url = f"https://t.me/s/{username}"
            print(f"📡 Получение содержимого {username}...")
            
            with self.opener.open(url, timeout=15) as response:
                content = response.read().decode('utf-8')
                print(f"✅ Получено {len(content)} символов из {username}")
                return content
                
        except Exception as e:
            print(f"❌ Ошибка получения {username}: {e}")
            return None
    
    def extract_messages_from_html(self, html_content, username):
        """Извлекает сообщения из HTML с правильными паттернами"""
        messages = []
        
        if not html_content:
            return messages
        
        # Правильный паттерн для сообщений Telegram
        message_pattern = r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>'
        matches = re.findall(message_pattern, html_content, re.DOTALL)
        
        for i, text_html in enumerate(matches):
            # Очищаем HTML из текста
            text = re.sub(r'<[^>]+>', '', text_html)
            text = re.sub(r'&nbsp;', ' ', text)
            text = re.sub(r'&amp;', '&', text)
            text = re.sub(r'&lt;', '<', text)
            text = re.sub(r'&gt;', '>', text)
            text = re.sub(r'&#036;', '$', text)  # Заменяем HTML-код доллара
            text = re.sub(r'&#39;', "'", text)   # Заменяем HTML-код апострофа
            text = text.strip()
            
            if text and len(text) > 10:  # Минимальная длина сообщения
                messages.append({
                    'id': f"msg_{i}",
                    'text': text,
                    'date': datetime.now().isoformat(),
                    'username': username
                })
        
        print(f"✅ Найдено {len(messages)} сообщений в {username}")
        return messages
    
    def extract_signals_from_text(self, text):
        """Извлекает сигналы из текста с улучшенными паттернами"""
        signals = []
        
        # Улучшенные паттерны для поиска сигналов
        patterns = [
            # Паттерны с ценами
            r'(\w+)\s+(LONG|SHORT)\s+\$?([\d,]+\.?\d*)',
            r'(\w+)\s+(BUY|SELL)\s+\$?([\d,]+\.?\d*)',
            r'[🚀📉🔥]\s*(\w+)\s+(LONG|SHORT|BUY|SELL)\s+\$?([\d,]+\.?\d*)',
            
            # Паттерны с эмодзи без цен
            r'[🚀📉🔥]\s*(\w+)\s+(LONG|SHORT|BUY|SELL)',
            r'(\w+)\s+(LONG|SHORT|BUY|SELL)\s*[🚀📉🔥]',
            
            # Паттерны с упоминанием криптовалют
            r'\$(\w+)\s+(LONG|SHORT|BUY|SELL)',
            r'(\w+)\s+(LONG|SHORT|BUY|SELL)\s+update',
            
            # Паттерны с целями
            r'(\w+)\s+target\s+\$?([\d,]+\.?\d*)',
            r'(\w+)\s+resistance\s+\$?([\d,]+\.?\d*)',
            r'(\w+)\s+support\s+\$?([\d,]+\.?\d*)',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                groups = match.groups()
                
                if len(groups) >= 2:
                    signal = {
                        "asset": groups[0].upper(),
                        "direction": groups[1].upper(),
                        "entry_price": float(groups[2].replace(',', '')) if len(groups) > 2 and groups[2].replace(',', '').replace('.', '').isdigit() else None,
                        "target_price": None,
                        "stop_loss": None,
                        "pattern_used": pattern[:50] + "...",
                        "original_text": text[:200] + "..." if len(text) > 200 else text
                    }
                    
                    # Проверяем, что это не дубликат
                    if not any(s['asset'] == signal['asset'] and s['direction'] == signal['direction'] for s in signals):
                        signals.append(signal)
        
        return signals
    
    def parse_channel(self, username, hours_back=24):
        """Парсит канал и извлекает сигналы"""
        print(f"\n🔍 Парсинг канала: {username}")
        
        # Получаем содержимое канала
        content = self.get_channel_content(username)
        if not content:
            return []
        
        # Извлекаем сообщения
        messages = self.extract_messages_from_html(content, username)
        if not messages:
            print(f"❌ Не найдено сообщений в {username}")
            return []
        
        # Извлекаем сигналы из сообщений
        all_signals = []
        for message in messages:
            signals = self.extract_signals_from_text(message['text'])
            for signal in signals:
                signal.update({
                    'channel': username,
                    'message_id': message['id'],
                    'timestamp': message['date'],
                    'extraction_time': datetime.now().isoformat()
                })
                all_signals.append(signal)
        
        print(f"✅ Извлечено {len(all_signals)} сигналов из {username}")
        return all_signals
    
    def parse_all_channels(self, channels, hours_back=24):
        """Парсит все каналы"""
        all_signals = []
        channel_stats = {}
        
        for username in channels:
            try:
                signals = self.parse_channel(username, hours_back)
                all_signals.extend(signals)
                
                channel_stats[username] = {
                    'signals_found': len(signals),
                    'channel_name': username
                }
                
                # Небольшая задержка между запросами
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Ошибка парсинга {username}: {e}")
                channel_stats[username] = {
                    'signals_found': 0,
                    'channel_name': username,
                    'error': str(e)
                }
        
        return all_signals, channel_stats

def main():
    """Основная функция"""
    parser = ImprovedTelegramParser()
    
    # Список каналов для парсинга
    channels = [
        'CryptoCapoTG',
        'signalsbitcoinandethereum',
        'cryptosignals',
        'binance_signals'
    ]
    
    print("🚀 Запуск улучшенного парсера Telegram каналов...")
    
    # Парсим все каналы
    signals, stats = parser.parse_all_channels(channels, hours_back=24)
    
    # Сохраняем результаты
    result = {
        'success': True,
        'total_signals': len(signals),
        'signals': signals,
        'channel_stats': stats,
        'collection_time': datetime.now().isoformat(),
        'hours_back': 24
    }
    
    with open('improved_telegram_signals.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Парсинг завершен!")
    print(f"📊 Всего сигналов: {len(signals)}")
    print(f"📁 Результат сохранен в: improved_telegram_signals.json")
    
    # Выводим статистику по каналам
    for channel, stat in stats.items():
        print(f"📱 {channel}: {stat['signals_found']} сигналов")
    
    # Показываем найденные сигналы
    if signals:
        print(f"\n🎯 Найденные сигналы:")
        for i, signal in enumerate(signals, 1):
            print(f"   {i}. {signal['asset']} {signal['direction']} ${signal['entry_price'] if signal['entry_price'] else 'N/A'}")

if __name__ == "__main__":
    main()
