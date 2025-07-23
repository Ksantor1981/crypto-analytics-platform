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
        self.user_role = None
        
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
            self.log("[PASS] Health check passed")
            return True
        except Exception as e:
            self.log(f"[FAIL] Health check failed: {e}", "ERROR")
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
                self.log("[PASS] User already exists (expected)")
                return True
            elif response.status_code == 201:
                self.log("[PASS] User registration successful")
                return True
            else:
                self.log(f"[FAIL] Registration failed: {response.status_code} - {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"[FAIL] Registration test failed: {e}", "ERROR")
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
                self.log("[PASS] User login successful")
                return True
            else:
                self.log(f"[FAIL] Login failed: {response.status_code} - {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"[FAIL] Login test failed: {e}", "ERROR")
            return False
    
    def test_user_profile(self):
        """Test getting user profile"""
        self.log("Testing user profile retrieval...")
        try:
            response = self.session.get(f"{self.base_url}/api/v1/users/me")
            
            if response.status_code == 200:
                data = response.json()
                self.user_id = data["id"]
                self.user_role = data["role"]
                self.log(f"[PASS] User profile retrieved: {data['email']}, Role: {data['role']}")
                return True
            else:
                self.log(f"[FAIL] Profile retrieval failed: {response.status_code} - {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"[FAIL] Profile test failed: {e}", "ERROR")
            return False
    
    def test_channels_api(self):
        """Test channels API endpoints"""
        self.log("Testing channels API...")
        try:
            response = self.session.get(f"{self.base_url}/api/v1/channels/")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"[PASS] Channels API working: {len(data)} channels found")
                return True
            else:
                self.log(f"[FAIL] Channels API failed: {response.status_code} - {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"[FAIL] Channels API test failed: {e}", "ERROR")
            return False
    
    def test_signals_api(self):
        """Test signals API endpoints"""
        self.log("Testing signals API...")
        try:
            response = self.session.get(f"{self.base_url}/api/v1/signals/")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"[PASS] Signals API working: {len(data)} signals found")
                return True
            else:
                self.log(f"[FAIL] Signals API failed: {response.status_code} - {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"[FAIL] Signals API test failed: {e}", "ERROR")
            return False
    
    def test_signals_stats(self):
        """Test signals statistics endpoint"""
        self.log("Testing signals statistics...")
        try:
            response = self.session.get(f"{self.base_url}/api/v1/signals/stats/overview")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"[PASS] Signals stats working: {data['total_signals']} total signals")
                return True
            else:
                self.log(f"[FAIL] Signals stats failed: {response.status_code} - {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"[FAIL] Signals stats test failed: {e}", "ERROR")
            return False
    
    def test_subscriptions_api(self):
        """Test subscriptions API endpoints"""
        self.log("Testing subscriptions API...")
        try:
            # Test subscription plans
            response = self.session.get(f"{self.base_url}/api/v1/subscriptions/plans")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"[PASS] Subscription plans working: {len(data)} plans available")
                
                # Test current subscription
                response = self.session.get(f"{self.base_url}/api/v1/subscriptions/me")
                if response.status_code == 200:
                    data = response.json()
                    # Handle case where user has no subscription (data might be None)
                    if data and 'plan_name' in data:
                        self.log(f"[PASS] Current subscription: {data['plan_name']}")
                    else:
                        self.log("[PASS] No current subscription (expected for new user)")
                    return True
                else:
                    self.log(f"[FAIL] Current subscription failed: {response.status_code}", "ERROR")
                    return False
            else:
                self.log(f"[FAIL] Subscription plans failed: {response.status_code} - {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"[FAIL] Subscriptions API test failed: {e}", "ERROR")
            return False
    
    def test_channel_creation_limits(self):
        """Test channel creation limits for free users."""
        self.log("Testing channel creation limits...")

        if self.user_role != 'FREE_USER':
            self.log("Skipping test: User is not a FREE_USER.", "WARNING")
            return True

        try:
            # 1. Cleanup existing channels
            self.log("Cleaning up existing channels...")
            response = self.session.get(f"{self.base_url}/api/v1/channels/")
            if response.status_code == 200:
                for channel in response.json():
                    self.session.delete(f"{self.base_url}/api/v1/channels/{channel.get('id')}")
                self.log("Cleanup complete.")
            
            # 2. Create channels up to the limit
            for i in range(1, 4):
                channel_data = {
                    "name": f"Test Channel {i}",
                    "url": f"https://t.me/testchannel{int(time.time())}{i}",
                    "description": "A test channel"
                }
                response = self.session.post(f"{self.base_url}/api/v1/channels/", json=channel_data)
                assert response.status_code == 201, f"Failed to create channel {i}"
                self.log(f"[PASS] Created channel {i}")

            # 3. Attempt to create one more channel (should fail)
            self.log("Attempting to create channel beyond limit...")
            channel_data = {
                "name": "Test Channel 4",
                "url": f"https://t.me/testchannel{int(time.time())}4",
                "description": "A test channel that should fail"
            }
            response = self.session.post(f"{self.base_url}/api/v1/channels/", json=channel_data)
            assert response.status_code == 402, "Limit check failed"
            self.log("[PASS] Correctly blocked channel creation beyond limit (402 Payment Required)")

            # 4. Final cleanup
            self.log("Final cleanup...")
            response = self.session.get(f"{self.base_url}/api/v1/channels/")
            if response.status_code == 200:
                for channel in response.json():
                    self.session.delete(f"{self.base_url}/api/v1/channels/{channel.get('id')}")
                self.log("Final cleanup complete.")

            return True
        except Exception as e:
            self.log(f"[FAIL] Channel creation limit test failed: {e}", "ERROR")
            return False

    def test_payments_api(self):
        """Test payments API endpoints"""
        self.log("Testing payments API...")
        try:
            response = self.session.get(f"{self.base_url}/api/v1/payments/me")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"[PASS] Payments API working: {len(data)} payments found")
                return True
            else:
                self.log(f"[FAIL] Payments API failed: {response.status_code} - {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"[FAIL] Payments API test failed: {e}", "ERROR")
            return False
    
    def test_api_docs(self):
        """Test API documentation endpoints"""
        self.log("Testing API documentation...")
        try:
            response = self.session.get(f"{self.base_url}/docs")
            
            if response.status_code == 200:
                self.log("[PASS] API documentation accessible")
                return True
            else:
                self.log(f"[FAIL] API docs failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"[FAIL] API docs test failed: {e}", "ERROR")
            return False
    
    def run_all_tests(self):
        """Run all integration tests"""
        self.log(">> Starting comprehensive API integration tests...")
        
        tests = [
            self.test_health_check,
            self.test_user_registration,
            self.test_user_login,
            self.test_user_profile,
            self.test_channel_creation_limits,
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
                self.log(f"[FAIL] Test {test.__name__} crashed: {e}", "ERROR")
                failed += 1
        
        self.log(f"\n[STATS] Test Results:")
        self.log(f"[PASS] Passed: {passed}")
        self.log(f"[FAIL] Failed: {failed}")
        self.log(f"[RATE] Success Rate: {(passed/(passed+failed)*100):.1f}%")
        
        if failed == 0:
            self.log("[SUCCESS] All tests passed! API integration is working correctly.")
        else:
            self.log(f"[WARN]  {failed} tests failed. Please check the logs above.")
        
        return failed == 0

if __name__ == "__main__":
    tester = APITester(BASE_URL)
    success = tester.run_all_tests()
    exit(0 if success else 1) 