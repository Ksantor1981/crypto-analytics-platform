"""
Real Telegram Parser - Реальный парсер Telegram каналов
Использует web scraping для извлечения актуальных сигналов
"""

import urllib.request
import json
import re
from datetime import datetime, timedelta
import time
from typing import List, Dict, Optional, Tuple, Any
import logging
import ssl
from improved_signal_parser import ImprovedSignal, SignalDirection, SignalQuality, ImprovedSignalExtractor

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RealTelegramParser:
    """Реальный парсер Telegram каналов"""
    
    def __init__(self):
        self.extractor = ImprovedSignalExtractor()
        
        # Настройка SSL контекста для избежания ошибок сертификатов
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
        # Список реальных каналов для парсинга
        self.channels = [
            {
                'name': 'CryptoCapoTG',
                'url': 'https://t.me/CryptoCapoTG',
                'web_url': 'https://t.me/s/CryptoCapoTG'
            },
            {
                'name': 'BinanceKillers_Free',
                'url': 'https://t.me/BinanceKillers_Free',
                'web_url': 'https://t.me/s/BinanceKillers_Free'
            },
            {
                'name': 'cryptosignals',
                'url': 'https://t.me/cryptosignals',
                'web_url': 'https://t.me/s/cryptosignals'
            },
            {
                'name': 'binance_signals',
                'url': 'https://t.me/binance_signals',
                'web_url': 'https://t.me/s/binance_signals'
            },
            {
                'name': 'bitcoin_signals',
                'url': 'https://t.me/bitcoin_signals',
                'web_url': 'https://t.me/s/bitcoin_signals'
            }
        ]
        
        # User-Agent для имитации браузера
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def parse_channels(self) -> Dict[str, Any]:
        """Парсит все каналы и возвращает реальные сигналы"""
        all_signals = []
        channel_stats = {}
        
        for channel_info in self.channels:
            try:
                logger.info(f"Parsing channel: {channel_info['name']}")
                channel_signals = self.parse_channel(channel_info)
                all_signals.extend(channel_signals)
                
                # Статистика по каналу
                channel_stats[channel_info['name']] = {
                    'total_signals': len(channel_signals),
                    'valid_signals': len([s for s in channel_signals if s.is_valid]),
                    'avg_confidence': sum([s.real_confidence for s in channel_signals]) / len(channel_signals) if channel_signals else 0,
                    'quality_distribution': self.get_quality_distribution(channel_signals)
                }
                
                # Задержка между запросами для избежания блокировки
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error parsing channel {channel_info['name']}: {e}")
                channel_stats[channel_info['name']] = {
                    'total_signals': 0,
                    'valid_signals': 0,
                    'avg_confidence': 0,
                    'quality_distribution': {},
                    'error': str(e)
                }
        
        # Фильтруем только валидные сигналы
        valid_signals = [s for s in all_signals if s.is_valid]
        
        # Сортируем по confidence
        valid_signals.sort(key=lambda x: x.real_confidence, reverse=True)
        
        return {
            'success': True,
            'total_signals': len(valid_signals),
            'total_raw_signals': len(all_signals),
            'signals': [self.signal_to_dict(signal) for signal in valid_signals],
            'channel_stats': channel_stats,
            'quality_summary': self.get_quality_summary(valid_signals),
            'timestamp': datetime.now().isoformat()
        }
    
    def parse_channel(self, channel_info: Dict[str, str]) -> List[ImprovedSignal]:
        """Парсит конкретный канал"""
        signals = []
        
        try:
            # Получаем HTML страницы канала
            html_content = self.fetch_channel_page(channel_info['web_url'])
            if not html_content:
                logger.warning(f"Could not fetch content for {channel_info['name']}")
                return signals
            
            # Извлекаем сообщения из HTML
            messages = self.extract_messages_from_html(html_content)
            logger.info(f"Found {len(messages)} messages in {channel_info['name']}")
            
            # Обрабатываем каждое сообщение
            for i, message_text in enumerate(messages):
                try:
                    message_id = f"msg_{i}"
                    message_signals = self.extractor.extract_signals_from_text(
                        message_text, channel_info['name'], message_id
                    )
                    signals.extend(message_signals)
                except Exception as e:
                    logger.error(f"Error processing message {i} in {channel_info['name']}: {e}")
            
        except Exception as e:
            logger.error(f"Error parsing channel {channel_info['name']}: {e}")
        
        return signals
    
    def fetch_channel_page(self, url: str) -> Optional[str]:
        """Получает HTML страницу канала"""
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, context=self.ssl_context, timeout=10) as response:
                return response.read().decode('utf-8')
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def extract_messages_from_html(self, html_content: str) -> List[str]:
        """Извлекает сообщения из HTML"""
        messages = []
        
        # Паттерн для поиска сообщений в Telegram web view
        message_pattern = r'<div class="tgme_widget_message_text js-message_text" dir="auto">(.*?)</div>'
        matches = re.findall(message_pattern, html_content, re.DOTALL)
        
        for match in matches:
            # Очищаем HTML теги
            clean_text = self.clean_html(match)
            if clean_text and len(clean_text.strip()) > 10:  # Минимальная длина сообщения
                messages.append(clean_text.strip())
        
        # Убираем дубликаты
        unique_messages = list(set(messages))
        return unique_messages[:20]  # Ограничиваем количество сообщений
    
    def clean_html(self, html_text: str) -> str:
        """Очищает HTML от тегов"""
        # Убираем HTML теги
        clean = re.sub(r'<[^>]+>', '', html_text)
        
        # Заменяем HTML entities
        clean = clean.replace('&amp;', '&')
        clean = clean.replace('&lt;', '<')
        clean = clean.replace('&gt;', '>')
        clean = clean.replace('&quot;', '"')
        clean = clean.replace('&#39;', "'")
        clean = clean.replace('&nbsp;', ' ')
        
        # Убираем лишние пробелы
        clean = re.sub(r'\s+', ' ', clean)
        
        return clean.strip()
    
    def get_quality_distribution(self, signals: List[ImprovedSignal]) -> Dict[str, int]:
        """Получает распределение качества сигналов"""
        distribution = {}
        for signal in signals:
            quality = signal.signal_quality.value
            distribution[quality] = distribution.get(quality, 0) + 1
        return distribution
    
    def get_quality_summary(self, signals: List[ImprovedSignal]) -> Dict[str, Any]:
        """Получает сводку по качеству сигналов"""
        if not signals:
            return {}
        
        confidences = [s.real_confidence for s in signals]
        
        return {
            'avg_confidence': sum(confidences) / len(confidences) if confidences else 0,
            'median_confidence': sorted(confidences)[len(confidences)//2] if confidences else 0,
            'min_confidence': min(confidences) if confidences else 0,
            'max_confidence': max(confidences) if confidences else 0,
            'quality_distribution': self.get_quality_distribution(signals),
            'bybit_available_count': len([s for s in signals if s.bybit_available]),
            'high_confidence_count': len([s for s in signals if s.real_confidence >= 70]),
        }
    
    def signal_to_dict(self, signal: ImprovedSignal) -> Dict[str, Any]:
        """Конвертирует ImprovedSignal в dict для JSON сериализации"""
        return {
            'id': signal.id,
            'asset': signal.asset,
            'direction': signal.direction.value,
            'entry_price': signal.entry_price,
            'target_price': signal.target_price,
            'stop_loss': signal.stop_loss,
            'leverage': signal.leverage,
            'timeframe': signal.timeframe,
            'signal_quality': signal.signal_quality.value,
            'real_confidence': signal.real_confidence,
            'calculated_confidence': signal.calculated_confidence,
            'channel': signal.channel,
            'message_id': signal.message_id,
            'original_text': signal.original_text,
            'cleaned_text': signal.cleaned_text,
            'signal_type': signal.signal_type,
            'timestamp': signal.timestamp,
            'extraction_time': signal.extraction_time,
            'bybit_available': signal.bybit_available,
            'is_valid': signal.is_valid,
            'validation_errors': signal.validation_errors,
            'risk_reward_ratio': signal.risk_reward_ratio,
            'potential_profit': signal.potential_profit,
            'potential_loss': signal.potential_loss
        }

def main():
    """Основная функция для запуска реального парсера"""
    parser = RealTelegramParser()
    
    logger.info("Starting real Telegram parsing...")
    result = parser.parse_channels()
    
    # Сохраняем результат
    with open('real_telegram_signals.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Parsing completed. Found {result['total_signals']} valid signals.")
    logger.info(f"Quality summary: {result['quality_summary']}")
    
    return result

if __name__ == "__main__":
    main()
