"""
Тестовый файл для проверки импортов
"""

print("=== Тест импортов ===")

try:
    print("1. Импорт improved_signal_parser...")
    from improved_signal_parser import ImprovedSignal, ImprovedSignalExtractor, SignalDirection, SignalQuality
    print("✅ improved_signal_parser импортирован успешно")
except Exception as e:
    print(f"❌ Ошибка импорта improved_signal_parser: {e}")

try:
    print("2. Импорт real_telegram_parser...")
    from real_telegram_parser import RealTelegramParser
    print("✅ real_telegram_parser импортирован успешно")
except Exception as e:
    print(f"❌ Ошибка импорта real_telegram_parser: {e}")

try:
    print("3. Импорт simple_reddit_parser...")
    from simple_reddit_parser import SimpleRedditParser
    print("✅ simple_reddit_parser импортирован успешно")
except Exception as e:
    print(f"❌ Ошибка импорта simple_reddit_parser: {e}")

try:
    print("4. Импорт simple_tradingview_parser...")
    from simple_tradingview_parser import SimpleTradingViewParser
    print("✅ simple_tradingview_parser импортирован успешно")
except Exception as e:
    print(f"❌ Ошибка импорта simple_tradingview_parser: {e}")

try:
    print("5. Импорт integrated_signal_processor...")
    from integrated_signal_processor import IntegratedSignalProcessor
    print("✅ integrated_signal_processor импортирован успешно")
except Exception as e:
    print(f"❌ Ошибка импорта integrated_signal_processor: {e}")

try:
    print("6. Импорт signal_quality_analyzer...")
    from signal_quality_analyzer import SignalQualityAnalyzer, QualityScore
    print("✅ signal_quality_analyzer импортирован успешно")
except Exception as e:
    print(f"❌ Ошибка импорта signal_quality_analyzer: {e}")

print("\n=== Тест завершен ===")
