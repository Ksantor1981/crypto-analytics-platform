import urllib.request
import json
import re
from datetime import datetime, timedelta
import time

class FixedWebParser:
    """Исправленный парсер Telegram каналов"""
    
    def __init__(self):
        self.opener = urllib.request.build_opener()
        self.opener.addheaders = [
            ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        ]
    
    def get_channel_content(self, username):
        """Получает содержимое канала"""
        try:
            url = f"https://t.me/s/{username}"
            print(f"📡 Получение содержимого {username}...")
            
            with self.opener.open(url, timeout=10) as response:
                content = response.read().decode('utf-8')
                return content
                
        except Exception as e:
            print(f"❌ Ошибка получения {username}: {e}")
            return None
    
    def extract_messages_from_html(self, html_content, username):
        """Извлекает сообщения из HTML с исправленным парсингом"""
        messages = []
        
        # Ищем все блоки сообщений
        message_pattern = r'<div class="tgme_widget_message[^"]*"[^>]*data-post="(\d+)"[^>]*>(.*?)</div>\s*</div>\s*</div>'
        
        matches = re.findall(message_pattern, html_content, re.DOTALL)
        
        for match in matches:
            message_id, message_html = match
            
            # Ищем текст сообщения в блоке
            text_pattern = r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>'
            text_match = re.search(text_pattern, message_html, re.DOTALL)
            
            if text_match:
                text_html = text_match.group(1)
                # Очищаем HTML из текста
                text = re.sub(r'<[^>]+>', '', text_html)
                text = text.strip()
                
                # Ищем дату
                date_pattern = r'<time[^>]*datetime="([^"]*)"[^>]*>'
                date_match = re.search(date_pattern, message_html)
                date_str = date_match.group(1) if date_match else datetime.now().isoformat()
                
                if text:
                    messages.append({
                        'id': message_id,
                        'text': text,
                        'date': date_str,
                        'username': username
                    })
        
        print(f"✅ Найдено {len(messages)} сообщений в {username}")
        return messages
    
    def extract_signals_from_text(self, text):
        """Извлекает сигналы из текста сообщения"""
        signals = []
        
        # Расширенные паттерны для поиска сигналов
        patterns = [
            # Стандартные форматы
            r'(\w+)/USDT\s+(LONG|SHORT)\s+Entry:\s*\$?([\d,]+\.?\d*)\s+Target:\s*\$?([\d,]+\.?\d*)\s+Stop:\s*\$?([\d,]+\.?\d*)',
            r'[🚀📉🔥]\s*(\w+)\s+(LONG|SHORT)\s+Entry:\s*\$?([\d,]+\.?\d*)\s+Target:\s*\$?([\d,]+\.?\d*)\s+Stop:\s*\$?([\d,]+\.?\d*)',
            r'(\w+)\s+(LONG|SHORT)\s+\$?([\d,]+\.?\d*)\s*[→➡️]\s*\$?([\d,]+\.?\d*)\s*🛑\s*\$?([\d,]+\.?\d*)',
            
            # Простые форматы
            r'(\w+)\s+(LONG|SHORT)\s+\$?([\d,]+\.?\d*)',
            r'[🚀📉🔥]\s*(\w+)\s+(LONG|SHORT)\s+\$?([\d,]+\.?\d*)',
            r'(\w+)\s+(LONG|SHORT)\s+[+-]\d+%\s+\$?([\d,]+\.?\d*)',
            
            # Альтернативные форматы
            r'(\w+)\.(LONG|SHORT)\.\$?([\d,]+\.?\d*)',
            r'(\w+)_(LONG|SHORT)_\$?([\d,]+\.?\d*)',
            
            # Форматы с эмодзи
            r'🚀\s*(\w+)\s+(LONG|SHORT)\s+\$?([\d,]+\.?\d*)',
            r'📉\s*(\w+)\s+(LONG|SHORT)\s+\$?([\d,]+\.?\d*)',
            r'🔥\s*(\w+)\s+(LONG|SHORT)\s+\$?([\d,]+\.?\d*)',
            
            # Форматы с процентами
            r'(\w+)\s+(LONG|SHORT)\s+\+(\d+)%\s+\$?([\d,]+\.?\d*)',
            r'(\w+)\s+(LONG|SHORT)\s+-(\d+)%\s+\$?([\d,]+\.?\d*)',
            
            # Форматы с точками и запятыми
            r'(\w+)\s+(LONG|SHORT)\s+@\s*\$?([\d,]+\.?\d*)',
            r'(\w+)\s+(LONG|SHORT)\s+:\s*\$?([\d,]+\.?\d*)',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) >= 3:
                    signal = {
                        "asset": match.group(1).upper(),
                        "direction": match.group(2).upper(),
                        "entry_price": float(match.group(3).replace(',', '')),
                        "target_price": None,
                        "stop_loss": None,
                        "pattern_used": pattern[:50] + "..."
                    }
                    
                    # Добавляем target и stop loss если найдены
                    if len(match.groups()) >= 5:
                        signal["target_price"] = float(match.group(4).replace(',', ''))
                        signal["stop_loss"] = float(match.group(5).replace(',', ''))
                    
                    signals.append(signal)
        
        return signals
    
    def collect_signals_from_channel(self, username, hours_back=24):
        """Собирает сигналы из канала"""
        print(f"🔍 Сбор сигналов из канала {username}...")
        
        html_content = self.get_channel_content(username)
        if not html_content:
            return []
        
        messages = self.extract_messages_from_html(html_content, username)
        signals = []
        
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        for message in messages:
            try:
                # Парсим дату
                date_str = message['date']
                if 'T' in date_str:
                    message_time = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                else:
                    message_time = datetime.now()
                
                if message_time >= cutoff_time:
                    extracted_signals = self.extract_signals_from_text(message['text'])
                    
                    for signal in extracted_signals:
                        signal.update({
                            "channel_username": username,
                            "message_id": message['id'],
                            "message_date": message['date'],
                            "message_text": message['text'][:200] + "..." if len(message['text']) > 200 else message['text']
                        })
                        signals.append(signal)
            except Exception as e:
                print(f"❌ Ошибка обработки сообщения: {e}")
                continue
        
        print(f"✅ Найдено {len(signals)} сигналов в канале {username}")
        return signals
    
    def collect_all_signals(self, channels, hours_back=24):
        """Собирает сигналы из всех каналов"""
        print("🚀 Запуск сбора сигналов из всех каналов...")
        
        all_signals = []
        channel_stats = {}
        
        for channel in channels:
            username = channel.get('username', channel)
            try:
                signals = self.collect_signals_from_channel(username, hours_back)
                all_signals.extend(signals)
                channel_stats[username] = {
                    "signals_found": len(signals),
                    "channel_name": channel.get('name', username)
                }
                
                # Пауза между запросами
                time.sleep(3)
                
            except Exception as e:
                print(f"❌ Ошибка сбора сигналов из {username}: {e}")
                channel_stats[username] = {
                    "signals_found": 0,
                    "error": str(e),
                    "channel_name": channel.get('name', username)
                }
        
        results = {
            "success": True,
            "total_signals": len(all_signals),
            "signals": all_signals,
            "channel_stats": channel_stats,
            "collection_time": datetime.now().isoformat(),
            "hours_back": hours_back
        }
        
        print(f"✅ Сбор завершен: {len(all_signals)} сигналов из {len(channels)} каналов")
        return results

def main():
    """Основная функция"""
    print("🚀 ЗАПУСК ИСПРАВЛЕННОГО ВЕБ-ПАРСЕРА TELEGRAM КАНАЛОВ")
    print("=" * 60)
    
    # Список каналов для парсинга (только те, где есть сообщения)
    channels = [
        {"username": "CryptoCapoTG", "name": "Crypto Capo"},
        {"username": "cryptosignals", "name": "Crypto Signals"},
        {"username": "binance_signals", "name": "Binance Signals"}
    ]
    
    parser = FixedWebParser()
    
    # Собираем сигналы
    results = parser.collect_all_signals(channels, hours_back=24)
    
    if results['success']:
        print(f"\n✅ СБОР ЗАВЕРШЕН:")
        print(f"Всего сигналов: {results['total_signals']}")
        
        for username, stats in results['channel_stats'].items():
            print(f"  {username}: {stats['signals_found']} сигналов")
        
        # Сохраняем результаты
        with open('fixed_web_signals.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Результаты сохранены в fixed_web_signals.json")
        
        # Показываем найденные сигналы
        if results['signals']:
            print(f"\n📊 НАЙДЕННЫЕ СИГНАЛЫ:")
            for i, signal in enumerate(results['signals'][:10], 1):  # Показываем первые 10
                print(f"  {i}. {signal['asset']} {signal['direction']} @ ${signal['entry_price']}")
                print(f"     Канал: {signal['channel_username']}")
                if signal['target_price']:
                    print(f"     Target: ${signal['target_price']}")
                if signal['stop_loss']:
                    print(f"     Stop: ${signal['stop_loss']}")
                print()
        else:
            print(f"\n⚠️ Сигналы не найдены")
            print("Возможные причины:")
            print("- Каналы не содержат сигналы в нужном формате")
            print("- Сигналы были опубликованы более 24 часов назад")
            print("- Нужно настроить другие паттерны поиска")
    else:
        print(f"\n❌ Ошибка сбора: {results.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()
