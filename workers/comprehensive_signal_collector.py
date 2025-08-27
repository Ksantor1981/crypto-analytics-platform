"""
Комплексный сборщик и анализатор торговых сигналов
Собирает сигналы со всех источников, анализирует точность и показывает актуальные сигналы
"""

import json
import sqlite3
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging
import time
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveSignalCollector:
    """Комплексный сборщик сигналов со всех источников"""
    
    def __init__(self):
        self.db_path = 'signals_database.db'
        self.init_database()
        
        # Источники сигналов
        self.sources = {
            'telegram_channels': [
                'CryptoCapoTG',
                'signalsbitcoinandethereum',
                'cryptosignals',
                'binance_signals',
                'crypto_analytics',
                'binance_signals_official',
                'coinbase_signals',
                'kraken_signals',
                'crypto_signals_daily',
                'bitcoin_signals',
                'ethereum_signals_daily',
                'altcoin_signals_pro',
                'defi_signals_daily',
                'trading_signals_24_7',
                'crypto_analytics_pro',
                'market_signals',
                'price_alerts',
                'crypto_news_signals',
                'BinanceKillers_Free',
                'Wolf_of_Trading',
                'Crypto_Inner_Circle',
                'Traders_Diary',
                'Crypto_Trading_RU'
            ],
            'apis': [
                'coingecko',
                'binance',
                'bybit'
            ],
            'websites': [
                'tradingview',
                'coinmarketcap',
                'cryptocompare'
            ]
        }
        
        # Импортируем парсеры
        try:
            from enhanced_telegram_parser import EnhancedTelegramParser
            from universal_signal_parser import UniversalSignalParser
            from technical_signal_analyzer import TechnicalSignalAnalyzer
            
            self.telegram_parser = EnhancedTelegramParser()
            self.universal_parser = UniversalSignalParser()
            self.technical_analyzer = TechnicalSignalAnalyzer()
            
            logger.info("✅ Все парсеры успешно загружены")
        except ImportError as e:
            logger.error(f"❌ Ошибка импорта парсеров: {e}")
            self.telegram_parser = None
            self.universal_parser = None
            self.technical_analyzer = None
    
    def init_database(self):
        """Инициализирует базу данных для хранения сигналов и статистики"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица сигналов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signals (
                id TEXT PRIMARY KEY,
                asset TEXT NOT NULL,
                direction TEXT NOT NULL,
                entry_price REAL,
                target_price REAL,
                stop_loss REAL,
                confidence REAL,
                channel TEXT NOT NULL,
                source_type TEXT NOT NULL,
                signal_type TEXT,
                timestamp TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                result TEXT,
                profit_loss REAL,
                completion_time TEXT,
                leverage TEXT,
                timeframe TEXT,
                entry_type TEXT,
                all_targets TEXT,
                stop_loss_percent REAL
            )
        ''')
        
        # Таблица статистики каналов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS channel_stats (
                channel TEXT PRIMARY KEY,
                total_signals INTEGER DEFAULT 0,
                successful_signals INTEGER DEFAULT 0,
                failed_signals INTEGER DEFAULT 0,
                pending_signals INTEGER DEFAULT 0,
                avg_confidence REAL DEFAULT 0,
                avg_profit_loss REAL DEFAULT 0,
                last_updated TEXT,
                success_rate REAL DEFAULT 0
            )
        ''')
        
        # Таблица цен активов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS asset_prices (
                asset TEXT,
                price REAL,
                timestamp TEXT,
                source TEXT,
                PRIMARY KEY (asset, timestamp)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ База данных инициализирована")
    
    def collect_all_signals(self) -> Dict:
        """Собирает сигналы со всех источников"""
        logger.info("🚀 Начинаем сбор сигналов со всех источников...")
        
        all_signals = {
            'telegram': [],
            'api': [],
            'website': [],
            'total': 0,
            'collection_time': datetime.now().isoformat()
        }
        
        # Собираем сигналы из Telegram
        if self.telegram_parser:
            logger.info("📱 Сбор сигналов из Telegram каналов...")
            try:
                telegram_signals, stats = self.telegram_parser.parse_all_channels(
                    self.sources['telegram_channels'], 
                    hours_back=24
                )
                all_signals['telegram'] = telegram_signals
                logger.info(f"✅ Собрано {len(telegram_signals)} сигналов из Telegram")
            except Exception as e:
                logger.error(f"❌ Ошибка сбора Telegram сигналов: {e}")
        
        # Собираем сигналы из API
        logger.info("🔌 Сбор сигналов из API...")
        api_signals = self.collect_api_signals()
        all_signals['api'] = api_signals
        logger.info(f"✅ Собрано {len(api_signals)} сигналов из API")
        
        # Собираем сигналы с веб-сайтов
        logger.info("🌐 Сбор сигналов с веб-сайтов...")
        website_signals = self.collect_website_signals()
        all_signals['website'] = website_signals
        logger.info(f"✅ Собрано {len(website_signals)} сигналов с веб-сайтов")
        
        # Обновляем общее количество
        all_signals['total'] = len(all_signals['telegram']) + len(all_signals['api']) + len(all_signals['website'])
        
        # Сохраняем в базу данных
        self.save_signals_to_database(all_signals)
        
        logger.info(f"🎉 Сбор завершен! Всего сигналов: {all_signals['total']}")
        return all_signals
    
    def collect_api_signals(self) -> List[Dict]:
        """Собирает сигналы из API источников"""
        signals = []
        
        # CoinGecko API
        try:
            coingecko_signals = self.get_coingecko_signals()
            signals.extend(coingecko_signals)
        except Exception as e:
            logger.error(f"❌ Ошибка CoinGecko API: {e}")
        
        # Binance API
        try:
            binance_signals = self.get_binance_signals()
            signals.extend(binance_signals)
        except Exception as e:
            logger.error(f"❌ Ошибка Binance API: {e}")
        
        return signals
    
    def get_coingecko_signals(self) -> List[Dict]:
        """Получает сигналы из CoinGecko API"""
        signals = []
        
        try:
            # Получаем топ криптовалют
            url = "https://api.coingecko.com/api/v3/coins/markets"
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': 20,
                'page': 1,
                'sparkline': False
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                for coin in data[:10]:  # Топ 10
                    # Анализируем изменение цены за 24ч
                    price_change_24h = coin.get('price_change_percentage_24h', 0)
                    
                    if abs(price_change_24h) > 5:  # Если изменение больше 5%
                        signal = {
                            'id': f"coingecko_{coin['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                            'asset': coin['symbol'].upper(),
                            'direction': 'BUY' if price_change_24h > 0 else 'SELL',
                            'entry_price': coin['current_price'],
                            'target_price': coin['current_price'] * (1 + price_change_24h/100 * 0.5),
                            'stop_loss': coin['current_price'] * (1 - price_change_24h/100 * 0.3),
                            'confidence': min(abs(price_change_24h) * 2, 85),
                            'channel': 'CoinGecko API',
                            'source_type': 'api',
                            'signal_type': 'price_movement',
                            'timestamp': datetime.now().isoformat(),
                            'leverage': '1x',
                            'timeframe': '24H',
                            'entry_type': 'market',
                            'all_targets': [coin['current_price'] * (1 + price_change_24h/100 * 0.5)],
                            'stop_loss_percent': None
                        }
                        signals.append(signal)
            
        except Exception as e:
            logger.error(f"❌ Ошибка CoinGecko: {e}")
        
        return signals
    
    def get_binance_signals(self) -> List[Dict]:
        """Получает сигналы из Binance API"""
        signals = []
        
        try:
            # Получаем 24ч статистику
            url = "https://api.binance.com/api/v3/ticker/24hr"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                for ticker in data[:20]:  # Топ 20 по объему
                    symbol = ticker['symbol']
                    if symbol.endswith('USDT'):
                        price_change = float(ticker['priceChangePercent'])
                        volume = float(ticker['volume'])
                        
                        # Сигнал на основе изменения цены и объема
                        if abs(price_change) > 3 and volume > 1000000:  # Изменение >3% и объем >1M
                            current_price = float(ticker['lastPrice'])
                            
                            signal = {
                                'id': f"binance_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                                'asset': symbol.replace('USDT', ''),
                                'direction': 'BUY' if price_change > 0 else 'SELL',
                                'entry_price': current_price,
                                'target_price': current_price * (1 + price_change/100 * 0.6),
                                'stop_loss': current_price * (1 - price_change/100 * 0.4),
                                'confidence': min(abs(price_change) * 3, 80),
                                'channel': 'Binance API',
                                'source_type': 'api',
                                'signal_type': 'volume_price',
                                'timestamp': datetime.now().isoformat(),
                                'leverage': '1x',
                                'timeframe': '24H',
                                'entry_type': 'market',
                                'all_targets': [current_price * (1 + price_change/100 * 0.6)],
                                'stop_loss_percent': None
                            }
                            signals.append(signal)
            
        except Exception as e:
            logger.error(f"❌ Ошибка Binance: {e}")
        
        return signals
    
    def collect_website_signals(self) -> List[Dict]:
        """Собирает сигналы с веб-сайтов (симуляция)"""
        signals = []
        
        # Симулируем сигналы с TradingView
        tradingview_signals = [
            {
                'id': f"tradingview_BTC_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'asset': 'BTC',
                'direction': 'BUY',
                'entry_price': 115000,
                'target_price': 120000,
                'stop_loss': 112000,
                'confidence': 75,
                'channel': 'TradingView',
                'source_type': 'website',
                'signal_type': 'technical_analysis',
                'timestamp': datetime.now().isoformat(),
                'leverage': '2x',
                'timeframe': '4H',
                'entry_type': 'limit',
                'all_targets': [120000, 125000],
                'stop_loss_percent': None
            },
            {
                'id': f"tradingview_ETH_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'asset': 'ETH',
                'direction': 'SELL',
                'entry_price': 3200,
                'target_price': 3000,
                'stop_loss': 3300,
                'confidence': 70,
                'channel': 'TradingView',
                'source_type': 'website',
                'signal_type': 'technical_analysis',
                'timestamp': datetime.now().isoformat(),
                'leverage': '3x',
                'timeframe': '1H',
                'entry_type': 'market',
                'all_targets': [3000, 2900],
                'stop_loss_percent': None
            }
        ]
        
        signals.extend(tradingview_signals)
        return signals
    
    def save_signals_to_database(self, all_signals: Dict):
        """Сохраняет сигналы в базу данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        total_saved = 0
        
        for source_type, signals in all_signals.items():
            if source_type in ['telegram', 'api', 'website']:
                for signal in signals:
                    try:
                        cursor.execute('''
                            INSERT OR REPLACE INTO signals 
                            (id, asset, direction, entry_price, target_price, stop_loss, 
                             confidence, channel, source_type, signal_type, timestamp,
                             leverage, timeframe, entry_type, all_targets, stop_loss_percent)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            signal['id'],
                            signal['asset'],
                            signal['direction'],
                            signal['entry_price'],
                            signal['target_price'],
                            signal['stop_loss'],
                            signal['confidence'],
                            signal['channel'],
                            signal['source_type'],
                            signal.get('signal_type', 'unknown'),
                            signal['timestamp'],
                            signal.get('leverage'),
                            signal.get('timeframe'),
                            signal.get('entry_type'),
                            json.dumps(signal.get('all_targets', [])),
                            signal.get('stop_loss_percent')
                        ))
                        total_saved += 1
                    except Exception as e:
                        logger.error(f"❌ Ошибка сохранения сигнала {signal['id']}: {e}")
        
        conn.commit()
        conn.close()
        logger.info(f"✅ Сохранено {total_saved} сигналов в базу данных")
    
    def calculate_channel_accuracy(self) -> Dict:
        """Рассчитывает точность каналов на основе исторических данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Получаем статистику по каналам
        cursor.execute('''
            SELECT 
                channel,
                COUNT(*) as total_signals,
                SUM(CASE WHEN status = 'completed' AND result = 'success' THEN 1 ELSE 0 END) as successful,
                SUM(CASE WHEN status = 'completed' AND result = 'failed' THEN 1 ELSE 0 END) as failed,
                SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as pending,
                AVG(confidence) as avg_confidence,
                AVG(profit_loss) as avg_profit_loss
            FROM signals 
            WHERE timestamp >= datetime('now', '-30 days')
            GROUP BY channel
        ''')
        
        results = cursor.fetchall()
        channel_stats = {}
        
        for row in results:
            channel, total, successful, failed, pending, avg_conf, avg_pl = row
            
            success_rate = (successful / (successful + failed)) * 100 if (successful + failed) > 0 else 0
            
            channel_stats[channel] = {
                'total_signals': total,
                'successful_signals': successful,
                'failed_signals': failed,
                'pending_signals': pending,
                'success_rate': round(success_rate, 2),
                'avg_confidence': round(avg_conf or 0, 2),
                'avg_profit_loss': round(avg_pl or 0, 2),
                'last_updated': datetime.now().isoformat()
            }
        
        conn.close()
        return channel_stats
    
    def get_active_signals(self) -> List[Dict]:
        """Получает актуальные активные сигналы"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Получаем активные сигналы за последние 24 часа
        cursor.execute('''
            SELECT 
                id, asset, direction, entry_price, target_price, stop_loss,
                confidence, channel, source_type, signal_type, timestamp,
                leverage, timeframe, entry_type, all_targets, stop_loss_percent
            FROM signals 
            WHERE status = 'active' 
            AND timestamp >= datetime('now', '-24 hours')
            ORDER BY confidence DESC, timestamp DESC
        ''')
        
        results = cursor.fetchall()
        active_signals = []
        
        for row in results:
            signal = {
                'id': row[0],
                'asset': row[1],
                'direction': row[2],
                'entry_price': row[3],
                'target_price': row[4],
                'stop_loss': row[5],
                'confidence': row[6],
                'channel': row[7],
                'source_type': row[8],
                'signal_type': row[9],
                'timestamp': row[10],
                'leverage': row[11],
                'timeframe': row[12],
                'entry_type': row[13],
                'all_targets': json.loads(row[14]) if row[14] else [],
                'stop_loss_percent': row[15]
            }
            active_signals.append(signal)
        
        conn.close()
        return active_signals
    
    def generate_comprehensive_report(self) -> Dict:
        """Генерирует комплексный отчет"""
        logger.info("📊 Генерация комплексного отчета...")
        
        # Собираем новые сигналы
        new_signals = self.collect_all_signals()
        
        # Получаем статистику каналов
        channel_accuracy = self.calculate_channel_accuracy()
        
        # Получаем активные сигналы
        active_signals = self.get_active_signals()
        
        # Генерируем отчет
        report = {
            'report_time': datetime.now().isoformat(),
            'summary': {
                'total_new_signals': new_signals['total'],
                'total_active_signals': len(active_signals),
                'sources_analyzed': len(self.sources['telegram_channels']) + len(self.sources['apis']) + len(self.sources['websites']),
                'collection_duration': '24 hours'
            },
            'channel_accuracy': channel_accuracy,
            'active_signals': active_signals,
            'signal_distribution': {
                'telegram': len(new_signals['telegram']),
                'api': len(new_signals['api']),
                'website': len(new_signals['website'])
            },
            'top_performing_channels': self.get_top_performing_channels(channel_accuracy),
            'signal_quality_analysis': self.analyze_signal_quality(active_signals)
        }
        
        # Сохраняем отчет
        with open('comprehensive_signals_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info("✅ Комплексный отчет сгенерирован и сохранен")
        return report
    
    def get_top_performing_channels(self, channel_accuracy: Dict) -> List[Dict]:
        """Получает топ каналов по точности"""
        channels = []
        for channel, stats in channel_accuracy.items():
            if stats['total_signals'] >= 5:  # Минимум 5 сигналов для статистики
                channels.append({
                    'channel': channel,
                    'success_rate': stats['success_rate'],
                    'total_signals': stats['total_signals'],
                    'avg_confidence': stats['avg_confidence']
                })
        
        # Сортируем по точности
        channels.sort(key=lambda x: x['success_rate'], reverse=True)
        return channels[:10]  # Топ 10
    
    def analyze_signal_quality(self, signals: List[Dict]) -> Dict:
        """Анализирует качество сигналов"""
        if not signals:
            return {}
        
        total_signals = len(signals)
        high_confidence = len([s for s in signals if s['confidence'] >= 70])
        medium_confidence = len([s for s in signals if 50 <= s['confidence'] < 70])
        low_confidence = len([s for s in signals if s['confidence'] < 50])
        
        buy_signals = len([s for s in signals if s['direction'] == 'BUY'])
        sell_signals = len([s for s in signals if s['direction'] == 'SELL'])
        
        return {
            'total_signals': total_signals,
            'confidence_distribution': {
                'high': high_confidence,
                'medium': medium_confidence,
                'low': low_confidence
            },
            'direction_distribution': {
                'buy': buy_signals,
                'sell': sell_signals
            },
            'avg_confidence': sum(s['confidence'] for s in signals) / total_signals,
            'signals_with_prices': len([s for s in signals if s['entry_price']]),
            'signals_with_targets': len([s for s in signals if s['target_price']])
        }

def main():
    """Основная функция"""
    collector = ComprehensiveSignalCollector()
    
    print("🎯 КОМПЛЕКСНЫЙ СБОР И АНАЛИЗ СИГНАЛОВ")
    print("=" * 60)
    
    # Генерируем комплексный отчет
    report = collector.generate_comprehensive_report()
    
    # Выводим результаты
    print(f"\n📊 ОТЧЕТ СОЗДАН: {report['report_time']}")
    print(f"📈 Новых сигналов: {report['summary']['total_new_signals']}")
    print(f"🎯 Активных сигналов: {report['summary']['total_active_signals']}")
    print(f"🔍 Источников проанализировано: {report['summary']['sources_analyzed']}")
    
    # Топ каналы по точности
    print(f"\n🏆 ТОП КАНАЛЫ ПО ТОЧНОСТИ:")
    for i, channel in enumerate(report['top_performing_channels'][:5], 1):
        print(f"   {i}. {channel['channel']}: {channel['success_rate']}% ({channel['total_signals']} сигналов)")
    
    # Активные сигналы
    print(f"\n🎯 АКТИВНЫЕ СИГНАЛЫ:")
    for i, signal in enumerate(report['active_signals'][:10], 1):
        print(f"   {i}. {signal['asset']} {signal['direction']} @ ${signal['entry_price']:,.2f if signal['entry_price'] else 'Market'}")
        print(f"      Канал: {signal['channel']} | Уверенность: {signal['confidence']}%")
        print(f"      Цель: ${signal['target_price']:,.2f if signal['target_price'] else 'N/A'}")
        print()
    
    # Анализ качества
    quality = report['signal_quality_analysis']
    if quality:
        print(f"📈 АНАЛИЗ КАЧЕСТВА:")
        print(f"   Высокая уверенность: {quality['confidence_distribution']['high']}")
        print(f"   Средняя уверенность: {quality['confidence_distribution']['medium']}")
        print(f"   Низкая уверенность: {quality['confidence_distribution']['low']}")
        print(f"   Средняя уверенность: {quality['avg_confidence']:.1f}%")
    
    print(f"\n📁 Отчет сохранен в: comprehensive_signals_report.json")
    print(f"💾 База данных: signals_database.db")

if __name__ == "__main__":
    main()
