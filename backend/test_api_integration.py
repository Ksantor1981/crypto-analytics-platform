#!/usr/bin/env python3
"""
Comprehensive API Integration Test Script
Tests all API endpoints to ensure proper integration
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://127.0.0.1:8000"
TEST_USER = {
    "email": "test@example.com",
    "password": "testpass123",
    "full_name": "Test User"
}

class APITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.access_token = None
        self.user_id = None
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def test_health_check(self):
        """Test health check endpoint"""
        self.log("Testing health check endpoint...")
        try:
            response = self.session.get(f"{self.base_url}/health")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"
            self.log("✅ Health check passed")
            return True
        except Exception as e:
            self.log(f"❌ Health check failed: {e}", "ERROR")
            return False
    
    def test_user_registration(self):
        """Test user registration"""
        self.log("Testing user registration...")
        try:
            # Add confirm_password field for registration
            registration_data = {
                **TEST_USER,
                "confirm_password": TEST_USER["password"]
            }
            response = self.session.post(
                f"{self.base_url}/api/v1/users/register",
                json=registration_data
            )
            
            if response.status_code == 400 and "already exists" in response.text:
                self.log("✅ User already exists (expected)")
                return True
            elif response.status_code == 201:
                self.log("✅ User registration successful")
                return True
            else:
                self.log(f"❌ Registration failed: {response.status_code} - {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Registration test failed: {e}", "ERROR")
            return False
    
    def test_user_login(self):
        """Test user login and get access token"""
        self.log("Testing user login...")
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/users/login",
                json={
                    "email": TEST_USER["email"],
                    "password": TEST_USER["password"]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})
                self.log("✅ User login successful")
                return True
            else:
                self.log(f"❌ Login failed: {response.status_code} - {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Login test failed: {e}", "ERROR")
            return False
    
    def test_user_profile(self):
        """Test getting user profile"""
        self.log("Testing user profile retrieval...")
        try:
            response = self.session.get(f"{self.base_url}/api/v1/users/me")
            
            if response.status_code == 200:
                data = response.json()
                self.user_id = data["id"]
                self.log(f"✅ User profile retrieved: {data['email']}")
                return True
            else:
                self.log(f"❌ Profile retrieval failed: {response.status_code} - {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Profile test failed: {e}", "ERROR")
            return False
    
    def test_channels_api(self):
        """Test channels API endpoints"""
        self.log("Testing channels API...")
        try:
            response = self.session.get(f"{self.base_url}/api/v1/channels/")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Channels API working: {len(data)} channels found")
                return True
            else:
                self.log(f"❌ Channels API failed: {response.status_code} - {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Channels API test failed: {e}", "ERROR")
            return False
    
    def test_signals_api(self):
        """Test signals API endpoints"""
        self.log("Testing signals API...")
        try:
            response = self.session.get(f"{self.base_url}/api/v1/signals/")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Signals API working: {len(data)} signals found")
                return True
            else:
                self.log(f"❌ Signals API failed: {response.status_code} - {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Signals API test failed: {e}", "ERROR")
            return False
    
    def test_signals_stats(self):
        """Test signals statistics endpoint"""
        self.log("Testing signals statistics...")
        try:
            response = self.session.get(f"{self.base_url}/api/v1/signals/stats/overview")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Signals stats working: {data['total_signals']} total signals")
                return True
            else:
                self.log(f"❌ Signals stats failed: {response.status_code} - {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Signals stats test failed: {e}", "ERROR")
            return False
    
    def test_subscriptions_api(self):
        """Test subscriptions API endpoints"""
        self.log("Testing subscriptions API...")
        try:
            # Test subscription plans
            response = self.session.get(f"{self.base_url}/api/v1/subscriptions/plans")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Subscription plans working: {len(data)} plans available")
                
                # Test current subscription
                response = self.session.get(f"{self.base_url}/api/v1/subscriptions/me")
                if response.status_code == 200:
                    data = response.json()
                    # Handle case where user has no subscription (data might be None)
                    if data and 'plan_name' in data:
                        self.log(f"✅ Current subscription: {data['plan_name']}")
                    else:
                        self.log("✅ No current subscription (expected for new user)")
                    return True
                else:
                    self.log(f"❌ Current subscription failed: {response.status_code}", "ERROR")
                    return False
            else:
                self.log(f"❌ Subscription plans failed: {response.status_code} - {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Subscriptions API test failed: {e}", "ERROR")
            return False
    
    def test_payments_api(self):
        """Test payments API endpoints"""
        self.log("Testing payments API...")
        try:
            response = self.session.get(f"{self.base_url}/api/v1/payments/me")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Payments API working: {len(data)} payments found")
                return True
            else:
                self.log(f"❌ Payments API failed: {response.status_code} - {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Payments API test failed: {e}", "ERROR")
            return False
    
    def test_api_docs(self):
        """Test API documentation endpoints"""
        self.log("Testing API documentation...")
        try:
            response = self.session.get(f"{self.base_url}/docs")
            
            if response.status_code == 200:
                self.log("✅ API documentation accessible")
                return True
            else:
                self.log(f"❌ API docs failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ API docs test failed: {e}", "ERROR")
            return False
    
    def run_all_tests(self):
        """Run all integration tests"""
        self.log("🚀 Starting comprehensive API integration tests...")
        
        tests = [
            self.test_health_check,
            self.test_user_registration,
            self.test_user_login,
            self.test_user_profile,
            self.test_channels_api,
            self.test_signals_api,
            self.test_signals_stats,
            self.test_subscriptions_api,
            self.test_payments_api,
            self.test_api_docs
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    failed += 1
                time.sleep(0.5)  # Small delay between tests
            except Exception as e:
                self.log(f"❌ Test {test.__name__} crashed: {e}", "ERROR")
                failed += 1
        
        self.log(f"\n📊 Test Results:")
        self.log(f"✅ Passed: {passed}")
        self.log(f"❌ Failed: {failed}")
        self.log(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
        
        if failed == 0:
            self.log("🎉 All tests passed! API integration is working correctly.")
        else:
            self.log(f"⚠️  {failed} tests failed. Please check the logs above.")
        
        return failed == 0

if __name__ == "__main__":
    tester = APITester(BASE_URL)
    success = tester.run_all_tests()
    exit(0 if success else 1) 