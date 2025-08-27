"""
Анализатор реальных Telegram сигналов
"""

import json
from datetime import datetime

def analyze_signals():
    """Анализирует реальные сигналы из Telegram"""
    
    with open('enhanced_telegram_signals.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print('🎯 АНАЛИЗ РЕАЛЬНЫХ TELEGRAM СИГНАЛОВ')
    print('=' * 60)
    
    # Фильтруем реальные криптовалюты
    real_cryptos = {
        'BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOGE', 'DOT', 'LINK', 'UNI', 'AVAX', 
        'MATIC', 'ATOM', 'LTC', 'BCH', 'BNB', 'SYS', 'ENA', 'ZIG', 'ATA'
    }
    
    all_signals = data['signals']
    real_signals = [s for s in all_signals if s['asset'] in real_cryptos]
    
    print(f'📊 Общая статистика:')
    print(f'   Всего извлечено: {len(all_signals)} сигналов')
    print(f'   Реальные криптовалюты: {len(real_signals)} сигналов')
    print(f'   Точность фильтрации: {len(real_signals)/len(all_signals)*100:.1f}%')
    print()
    
    # Статистика по каналам
    print('📺 Статистика по каналам:')
    channel_stats = {}
    for signal in real_signals:
        channel = signal['channel']
        if channel not in channel_stats:
            channel_stats[channel] = {'total': 0, 'with_price': 0, 'avg_confidence': []}
        
        channel_stats[channel]['total'] += 1
        channel_stats[channel]['avg_confidence'].append(signal['confidence'])
        if signal['entry_price']:
            channel_stats[channel]['with_price'] += 1
    
    for channel, stats in channel_stats.items():
        avg_conf = sum(stats['avg_confidence']) / len(stats['avg_confidence'])
        print(f'   {channel}: {stats["total"]} сигналов, {stats["with_price"]} с ценой, средняя уверенность {avg_conf:.1f}%')
    print()
    
    # ТОП сигналы с ценами
    print('💰 ТОП сигналы с ценами:')
    priced_signals = [s for s in real_signals if s['entry_price']]
    priced_signals.sort(key=lambda x: x['confidence'], reverse=True)
    
    for i, signal in enumerate(priced_signals[:10], 1):
        entry = f"${signal['entry_price']}" if signal['entry_price'] else 'Market'
        target = f" → ${signal['target_price']}" if signal['target_price'] else ''
        bybit = '✅' if signal['bybit_available'] else '❌'
        
        print(f'{i:2d}. {signal["asset"]} {signal["direction"]} {entry}{target}')
        print(f'    Confidence: {signal["confidence"]}% | Bybit: {bybit} | {signal["channel"]}')
        print(f'    Text: {signal["original_text"][:80]}...')
        print()
    
    # Статистика по направлениям
    print('📈 Распределение по направлениям:')
    directions = {}
    for signal in real_signals:
        direction = signal['direction']
        directions[direction] = directions.get(direction, 0) + 1
    
    for direction, count in sorted(directions.items(), key=lambda x: x[1], reverse=True):
        print(f'   {direction}: {count} сигналов ({count/len(real_signals)*100:.1f}%)')
    print()
    
    # Статистика по криптовалютам
    print('🪙 ТОП криптовалюты:')
    assets = {}
    for signal in real_signals:
        asset = signal['asset']
        assets[asset] = assets.get(asset, 0) + 1
    
    for asset, count in sorted(assets.items(), key=lambda x: x[1], reverse=True)[:10]:
        bybit_available = any(s['bybit_available'] for s in real_signals if s['asset'] == asset)
        bybit_status = '✅' if bybit_available else '❌'
        print(f'   {asset}: {count} сигналов {bybit_status}')
    print()
    
    # Bybit доступность
    bybit_available = sum(1 for s in real_signals if s['bybit_available'])
    print(f'🏦 Bybit доступность: {bybit_available}/{len(real_signals)} ({bybit_available/len(real_signals)*100:.1f}%)')
    
    return {
        'total_signals': len(all_signals),
        'real_signals': len(real_signals),
        'accuracy': len(real_signals)/len(all_signals)*100,
        'channels': len(channel_stats),
        'bybit_available': bybit_available,
        'top_assets': list(sorted(assets.items(), key=lambda x: x[1], reverse=True)[:5])
    }

if __name__ == "__main__":
    stats = analyze_signals()
