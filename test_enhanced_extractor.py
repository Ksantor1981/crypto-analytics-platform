#!/usr/bin/env python3
"""
Тест улучшенного экстрактора цен на реальных данных
"""

import sys
import os
sys.path.append('workers')

from enhanced_price_extractor import EnhancedPriceExtractor

def test_real_telegram_message():
    """Тестирует экстрактор на реальном сообщении из Telegram"""
    
    extractor = EnhancedPriceExtractor()
    
    # Реальное сообщение из Telegram
    real_message = "#BTCIf weekly candle closes below 114311 then BTC will look for Daily FVG (110532 - 109241) for a potential bounce however if fails to bounce then daily OB+ (103450 - 98455) But i think at some point of time BTC will test structure breaking WFVG 92880 - 86520 may be in september.In short BTC has a potential to bounce from 110532 for a relief@cryptosignals"
    
    print("🔍 Тестируем улучшенный экстрактор на реальном сообщении:")
    print(f"Сообщение: {real_message}")
    print("-" * 80)
    
    # Извлекаем цены
    prices = extractor.extract_prices(real_message)
    print(f"📊 Извлеченные цены:")
    print(f"Entry: {prices['entry_price']}")
    print(f"Target: {prices['target_price']}")
    print(f"Stop Loss: {prices['stop_loss']}")
    
    # Извлекаем направление
    direction = extractor.extract_direction(real_message)
    print(f"📈 Направление: {direction}")
    
    # Извлекаем актив
    asset = extractor.extract_asset(real_message)
    print(f"💰 Актив: {asset}")
    
    # Полный сигнал
    signal = extractor.extract_signal(real_message, "cryptosignals", "msg_test")
    print(f"🎯 Полный сигнал:")
    print(f"ID: {signal['id']}")
    print(f"Asset: {signal['asset']}")
    print(f"Direction: {signal['direction']}")
    print(f"Entry: {signal['entry_price']}")
    print(f"Target: {signal['target_price']}")
    print(f"Stop Loss: {signal['stop_loss']}")
    print(f"Confidence: {signal['real_confidence']}")
    print(f"Quality: {signal['signal_quality']}")
    print(f"Valid: {signal['is_valid']}")
    
    return signal

def test_multiple_messages():
    """Тестирует на нескольких типах сообщений"""
    
    extractor = EnhancedPriceExtractor()
    
    test_messages = [
        "#BTCIf weekly candle closes below 114311 then BTC will look for Daily FVG (110532 - 109241) for a potential bounce",
        "ETH LONG Entry: 3000, Target: 3200, Stop Loss: 2950",
        "ADA/USDT: Support Level Test Cardano testing key support level at 0.42. Long entry at 0.45, target 0.55, stop loss at 0.42",
        "SOL SHORT @ 130, TP: 115, SL: 135",
        "Bitcoin SHORT Entry at 50200, Target 48500, Stop Loss 51500"
    ]
    
    print("\n🧪 Тестируем на разных типах сообщений:")
    print("=" * 80)
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n📝 Тест {i}:")
        print(f"Сообщение: {message}")
        
        signal = extractor.extract_signal(message, f"test_channel_{i}", f"msg_{i}")
        
        print(f"✅ Результат:")
        print(f"   Asset: {signal['asset']}")
        print(f"   Direction: {signal['direction']}")
        print(f"   Entry: {signal['entry_price']}")
        print(f"   Target: {signal['target_price']}")
        print(f"   Stop Loss: {signal['stop_loss']}")
        print(f"   Valid: {signal['is_valid']}")
        print("-" * 40)

if __name__ == "__main__":
    print("🚀 Запуск тестов улучшенного экстрактора цен...")
    
    # Тест на реальном сообщении
    test_real_telegram_message()
    
    # Тест на множественных сообщениях
    test_multiple_messages()
    
    print("\n✅ Тестирование завершено!")
