"""
ML Integration Test Suite
Tests the complete ML service integration
"""

import asyncio
import httpx
import json
from datetime import datetime

# Service URLs
BACKEND_URL = "http://localhost:8000"
ML_SERVICE_URL = "http://localhost:8001"

async def test_ml_service_health():
    """Test ML service health"""
    print("🏥 Testing ML Service Health...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{ML_SERVICE_URL}/api/v1/health/")
            
            if response.status_code == 200:
                health_data = response.json()
                print(f"  ✅ ML Service is healthy: {health_data['status']}")
                return True
            else:
                print(f"  ❌ ML Service health check failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"  ❌ ML Service health check error: {str(e)}")
        return False

async def test_ml_service_prediction():
    """Test ML service prediction endpoint"""
    print("\n🔮 Testing ML Service Prediction...")
    
    try:
        signal_data = {
            "asset": "BTC",
            "direction": "LONG",
            "entry_price": 45000.0,
            "target_price": 47000.0,
            "stop_loss": 43000.0,
            "channel_id": 1,
            "channel_accuracy": 0.75,
            "confidence": 0.8
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ML_SERVICE_URL}/api/v1/predictions/signal",
                json=signal_data
            )
            
            if response.status_code == 200:
                prediction = response.json()
                print(f"  ✅ Prediction successful:")
                print(f"    Success probability: {prediction['success_probability']:.3f}")
                print(f"    Recommendation: {prediction['recommendation']}")
                print(f"    Risk score: {prediction['risk_score']:.3f}")
                print(f"    Model version: {prediction['model_version']}")
                return True
            else:
                print(f"  ❌ Prediction failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"  ❌ Prediction error: {str(e)}")
        return False

async def test_backend_health():
    """Test backend health"""
    print("\n🏥 Testing Backend Health...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BACKEND_URL}/health")
            
            if response.status_code == 200:
                health_data = response.json()
                print(f"  ✅ Backend is healthy: {health_data['status']}")
                return True
            else:
                print(f"  ❌ Backend health check failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"  ❌ Backend health check error: {str(e)}")
        return False

async def test_backend_ml_integration():
    """Test backend ML integration endpoints"""
    print("\n🔗 Testing Backend ML Integration...")
    
    try:
        # Test ML service health through backend
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BACKEND_URL}/api/v1/ml/health")
            
            if response.status_code == 200:
                ml_health = response.json()
                print(f"  ✅ ML service health via backend: {ml_health['ml_service_status']}")
                
                # Test model info through backend
                response = await client.get(f"{BACKEND_URL}/api/v1/ml/model/info")
                
                if response.status_code == 200:
                    model_info = response.json()
                    print(f"  ✅ Model info via backend: {model_info['model_version']}")
                    return True
                else:
                    print(f"  ❌ Model info failed: {response.status_code}")
                    return False
            else:
                print(f"  ❌ ML health via backend failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"  ❌ Backend ML integration error: {str(e)}")
        return False

async def test_service_discovery():
    """Test service discovery and communication"""
    print("\n📡 Testing Service Discovery...")
    
    try:
        # Test ML service info
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{ML_SERVICE_URL}/api/v1/info")
            
            if response.status_code == 200:
                ml_info = response.json()
                print(f"  ✅ ML Service info: {ml_info['service_name']} v{ml_info['version']}")
                print(f"    Features: {len(ml_info['features'])}")
                print(f"    Supported assets: {len(ml_info['supported_assets'])}")
                
                # Test backend API docs
                response = await client.get(f"{BACKEND_URL}/docs")
                
                if response.status_code == 200:
                    print(f"  ✅ Backend API docs accessible")
                    return True
                else:
                    print(f"  ❌ Backend API docs failed: {response.status_code}")
                    return False
            else:
                print(f"  ❌ ML service info failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"  ❌ Service discovery error: {str(e)}")
        return False

async def run_all_tests():
    """Run all integration tests"""
    print("🧪 ML Integration Test Suite")
    print("=" * 60)
    
    tests = [
        ("ML Service Health", test_ml_service_health),
        ("ML Service Prediction", test_ml_service_prediction),
        ("Backend Health", test_backend_health),
        ("Backend ML Integration", test_backend_ml_integration),
        ("Service Discovery", test_service_discovery)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if await test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} crashed: {str(e)}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Integration Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All integration tests passed!")
        print("✅ ML Service is fully integrated with Backend!")
        return True
    else:
        print("💥 Some integration tests failed!")
        return False

if __name__ == "__main__":
    print("🚀 Starting ML Integration Tests...")
    print("📋 Prerequisites:")
    print("  - Backend running on http://localhost:8000")
    print("  - ML Service running on http://localhost:8001")
    print()
    
    success = asyncio.run(run_all_tests())
    
    if success:
        print("\n🎯 ML Service Integration Complete!")
        print("✅ Ready for production deployment")
    else:
        print("\n❌ Integration tests failed")
        print("🔧 Please check service configurations") 