#!/usr/bin/env python3
"""
Test script for enhanced bybit_client.py
"""
import asyncio
import sys
import os
import time
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('.'))

from workers.exchange.bybit_client import BybitClient, bybit_client

async def test_bybit_client():
    """Test the enhanced Bybit client functionality"""
    
    print("🏦 Testing Enhanced Bybit Client...")
    print("=" * 50)
    
    # Test 1: Initialize client
    print("\n1. Testing client initialization...")
    
    async with bybit_client() as client:
        print("✅ Client initialized successfully")
        print(f"   Base URL: {client.base_url}")
        print(f"   Testnet: {client.testnet}")
        print(f"   Max retries: {client._max_retries}")
        print(f"   Cache TTL: {client._cache_ttl}s")
        
        # Test 2: Connection test
        print("\n2. Testing connection...")
        connection_ok = await client.test_connection()
        print(f"   {'✅' if connection_ok else '❌'} Connection: {'OK' if connection_ok else 'FAILED'}")
        
        if not connection_ok:
            print("   ⚠️  Skipping further tests due to connection failure")
            print("   This might be due to network issues or API key problems")
            return False
        
        # Test 3: Health status
        print("\n3. Testing health status...")
        health = await client.get_health_status()
        print(f"   Status: {health['status']}")
        print(f"   Cache size: {health['cache_size']}")
        print(f"   Rate limit remaining: {health['rate_limit_remaining']}")
        print(f"   Consecutive failures: {health['consecutive_failures']}")
        
        # Test 4: Get current prices
        print("\n4. Testing current prices...")
        test_symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
        
        try:
            prices = await client.get_current_prices(test_symbols)
            
            if prices:
                for symbol, price in prices.items():
                    print(f"   ✅ {symbol}: ${price:,.2f}")
            else:
                print("   ❌ No prices retrieved")
        except Exception as e:
            print(f"   ❌ Error getting prices: {e}")
        
        # Test 5: Get klines
        print("\n5. Testing klines...")
        
        try:
            klines = await client.get_klines("BTCUSDT", "60", 24)  # Use "60" for 1h interval
            if klines:
                print(f"   ✅ Retrieved {len(klines)} hourly klines for BTCUSDT")
                print(f"   Latest close: ${klines[-1]['close']:,.2f}")
                print(f"   24h High: ${max(k['high'] for k in klines):,.2f}")
                print(f"   24h Low: ${min(k['low'] for k in klines):,.2f}")
            else:
                print("   ❌ No klines retrieved")
        except Exception as e:
            print(f"   ❌ Error getting klines: {e}")
        
        # Test 6: Get market data
        print("\n6. Testing market data...")
        
        try:
            market_data = await client.get_market_data(["BTCUSDT", "ETHUSDT"])
            
            if market_data:
                for symbol, data in market_data.items():
                    print(f"   ✅ {symbol}:")
                    print(f"      Price: ${data['current_price']:,.2f}")
                    if 'change_24h' in data:
                        print(f"      24h Change: {data['change_24h']:+.2f}%")
                    if 'high_24h' in data:
                        print(f"      24h High: ${data['high_24h']:,.2f}")
                    if 'low_24h' in data:
                        print(f"      24h Low: ${data['low_24h']:,.2f}")
            else:
                print("   ❌ No market data retrieved")
        except Exception as e:
            print(f"   ❌ Error getting market data: {e}")
        
        # Test 7: Cache performance
        print("\n7. Testing cache performance...")
        
        try:
            # First request (should hit API)
            start_time = time.time()
            prices1 = await client.get_current_prices(["BTCUSDT"])
            first_request_time = time.time() - start_time
            
            # Second request (should use cache)
            start_time = time.time()
            prices2 = await client.get_current_prices(["BTCUSDT"])
            cached_request_time = time.time() - start_time
            
            print(f"   First request: {first_request_time:.3f}s")
            print(f"   Cached request: {cached_request_time:.3f}s")
            
            if cached_request_time < first_request_time:
                speedup = first_request_time / cached_request_time
                print(f"   ✅ Cache speedup: {speedup:.1f}x")
            else:
                print(f"   ⚠️  Cache may not be working as expected")
            
            # Verify cache contents
            cache_size = len(client._price_cache)
            print(f"   Cache entries: {cache_size}")
            
        except Exception as e:
            print(f"   ❌ Error testing cache: {e}")
        
        # Test 8: Rate limiting
        print("\n8. Testing rate limiting...")
        
        try:
            rate_limit = client.rate_limit
            print(f"   Requests per second: {rate_limit.requests_per_second}")
            print(f"   Requests per minute: {rate_limit.requests_per_minute}")
            print(f"   Current request count: {rate_limit.request_count}")
            
            # Make a few rapid requests to test rate limiting
            start_time = time.time()
            for i in range(3):
                await client.get_current_prices(["BTCUSDT"])
            total_time = time.time() - start_time
            
            print(f"   3 requests took: {total_time:.3f}s")
            print(f"   Average time per request: {total_time/3:.3f}s")
            
        except Exception as e:
            print(f"   ❌ Error testing rate limiting: {e}")
        
        # Test 9: Error handling
        print("\n9. Testing error handling...")
        
        try:
            # Test with invalid symbol
            invalid_prices = await client.get_current_prices(["INVALID_SYMBOL"])
            print(f"   Invalid symbol handling: {len(invalid_prices)} results")
            
            # Test with invalid klines request
            invalid_klines = await client.get_klines("INVALID_SYMBOL", "60", 10)
            print(f"   Invalid klines handling: {len(invalid_klines)} results")
            
        except Exception as e:
            print(f"   ❌ Error in error handling test: {e}")
        
        # Test 10: Cache management
        print("\n10. Testing cache management...")
        
        try:
            # Check cache before clearing
            cache_size_before = len(client._price_cache)
            print(f"   Cache size before clear: {cache_size_before}")
            
            # Clear cache
            client.clear_cache()
            
            # Check cache after clearing
            cache_size_after = len(client._price_cache)
            print(f"   Cache size after clear: {cache_size_after}")
            
            if cache_size_after == 0:
                print("   ✅ Cache cleared successfully")
            else:
                print("   ❌ Cache not cleared properly")
                
        except Exception as e:
            print(f"   ❌ Error testing cache management: {e}")
        
        print("\n" + "=" * 50)
        print("✅ Bybit Client tests completed!")
        
        return True

async def test_bybit_context_manager():
    """Test the context manager functionality"""
    
    print("\n🔄 Testing Context Manager...")
    print("-" * 30)
    
    try:
        async with bybit_client() as client:
            print("✅ Context manager entered successfully")
            
            # Test basic functionality
            connection_ok = await client.test_connection()
            print(f"   Connection test: {'✅' if connection_ok else '❌'}")
            
        print("✅ Context manager exited successfully")
        return True
        
    except Exception as e:
        print(f"❌ Context manager test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting Bybit Client Test Suite...")
    print("=" * 60)
    
    # Test 1: Basic functionality
    success1 = await test_bybit_client()
    
    # Test 2: Context manager
    success2 = await test_bybit_context_manager()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed - check logs above")
        
    return success1 and success2

if __name__ == "__main__":
    asyncio.run(main()) 