print("Hello World!")
print("Testing Python execution")

# Тестируем парсер структурированных сигналов
import re

test_text = """
SIGNAL ID: #1956
COIN: $BTC/USDT (3-5x)
Direction: LONG 📈
ENTRY: 112207 - 110500
TARGETS: 113500 - 114800 - 117000 - 123236
STOP LOSS: 109638
"""

# Простой тест извлечения
signal_id_match = re.search(r'SIGNAL\s+ID[:\s]*#?(\d+)', test_text, re.IGNORECASE)
if signal_id_match:
    print(f"✅ Signal ID: {signal_id_match.group(1)}")

asset_match = re.search(r'COIN[:\s]*\$?([A-Z]+)/?([A-Z]*)', test_text, re.IGNORECASE)
if asset_match:
    base = asset_match.group(1)
    quote = asset_match.group(2) if len(asset_match.groups()) > 1 else "USDT"
    print(f"✅ Asset: {base}/{quote}")

direction_match = re.search(r'(LONG|SHORT|BUY|SELL)', test_text, re.IGNORECASE)
if direction_match:
    print(f"✅ Direction: {direction_match.group(1)}")

entry_match = re.search(r'ENTRY[:\s]*(\d+)\s*[-–—]\s*(\d+)', test_text, re.IGNORECASE)
if entry_match:
    start = float(entry_match.group(1))
    end = float(entry_match.group(2))
    print(f"✅ Entry Range: {start} - {end}")

print("✅ Тест завершен успешно!")
