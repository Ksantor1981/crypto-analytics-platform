#!/usr/bin/env python3
"""
Simple test script for Telegram endpoints
"""
import requests
import json

def test_telegram_endpoints():
    base_url = "http://localhost:8000"
    
    # Test health endpoint
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Health: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Health error: {e}")
    
    # Test telegram test endpoint
    print("\nTesting telegram test endpoint...")
    try:
        response = requests.get(f"{base_url}/api/v1/telegram/test")
        print(f"Test: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Test error: {e}")
    
    # Test telegram channels simple endpoint
    print("\nTesting telegram channels-simple endpoint...")
    try:
        response = requests.get(f"{base_url}/api/v1/telegram/channels-simple")
        print(f"Channels Simple: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Channels Simple error: {e}")
    
    # Test telegram channels endpoint
    print("\nTesting telegram channels endpoint...")
    try:
        response = requests.get(f"{base_url}/api/v1/telegram/channels")
        print(f"Channels: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Channels error: {e}")

if __name__ == "__main__":
    test_telegram_endpoints() 