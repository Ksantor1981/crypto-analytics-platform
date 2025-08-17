"""
Отладочный тест паттернов
"""
import logging
from signal_patterns import SignalPatterns

# Включаем отладочные сообщения
logging.basicConfig(level=logging.DEBUG)

def debug_test():
    """Отладочный тест"""
    patterns = SignalPatterns()
    
    # Простой тест
    text = "BTC/USDT LONG 45000 TP: 47000 SL: 44000"
    print(f"Тестируем: {text}")
    
    signals = patterns.extract_signals_from_text(text, "test", "msg_1")
    print(f"Результат: {len(signals)} сигналов")
    
    for signal in signals:
        print(f"  - {signal}")

if __name__ == "__main__":
    debug_test()
