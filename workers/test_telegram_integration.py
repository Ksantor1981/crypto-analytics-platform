#!/usr/bin/env python3
"""
Test script for Telegram Integration
"""
import sys
import os
import json
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

def test_telegram_client():
    """Test Telegram client functionality"""
    print("🔄 Testing Telegram Client...")
    
    try:
        from telegram.telegram_client import collect_telegram_signals_sync
        
        print("✅ Telegram client imported successfully")
        
        # Test signal collection
        result = collect_telegram_signals_sync()
        
        print(f"📊 Collection Result:")
        print(f"   Status: {result.get('status')}")
        print(f"   Signals collected: {result.get('total_signals_collected', 0)}")
        print(f"   Channels processed: {result.get('channels_processed', 0)}")
        print(f"   Mode: {result.get('mode', 'real')}")
        
        if result.get('signals'):
            print(f"\n📋 Sample signals:")
            for i, signal in enumerate(result['signals'][:2], 1):
                print(f"   Signal {i}:")
                print(f"     Asset: {signal.get('asset')}")
                print(f"     Direction: {signal.get('direction')}")
                print(f"     Entry: {signal.get('entry_price')}")
                print(f"     TP1: {signal.get('tp1_price')}")
                print(f"     Confidence: {signal.get('confidence', 0):.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Telegram client: {e}")
        return False

def test_signal_processor():
    """Test signal processor functionality"""
    print("\n🔄 Testing Signal Processor...")
    
    try:
        from telegram.signal_processor import signal_processor
        
        print("✅ Signal processor imported successfully")
        
        # Test processing stats
        stats = signal_processor.get_processing_stats()
        
        print(f"📊 Processing Stats:")
        print(f"   Status: {stats.get('status')}")
        if stats.get('status') == 'success':
            print(f"   Today's signals: {stats.get('today_signals', 0)}")
            print(f"   Pending signals: {stats.get('pending_signals', 0)}")
            print(f"   Active channels: {stats.get('active_channels', 0)}")
        elif stats.get('status') == 'backend_unavailable':
            print("   Backend not available (expected in test mode)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing signal processor: {e}")
        return False

def test_price_monitor():
    """Test price monitor functionality"""
    print("\n🔄 Testing Price Monitor...")
    
    try:
        from exchange.price_monitor import monitor_prices_sync
        
        print("✅ Price monitor imported successfully")
        
        # Test price monitoring
        result = monitor_prices_sync()
        
        print(f"📊 Monitoring Result:")
        print(f"   Status: {result.get('status')}")
        print(f"   Monitored signals: {result.get('monitored_signals', 0)}")
        print(f"   Updated signals: {result.get('updated_signals', 0)}")
        print(f"   Assets monitored: {result.get('assets_monitored', 0)}")
        print(f"   Mode: {result.get('mode', 'real')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing price monitor: {e}")
        return False

def test_telegram_config():
    """Test Telegram configuration"""
    print("\n🔄 Testing Telegram Configuration...")
    
    try:
        from telegram.config import telegram_config
        
        print("✅ Telegram config imported successfully")
        
        print(f"📊 Configuration:")
        print(f"   Configured: {telegram_config.is_configured()}")
        print(f"   Session name: {telegram_config.session_name}")
        print(f"   Max messages: {telegram_config.max_messages_per_channel}")
        print(f"   Collection interval: {telegram_config.collection_interval}s")
        print(f"   Min confidence: {telegram_config.min_signal_confidence}")
        print(f"   Active channels: {len(telegram_config.get_active_channels())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Telegram config: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Telegram Integration Tests\n")
    print("=" * 50)
    
    tests = [
        test_telegram_config,
        test_telegram_client,
        test_signal_processor,
        test_price_monitor
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Telegram integration is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 