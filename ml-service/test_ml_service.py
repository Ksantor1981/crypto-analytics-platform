"""
ML Service Test Suite
"""

import asyncio
import httpx
import json
from datetime import datetime

# Test configuration
ML_SERVICE_URL = "http://localhost:8001"

async def test_health_endpoints():
    """Test health check endpoints"""
    print("🏥 Testing Health Endpoints...")
    
    async with httpx.AsyncClient() as client:
        # Basic health check
        response = await client.get(f"{ML_SERVICE_URL}/api/v1/health/")
        print(f"  ✓ Basic health: {response.status_code} - {response.json()}")
        
        # Detailed health check
        response = await client.get(f"{ML_SERVICE_URL}/api/v1/health/detailed")
        print(f"  ✓ Detailed health: {response.status_code}")
        
        # Readiness check
        response = await client.get(f"{ML_SERVICE_URL}/api/v1/health/readiness")
        print(f"  ✓ Readiness: {response.status_code}")
        
        # Liveness check
        response = await client.get(f"{ML_SERVICE_URL}/api/v1/health/liveness")
        print(f"  ✓ Liveness: {response.status_code}")

async def test_prediction_endpoints():
    """Test prediction endpoints"""
    print("\n🔮 Testing Prediction Endpoints...")
    
    async with httpx.AsyncClient() as client:
        # Test single prediction
        signal_data = {
            "asset": "BTC",
            "direction": "LONG",
            "entry_price": 45000.0,
            "target_price": 47000.0,
            "stop_loss": 43000.0,
            "channel_id": 1,
            "channel_accuracy": 0.75,
            "market_volatility": 0.6,
            "confidence": 0.8
        }
        
        response = await client.post(
            f"{ML_SERVICE_URL}/api/v1/predictions/signal",
            json=signal_data
        )
        
        if response.status_code == 200:
            prediction = response.json()
            print(f"  ✓ Single prediction: Success probability = {prediction['success_probability']:.3f}")
            print(f"    Recommendation: {prediction['recommendation']}")
            print(f"    Risk score: {prediction['risk_score']:.3f}")
        else:
            print(f"  ✗ Single prediction failed: {response.status_code}")
        
        # Test batch prediction
        batch_data = {
            "signals": [
                {
                    "asset": "BTC",
                    "direction": "LONG",
                    "entry_price": 45000.0,
                    "target_price": 47000.0,
                    "stop_loss": 43000.0,
                    "channel_id": 1,
                    "channel_accuracy": 0.75,
                    "confidence": 0.8
                },
                {
                    "asset": "ETH",
                    "direction": "SHORT",
                    "entry_price": 3000.0,
                    "target_price": 2800.0,
                    "stop_loss": 3200.0,
                    "channel_id": 2,
                    "channel_accuracy": 0.65,
                    "confidence": 0.6
                }
            ]
        }
        
        response = await client.post(
            f"{ML_SERVICE_URL}/api/v1/predictions/batch",
            json=batch_data
        )
        
        if response.status_code == 200:
            batch_result = response.json()
            print(f"  ✓ Batch prediction: {batch_result['total_processed']} signals processed")
            print(f"    Processing time: {batch_result['processing_time_ms']:.2f}ms")
        else:
            print(f"  ✗ Batch prediction failed: {response.status_code}")

async def test_model_info():
    """Test model information endpoint"""
    print("\n📊 Testing Model Info...")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{ML_SERVICE_URL}/api/v1/predictions/model/info")
        
        if response.status_code == 200:
            model_info = response.json()
            print(f"  ✓ Model version: {model_info['model_version']}")
            print(f"  ✓ Model type: {model_info['model_type']}")
            print(f"  ✓ Features: {len(model_info['feature_names'])}")
            print(f"  ✓ Is trained: {model_info['is_trained']}")
        else:
            print(f"  ✗ Model info failed: {response.status_code}")

async def test_service_info():
    """Test service information endpoints"""
    print("\n📋 Testing Service Info...")
    
    async with httpx.AsyncClient() as client:
        # Root endpoint
        response = await client.get(f"{ML_SERVICE_URL}/")
        if response.status_code == 200:
            print(f"  ✓ Root endpoint: {response.json()['service']}")
        
        # Service info
        response = await client.get(f"{ML_SERVICE_URL}/api/v1/info")
        if response.status_code == 200:
            info = response.json()
            print(f"  ✓ Service info: {info['service_name']} v{info['version']}")
            print(f"  ✓ Supported assets: {len(info['supported_assets'])}")
            print(f"  ✓ Features: {len(info['features'])}")

async def test_error_handling():
    """Test error handling"""
    print("\n🚨 Testing Error Handling...")
    
    async with httpx.AsyncClient() as client:
        # Test invalid signal data
        invalid_data = {
            "asset": "INVALID",
            "direction": "INVALID",
            "entry_price": -1000.0,  # Invalid price
            "channel_id": -1  # Invalid channel
        }
        
        response = await client.post(
            f"{ML_SERVICE_URL}/api/v1/predictions/signal",
            json=invalid_data
        )
        
        print(f"  ✓ Invalid data handling: {response.status_code}")
        
        # Test non-existent endpoint
        response = await client.get(f"{ML_SERVICE_URL}/api/v1/nonexistent")
        print(f"  ✓ Non-existent endpoint: {response.status_code}")

async def run_all_tests():
    """Run all tests"""
    print("🧪 ML Service Integration Tests")
    print("=" * 50)
    
    try:
        await test_health_endpoints()
        await test_prediction_endpoints()
        await test_model_info()
        await test_service_info()
        await test_error_handling()
        
        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        raise

if __name__ == "__main__":
    print("Starting ML Service tests...")
    print("Make sure ML Service is running on http://localhost:8001")
    print()
    
    asyncio.run(run_all_tests()) 