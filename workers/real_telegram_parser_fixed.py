import urllib.request
import urllib.parse
import json
import re
from datetime import datetime, timedelta
import time
import ssl

class RealTelegramParser:
    """Реальный парсер Telegram каналов с улучшенной логикой"""
    
    def __init__(self):
        # Создаем контекст SSL без проверки сертификатов
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPSHandler(context=self.ssl_context)
        )
        self.opener.addheaders = [
            ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'),
            ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'),
            ('Accept-Language', 'en-US,en;q=0.5'),
            ('Accept-Encoding', 'gzip, deflate'),
            ('Connection', 'keep-alive'),
            ('Upgrade-Insecure-Requests', '1'),
        ]
    
    def get_channel_content(self, username):
        """Получает содержимое канала с улучшенной обработкой ошибок"""
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
        """Извлекает сообщения из HTML с улучшенными паттернами"""
        messages = []
        
        if not html_content:
            return messages
        
        # Улучшенные паттерны для поиска сообщений
        patterns = [
            # Основной паттерн для сообщений
            r'<div class="tgme_widget_message[^"]*"[^>]*data-post="(\d+)"[^>]*>.*?<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>.*?<time[^>]*datetime="([^"]*)"[^>]*>',
            
            # Альтернативный паттерн
            r'<div class="tgme_widget_message[^"]*"[^>]*>.*?<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>',
            
            # Простой паттерн для текста
            r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_content, re.DOTALL)
            
            for i, match in enumerate(matches):
                if isinstance(match, tuple):
                    if len(match) >= 3:
                        message_id, text_html, date_str = match[0], match[1], match[2]
                    else:
                        text_html = match[0]
                        message_id = f"msg_{i}"
                        date_str = datetime.now().isoformat()
                else:
                    text_html = match
                    message_id = f"msg_{i}"
                    date_str = datetime.now().isoformat()
                
                # Очищаем HTML из текста
                text = re.sub(r'<[^>]+>', '', text_html)
                text = re.sub(r'&nbsp;', ' ', text)
                text = re.sub(r'&amp;', '&', text)
                text = re.sub(r'&lt;', '<', text)
                text = re.sub(r'&gt;', '>', text)
                text = text.strip()
                
                if text and len(text) > 10:  # Минимальная длина сообщения
                    messages.append({
                        'id': message_id,
                        'text': text,
                        'date': date_str,
                        'username': username
                    })
        
        print(f"✅ Найдено {len(messages)} сообщений в {username}")
        return messages
    
    def extract_signals_from_text(self, text):
        """Извлекает сигналы из текста с улучшенными паттернами"""
        signals = []
        
        # Улучшенные паттерны для поиска сигналов
        patterns = [
            # Полный паттерн с Entry, Target, Stop
            r'(\w+)/USDT\s+(LONG|SHORT)\s+Entry:\s*\$?([\d,]+\.?\d*)\s+Target:\s*\$?([\d,]+\.?\d*)\s+Stop:\s*\$?([\d,]+\.?\d*)',
            r'[🚀📉🔥]\s*(\w+)\s+(LONG|SHORT)\s+Entry:\s*\$?([\d,]+\.?\d*)\s+Target:\s*\$?([\d,]+\.?\d*)\s+Stop:\s*\$?([\d,]+\.?\d*)',
            
            # Паттерн с стрелками
            r'(\w+)\s+(LONG|SHORT)\s+\$?([\d,]+\.?\d*)\s*[→➡️]\s*\$?([\d,]+\.?\d*)\s*🛑\s*\$?([\d,]+\.?\d*)',
            
            # Простой паттерн с ценой
            r'(\w+)\s+(LONG|SHORT)\s+\$?([\d,]+\.?\d*)',
            r'[🚀📉🔥]\s*(\w+)\s+(LONG|SHORT)\s+\$?([\d,]+\.?\d*)',
            
            # Паттерн с процентами
            r'(\w+)\s+(LONG|SHORT)\s+[+-]\d+%\s+\$?([\d,]+\.?\d*)',
            
            # Паттерн с точками и подчеркиваниями
            r'(\w+)\.(LONG|SHORT)\.\$?([\d,]+\.?\d*)',
            r'(\w+)_(LONG|SHORT)_\$?([\d,]+\.?\d*)',
            
            # Паттерн с BUY/SELL
            r'(\w+)\s+(BUY|SELL)\s+\$?([\d,]+\.?\d*)',
            r'[🚀📉🔥]\s*(\w+)\s+(BUY|SELL)\s+\$?([\d,]+\.?\d*)',
            
            # Паттерн с CALL/PUT
            r'(\w+)\s+(CALL|PUT)\s+\$?([\d,]+\.?\d*)',
            
            # Паттерн с эмодзи и без цены
            r'[🚀📉🔥]\s*(\w+)\s+(LONG|SHORT|BUY|SELL)',
            r'(\w+)\s+(LONG|SHORT|BUY|SELL)\s*[🚀📉🔥]',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                groups = match.groups()
                
                if len(groups) >= 3:
                    signal = {
                        "asset": groups[0].upper(),
                        "direction": groups[1].upper(),
                        "entry_price": float(groups[2].replace(',', '')) if groups[2].replace(',', '').replace('.', '').isdigit() else None,
                        "target_price": float(groups[3].replace(',', '')) if len(groups) > 3 and groups[3].replace(',', '').replace('.', '').isdigit() else None,
                        "stop_loss": float(groups[4].replace(',', '')) if len(groups) > 4 and groups[4].replace(',', '').replace('.', '').isdigit() else None,
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
                all_signals.extend(signals)
        
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
    parser = RealTelegramParser()
    
    # Список каналов для парсинга
    channels = [
        'signalsbitcoinandethereum',
        'CryptoCapoTG',
        'cryptosignals',
        'binance_signals',
        'crypto_analytics'
    ]
    
    print("🚀 Запуск реального парсера Telegram каналов...")
    
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
    
    with open('real_telegram_signals_fixed.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Парсинг завершен!")
    print(f"📊 Всего сигналов: {len(signals)}")
    print(f"📁 Результат сохранен в: real_telegram_signals_fixed.json")
    
    # Выводим статистику по каналам
    for channel, stat in stats.items():
        print(f"📱 {channel}: {stat['signals_found']} сигналов")

if __name__ == "__main__":
    main()
