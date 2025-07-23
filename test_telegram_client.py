#!/usr/bin/env python3
"""
Test script for enhanced telegram_client.py
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('.'))

from workers.telegram.telegram_client import TelegramSignalCollector

async def test_telegram_client():
    """Test the enhanced telegram client functionality"""
    
    print("📡 Testing Enhanced Telegram Client...")
    print("=" * 50)
    
    # Test 1: Initialize client
    print("\n1. Testing client initialization...")
    collector = TelegramSignalCollector(use_real_config=False)  # Use mock for testing
    
    print(f"✅ Client initialized")
    print(f"   API ID: {collector.api_id}")
    print(f"   Channels: {len(collector.channels)}")
    print(f"   Supported pairs: {len(collector.supported_pairs)}")
    
    # Test 2: Signal parsing
    print("\n2. Testing signal parsing...")
    
    test_messages = [
        {
            'text': '🎯 BTC/USDT LONG\nEntry: 45000\nTP1: 46500\nTP2: 47800\nSL: 43500\nLeverage: 5x',
            'expected': True,
            'description': 'Complete signal with multiple targets'
        },
        {
            'text': '📈 ETH/USDT SHORT Entry: 3200 Target 1: 3100 Target 2: 3000 Stop Loss: 3280',
            'expected': True,
            'description': 'Inline format signal'
        },
        {
            'text': 'ADA/USDT LONG setup Entry: 0.58 Target: 0.62 SL: 0.55',
            'expected': True,
            'description': 'Simple signal format'
        },
        {
            'text': 'BTC @ 45000 going LONG tp 46500 sl 43500',
            'expected': True,
            'description': 'Alternative format with @ symbol'
        },
        {
            'text': 'This is just a news update about the market',
            'expected': False,
            'description': 'Non-signal message'
        },
        {
            'text': 'INVALID/PAIR LONG entry 100 tp 110 sl 90',
            'expected': False,
            'description': 'Unsupported pair'
        }
    ]
    
    for i, test_msg in enumerate(test_messages, 1):
        print(f"\n   Test {i}: {test_msg['description']}")
        
        signal = collector.parse_signal_message(
            test_msg['text'],
            datetime.now(),
            '@test_channel'
        )
        
        if test_msg['expected']:
            if signal:
                print(f"   ✅ Parsed: {signal['asset']} {signal['direction']} @ {signal['entry_price']}")
                print(f"      Confidence: {signal.get('confidence', 0):.2f}")
                if signal.get('tp1_price'):
                    print(f"      TP1: {signal['tp1_price']}")
                if signal.get('stop_loss'):
                    print(f"      SL: {signal['stop_loss']}")
            else:
                print(f"   ❌ Expected signal but got None")
        else:
            if signal:
                print(f"   ❌ Expected None but got signal: {signal['asset']}")
            else:
                print(f"   ✅ Correctly rejected non-signal")
    
    # Test 3: Price relationship validation
    print("\n3. Testing price relationship validation...")
    
    # Valid LONG signal
    valid_long = collector._validate_price_relationships(
        Decimal('100'), [Decimal('110'), Decimal('120')], Decimal('90'), 'LONG'
    )
    print(f"   Valid LONG signal: {valid_long} ✅")
    
    # Invalid LONG signal (target below entry)
    invalid_long = collector._validate_price_relationships(
        Decimal('100'), [Decimal('90')], Decimal('85'), 'LONG'
    )
    print(f"   Invalid LONG signal: {invalid_long} ❌")
    
    # Valid SHORT signal
    valid_short = collector._validate_price_relationships(
        Decimal('100'), [Decimal('90'), Decimal('80')], Decimal('110'), 'SHORT'
    )
    print(f"   Valid SHORT signal: {valid_short} ✅")
    
    # Invalid SHORT signal (target above entry)
    invalid_short = collector._validate_price_relationships(
        Decimal('100'), [Decimal('110')], Decimal('120'), 'SHORT'
    )
    print(f"   Invalid SHORT signal: {invalid_short} ❌")
    
    # Test 4: Confidence calculation
    print("\n4. Testing confidence calculation...")
    
    high_conf_text = "🎯 Strong bullish momentum confirmed breakout BTC/USDT LONG TP1 TP2 TP3"
    high_conf = collector._calculate_signal_confidence(
        high_conf_text, [Decimal('110'), Decimal('120')], Decimal('90'), '@cryptosignals'
    )
    print(f"   High confidence text: {high_conf:.2f}")
    
    low_conf_text = "risky uncertain volatile BTC/USDT maybe long"
    low_conf = collector._calculate_signal_confidence(
        low_conf_text, [Decimal('110')], None, '@unknown'
    )
    print(f"   Low confidence text: {low_conf:.2f}")
    
    # Test 5: Mock signal collection
    print("\n5. Testing mock signal collection...")
    
    try:
        result = await collector.collect_signals()
        
        if result['status'] == 'success':
            print(f"   ✅ Collected {result['total_signals']} signals")
            print(f"   Channel results: {result['channel_results']}")
            
            for i, signal in enumerate(result['signals'][:2], 1):
                print(f"   Signal {i}: {signal['asset']} {signal['direction']}")
                print(f"      Entry: {signal['entry_price']}")
                print(f"      Confidence: {signal.get('confidence', 0):.2f}")
                print(f"      Channel: {signal.get('channel', 'unknown')}")
        else:
            print(f"   ❌ Collection failed: {result.get('message', 'Unknown error')}")
            
    except Exception as e:
        print(f"   ❌ Error during collection: {e}")
    
    # Test 6: Pattern matching
    print("\n6. Testing pattern matching...")
    
    patterns = collector.signal_patterns
    test_text = "BTC/USDT LONG entry at 45000 target 46500 tp2 47000 stop loss 43500 leverage 5x"
    
    for pattern_name, pattern in patterns.items():
        matches = pattern.findall(test_text)
        if matches:
            print(f"   {pattern_name}: {matches}")
    
    print("\n" + "=" * 50)
    print("✅ Telegram Client tests completed!")

if __name__ == "__main__":
    asyncio.run(test_telegram_client()) 