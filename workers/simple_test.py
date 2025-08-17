"""
Простой тест паттернов
"""
import re
from signal_patterns import SignalPatterns

def test_patterns():
    """Тест паттернов"""
    patterns = SignalPatterns()
    
    # Тестовые тексты
    test_texts = [
        "BTC/USDT LONG 45000 TP: 47000 SL: 44000",
        "ETHUSDT short 3200 target 3000 stop 3300",
        "🚀 BTC 45000 📈 47000 📉 44000",
        "Bitcoin Long Entry: $45,000 Target: $47,000 Stop: $44,000",
        "Вход BTC лонг 45000 цель 47000 стоп 44000"
    ]
    
    print("Тестируем паттерны...")
    
    for i, text in enumerate(test_texts):
        print(f"\nТест {i+1}: {text}")
        
        # Тест извлечения пар
        pairs = patterns._extract_trading_pairs(text)
        print(f"  Пары: {pairs}")
        
        # Тест извлечения направления
        direction = patterns._extract_direction(text)
        print(f"  Направление: {direction}")
        
        # Тест извлечения цен
        prices = patterns._extract_prices(text)
        print(f"  Цены: {prices}")
        
        # Тест полного извлечения
        signals = patterns.extract_signals_from_text(text, "test", f"msg_{i}")
        print(f"  Сигналы: {len(signals)}")
        for signal in signals:
            print(f"    - {signal}")

if __name__ == "__main__":
    test_patterns()
