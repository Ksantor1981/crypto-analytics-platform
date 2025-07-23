#!/usr/bin/env python3
"""
Test script for enhanced price_checker.py
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('.'))

from workers.exchange.price_checker import PriceChecker

async def test_price_checker():
    """Test the enhanced price checker functionality"""
    
    print("🔍 Testing Enhanced Price Checker...")
    print("=" * 50)
    
    # Initialize price checker
    checker = PriceChecker()
    
    # Test 1: Current price fetching
    print("\n1. Testing current price fetching...")
    test_symbols = ['BTC/USDT', 'ETH/USDT', 'ADA/USDT']
    
    for symbol in test_symbols:
        try:
            price = await checker.get_current_price(symbol)
            if price:
                print(f"✅ {symbol}: ${price:,.2f}")
            else:
                print(f"❌ {symbol}: Failed to fetch price")
        except Exception as e:
            print(f"❌ {symbol}: Error - {e}")
    
    # Test 2: Historical data fetching
    print("\n2. Testing historical data fetching...")
    
    # Get data for the last 24 hours
    end_time = int(datetime.now().timestamp() * 1000)
    start_time = end_time - (24 * 60 * 60 * 1000)  # 24 hours ago
    
    try:
        klines = await checker.get_binance_klines('BTC/USDT', start_time, end_time, '1h')
        if klines:
            print(f"✅ Retrieved {len(klines)} hourly klines for BTC/USDT")
            print(f"   Latest price: ${klines[-1]['close']:,.2f}")
            print(f"   24h High: ${max(k['high'] for k in klines):,.2f}")
            print(f"   24h Low: ${min(k['low'] for k in klines):,.2f}")
        else:
            print("❌ Failed to fetch historical data")
    except Exception as e:
        print(f"❌ Error fetching historical data: {e}")
    
    # Test 3: Signal validation
    print("\n3. Testing signal validation...")
    
    valid_signal = {
        'asset': 'BTC/USDT',
        'direction': 'LONG',
        'entry_price': '45000.00',
        'tp1_price': '46500.00',
        'stop_loss': '43500.00',
        'message_timestamp': datetime.now() - timedelta(hours=2)
    }
    
    invalid_signal = {
        'asset': 'INVALID/PAIR',
        'direction': 'UNKNOWN',
        'entry_price': '-100'
    }
    
    print(f"Valid signal validation: {await checker.validate_signal_data(valid_signal)}")
    print(f"Invalid signal validation: {await checker.validate_signal_data(invalid_signal)}")
    
    # Test 4: Mock signal execution check
    print("\n4. Testing mock signal execution...")
    
    mock_signals = [
        {
            'id': 1,
            'asset': 'BTC/USDT',
            'direction': 'LONG',
            'entry_price': '45000.00',
            'tp1_price': '46500.00',
            'stop_loss': '43500.00',
            'message_timestamp': datetime.now() - timedelta(hours=6)
        },
        {
            'id': 2,
            'asset': 'ETH/USDT',
            'direction': 'SHORT',
            'entry_price': '3200.00',
            'tp1_price': '3100.00',
            'stop_loss': '3250.00',
            'message_timestamp': datetime.now() - timedelta(hours=12)
        }
    ]
    
    try:
        results = await checker.check_multiple_signals(mock_signals)
        print(f"✅ Processed {len(results)} signals")
        
        for result in results:
            print(f"   {result['asset']} {result['direction']}: {result['status']}")
            if result.get('profit_loss_percentage'):
                print(f"      P&L: {result['profit_loss_percentage']:.2f}%")
    except Exception as e:
        print(f"❌ Error checking signals: {e}")
    
    # Test 5: Exchange mapping
    print("\n5. Testing exchange mapping...")
    print(f"Supported exchanges: {len(checker.exchange_mapping)}")
    for asset, exchange in list(checker.exchange_mapping.items())[:5]:
        print(f"   {asset} -> {exchange}")
    print(f"   ... and {len(checker.exchange_mapping) - 5} more")
    
    print("\n" + "=" * 50)
    print("✅ Price Checker tests completed!")

if __name__ == "__main__":
    asyncio.run(test_price_checker()) 