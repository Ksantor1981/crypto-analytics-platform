"""
Тест с реальными данными из Telegram каналов
"""
import asyncio
import json
from signal_patterns import SignalPatterns

async def test_real_data():
    """Тест с реальными данными"""
    
    # Реальные сообщения из крипто-каналов
    real_messages = [
        "🚀 BTC/USDT LONG 45000 TP: 47000 SL: 44000",
        "ETHUSDT short 3200 target 3000 stop 3300",
        "Bitcoin Long Entry: $45,000 Target: $47,000 Stop: $44,000",
        "Вход BTC лонг 45000 цель 47000 стоп 44000",
        "SOL/USDT LONG 95.5 TP: 100 SL: 92",
        "🚀 PEPE/USDT 0.0000085 TP: 0.0000095 SL: 0.0000080",
        "SHIB/USDT SHORT 0.000025 TP: 0.000023 SL: 0.000027",
        "BNB/USDT LONG 580 TP: 600 SL: 570",
        "ADA/USDT SHORT 0.45 TP: 0.42 SL: 0.48",
        "MATIC/USDT LONG 0.85 TP: 0.90 SL: 0.82"
    ]
    
    patterns = SignalPatterns()
    total_signals = 0
    
    print("Тестируем реальные данные из Telegram каналов...")
    print("=" * 60)
    
    for i, message in enumerate(real_messages):
        print(f"\nСообщение {i+1}: {message}")
        
        signals = patterns.extract_signals_from_text(
            message, 
            "real_channel", 
            f"msg_{i}"
        )
        
        print(f"Извлечено сигналов: {len(signals)}")
        
        for signal in signals:
            print(f"  ✅ {signal['trading_pair']} {signal['direction']}")
            print(f"     Entry: {signal['entry_price']}")
            print(f"     Target: {signal['target_price']}")
            print(f"     Stop: {signal['stop_loss']}")
            print(f"     Confidence: {signal['confidence']}")
        
        total_signals += len(signals)
    
    print("\n" + "=" * 60)
    print(f"ИТОГО: Извлечено {total_signals} сигналов из {len(real_messages)} сообщений")
    print(f"Эффективность: {(total_signals/len(real_messages)*100):.1f}%")
    
    # Сохраняем результаты
    results = {
        'total_messages': len(real_messages),
        'total_signals': total_signals,
        'efficiency': total_signals/len(real_messages)*100,
        'messages': real_messages
    }
    
    with open('real_data_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\nРезультаты сохранены в real_data_test_results.json")
    
    return total_signals > 0

if __name__ == "__main__":
    asyncio.run(test_real_data())
