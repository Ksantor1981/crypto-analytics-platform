"""
Простой тест универсального парсера
"""

import sys
import os

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from universal_signal_parser import UniversalSignalParser
    
    print("✅ Парсер успешно импортирован!")
    
    # Тестируем на простом примере
    parser = UniversalSignalParser()
    
    test_text = """
    SIGNAL ID: #1956
    COIN: $BTC/USDT (3-5x)
    Direction: LONG 📈
    ENTRY: 112207 - 110500
    TARGETS: 113500 - 114800 - 117000 - 123236
    STOP LOSS: 109638
    """
    
    signal = parser.parse_signal(test_text, "BinanceKillers")
    
    if signal:
        print("✅ Сигнал успешно извлечен!")
        print(f"Asset: {signal.asset}")
        print(f"Direction: {signal.direction}")
        print(f"Entry Range: {signal.entry_range}")
        print(f"Targets: {signal.targets}")
        print(f"Stop Loss: {signal.stop_loss}")
        print(f"Leverage: {signal.leverage}")
    else:
        print("❌ Не удалось извлечь сигнал")
        
except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
