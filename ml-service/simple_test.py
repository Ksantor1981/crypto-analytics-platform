#!/usr/bin/env python3
"""
Simple test script for ML service
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_model():
    """Test the ML model"""
    print("🧪 Testing ML Service Model...")
    
    try:
        from models.signal_predictor import EnhancedSignalPredictor as SignalPredictor
        
        # Create model instance
        model = SignalPredictor()
        print(f"✅ Model created successfully")
        print(f"   Version: {model.model_version}")
        print(f"   Features: {len(model.feature_names)}")
        
        # Test prediction
        test_data = {
            "asset": "BTC",
            "direction": "LONG",
            "entry_price": 45000.0,
            "target_price": 47000.0,
            "stop_loss": 43000.0,
            "channel_id": 1,
            "channel_accuracy": 0.75,
            "confidence": 0.8
        }
        
        features = model.preprocess_features(test_data)
        prediction = model.predict_proba(features)
        
        print(f"✅ Test prediction successful")
        print(f"   Success probability: {prediction:.3f}")
        
        # Test feature importance
        importance = model.get_feature_importance()
        print(f"✅ Feature importance: {len(importance)} features")
        
        return True
        
    except Exception as e:
        print(f"❌ Model test failed: {str(e)}")
        return False

def test_api_imports():
    """Test API imports"""
    print("\n🔌 Testing API Imports...")
    
    try:
        from api.predictions import router as predictions_router
        from api.health import router as health_router
        
        print("✅ API routers imported successfully")
        print(f"   Predictions router: {predictions_router}")
        print(f"   Health router: {health_router}")
        
        return True
        
    except Exception as e:
        print(f"❌ API import test failed: {str(e)}")
        return False

def test_config():
    """Test configuration"""
    print("\n⚙️ Testing Configuration...")
    
    try:
        from config import settings, validate_settings
        
        print("✅ Configuration loaded successfully")
        print(f"   Service name: {settings.service_name}")
        print(f"   Port: {settings.port}")
        print(f"   Supported assets: {len(settings.supported_assets)}")
        
        # Test validation
        validate_settings()
        print("✅ Configuration validation passed")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 ML Service Component Tests")
    print("=" * 50)
    
    tests = [
        ("Model Test", test_model),
        ("API Imports Test", test_api_imports),
        ("Configuration Test", test_config)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} crashed: {str(e)}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed!")
        return 0
    else:
        print("💥 Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 