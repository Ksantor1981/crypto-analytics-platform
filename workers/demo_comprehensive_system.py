"""
Демонстрация комплексной системы сбора и анализа сигналов
"""

import json
import os
from datetime import datetime

def create_demo_data():
    """Создает демонстрационные данные для тестирования"""
    
    # Демонстрационные сигналы
    demo_signals = [
        {
            'id': f"demo_binancekillers_btc_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'asset': 'BTC',
            'direction': 'LONG',
            'entry_price': 115000,
            'target_price': 120000,
            'stop_loss': 112000,
            'confidence': 95.0,
            'channel': 'BinanceKillers',
            'source_type': 'telegram',
            'signal_type': 'structured',
            'timestamp': datetime.now().isoformat(),
            'leverage': '3-5x',
            'timeframe': '4H',
            'entry_type': 'range',
            'all_targets': [120000, 125000, 130000],
            'stop_loss_percent': None
        },
        {
            'id': f"demo_wolf_band_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'asset': 'BAND',
            'direction': 'SHORT',
            'entry_price': 1.0875,
            'target_price': 1.0590,
            'stop_loss': 1.1340,
            'confidence': 90.0,
            'channel': 'Wolf of Trading',
            'source_type': 'telegram',
            'signal_type': 'structured',
            'timestamp': datetime.now().isoformat(),
            'leverage': '20x',
            'timeframe': '1H',
            'entry_type': 'range',
            'all_targets': [1.0590, 1.0480, 1.0370, 1.0260, 1.0150, 1.0040],
            'stop_loss_percent': None
        },
        {
            'id': f"demo_coingecko_eth_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'asset': 'ETH',
            'direction': 'BUY',
            'entry_price': 3200,
            'target_price': 3400,
            'stop_loss': 3100,
            'confidence': 75.0,
            'channel': 'CoinGecko API',
            'source_type': 'api',
            'signal_type': 'price_movement',
            'timestamp': datetime.now().isoformat(),
            'leverage': '1x',
            'timeframe': '24H',
            'entry_type': 'market',
            'all_targets': [3400],
            'stop_loss_percent': None
        },
        {
            'id': f"demo_binance_sol_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'asset': 'SOL',
            'direction': 'SELL',
            'entry_price': 150,
            'target_price': 140,
            'stop_loss': 155,
            'confidence': 80.0,
            'channel': 'Binance API',
            'source_type': 'api',
            'signal_type': 'volume_price',
            'timestamp': datetime.now().isoformat(),
            'leverage': '1x',
            'timeframe': '24H',
            'entry_type': 'market',
            'all_targets': [140],
            'stop_loss_percent': None
        },
        {
            'id': f"demo_tradingview_btc_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'asset': 'BTC',
            'direction': 'BUY',
            'entry_price': 115000,
            'target_price': 120000,
            'stop_loss': 112000,
            'confidence': 75.0,
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
            'id': f"demo_crypto_inner_bsw_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'asset': 'BSW',
            'direction': 'SHORT',
            'entry_price': 0.01862,
            'target_price': 0.01834,
            'stop_loss': None,
            'confidence': 85.0,
            'channel': 'Crypto Inner Circle',
            'source_type': 'telegram',
            'signal_type': 'structured',
            'timestamp': datetime.now().isoformat(),
            'leverage': '25x',
            'timeframe': '1H',
            'entry_type': 'limit',
            'all_targets': [0.01834, 0.01815, 0.01797, 0.01769, 0.01750, 0.01722],
            'stop_loss_percent': 7.5
        }
    ]
    
    # Демонстрационная статистика каналов
    demo_channel_accuracy = {
        'BinanceKillers': {
            'total_signals': 45,
            'successful_signals': 38,
            'failed_signals': 7,
            'pending_signals': 0,
            'success_rate': 84.4,
            'avg_confidence': 92.5,
            'avg_profit_loss': 15.2,
            'last_updated': datetime.now().isoformat()
        },
        'Wolf of Trading': {
            'total_signals': 32,
            'successful_signals': 26,
            'failed_signals': 6,
            'pending_signals': 0,
            'success_rate': 81.3,
            'avg_confidence': 88.7,
            'avg_profit_loss': 12.8,
            'last_updated': datetime.now().isoformat()
        },
        'Crypto Inner Circle': {
            'total_signals': 28,
            'successful_signals': 22,
            'failed_signals': 6,
            'pending_signals': 0,
            'success_rate': 78.6,
            'avg_confidence': 85.2,
            'avg_profit_loss': 11.5,
            'last_updated': datetime.now().isoformat()
        },
        'CoinGecko API': {
            'total_signals': 67,
            'successful_signals': 48,
            'failed_signals': 19,
            'pending_signals': 0,
            'success_rate': 71.6,
            'avg_confidence': 72.3,
            'avg_profit_loss': 8.9,
            'last_updated': datetime.now().isoformat()
        },
        'Binance API': {
            'total_signals': 89,
            'successful_signals': 62,
            'failed_signals': 27,
            'pending_signals': 0,
            'success_rate': 69.7,
            'avg_confidence': 75.8,
            'avg_profit_loss': 9.2,
            'last_updated': datetime.now().isoformat()
        },
        'TradingView': {
            'total_signals': 23,
            'successful_signals': 15,
            'failed_signals': 8,
            'pending_signals': 0,
            'success_rate': 65.2,
            'avg_confidence': 78.4,
            'avg_profit_loss': 10.1,
            'last_updated': datetime.now().isoformat()
        }
    }
    
    # Создаем демонстрационный отчет
    demo_report = {
        'report_time': datetime.now().isoformat(),
        'summary': {
            'total_new_signals': len(demo_signals),
            'total_active_signals': len(demo_signals),
            'sources_analyzed': 28,
            'collection_duration': '24 hours'
        },
        'channel_accuracy': demo_channel_accuracy,
        'active_signals': demo_signals,
        'signal_distribution': {
            'telegram': 3,
            'api': 2,
            'website': 1
        },
        'top_performing_channels': [
            {'channel': 'BinanceKillers', 'success_rate': 84.4, 'total_signals': 45, 'avg_confidence': 92.5},
            {'channel': 'Wolf of Trading', 'success_rate': 81.3, 'total_signals': 32, 'avg_confidence': 88.7},
            {'channel': 'Crypto Inner Circle', 'success_rate': 78.6, 'total_signals': 28, 'avg_confidence': 85.2},
            {'channel': 'CoinGecko API', 'success_rate': 71.6, 'total_signals': 67, 'avg_confidence': 72.3},
            {'channel': 'Binance API', 'success_rate': 69.7, 'total_signals': 89, 'avg_confidence': 75.8}
        ],
        'signal_quality_analysis': {
            'total_signals': len(demo_signals),
            'confidence_distribution': {
                'high': 4,
                'medium': 2,
                'low': 0
            },
            'direction_distribution': {
                'buy': 3,
                'sell': 3
            },
            'avg_confidence': sum(s['confidence'] for s in demo_signals) / len(demo_signals),
            'signals_with_prices': len([s for s in demo_signals if s['entry_price']]),
            'signals_with_targets': len([s for s in demo_signals if s['target_price']])
        }
    }
    
    return demo_report

def main():
    """Основная функция демонстрации"""
    
    print("🎯 ДЕМОНСТРАЦИЯ КОМПЛЕКСНОЙ СИСТЕМЫ АНАЛИЗА СИГНАЛОВ")
    print("=" * 60)
    
    # Создаем демонстрационные данные
    print("📊 Создание демонстрационных данных...")
    demo_report = create_demo_data()
    
    # Сохраняем отчет
    with open('comprehensive_signals_report.json', 'w', encoding='utf-8') as f:
        json.dump(demo_report, f, ensure_ascii=False, indent=2)
    
    print("✅ Демонстрационный отчет создан!")
    
    # Выводим статистику
    print(f"\n📈 СТАТИСТИКА:")
    print(f"   Всего сигналов: {demo_report['summary']['total_new_signals']}")
    print(f"   Активных сигналов: {demo_report['summary']['total_active_signals']}")
    print(f"   Источников проанализировано: {demo_report['summary']['sources_analyzed']}")
    
    # Топ каналы
    print(f"\n🏆 ТОП КАНАЛЫ ПО ТОЧНОСТИ:")
    for i, channel in enumerate(demo_report['top_performing_channels'][:5], 1):
        print(f"   {i}. {channel['channel']}: {channel['success_rate']}% ({channel['total_signals']} сигналов)")
    
    # Активные сигналы
    print(f"\n🎯 АКТИВНЫЕ СИГНАЛЫ:")
    for i, signal in enumerate(demo_report['active_signals'], 1):
        entry_price = f"${signal['entry_price']:,.2f}" if signal['entry_price'] else 'Market'
        target_price = f"${signal['target_price']:,.2f}" if signal['target_price'] else 'N/A'
        print(f"   {i}. {signal['asset']} {signal['direction']} @ {entry_price}")
        print(f"      Канал: {signal['channel']} | Уверенность: {signal['confidence']}%")
        print(f"      Цель: {target_price} | Плечо: {signal['leverage']}")
        print()
    
    # Анализ качества
    quality = demo_report['signal_quality_analysis']
    print(f"📊 АНАЛИЗ КАЧЕСТВА:")
    print(f"   Высокая уверенность: {quality['confidence_distribution']['high']}")
    print(f"   Средняя уверенность: {quality['confidence_distribution']['medium']}")
    print(f"   Низкая уверенность: {quality['confidence_distribution']['low']}")
    print(f"   Средняя уверенность: {quality['avg_confidence']:.1f}%")
    print(f"   Сигналов с ценами: {quality['signals_with_prices']}")
    print(f"   Сигналов с целями: {quality['signals_with_targets']}")
    
    print(f"\n🎉 Демонстрация завершена!")
    print(f"📁 Отчет сохранен в: comprehensive_signals_report.json")
    print(f"🌐 Откройте comprehensive_dashboard.html для просмотра дашборда")
    
    # Проверяем наличие дашборда
    if os.path.exists('comprehensive_dashboard.html'):
        print(f"✅ Дашборд найден: comprehensive_dashboard.html")
    else:
        print(f"⚠️ Дашборд не найден. Создайте comprehensive_dashboard.html")

if __name__ == "__main__":
    main()
