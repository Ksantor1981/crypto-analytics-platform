#!/usr/bin/env python3
"""
Test script to check configuration loading
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

print("Testing configuration loading...")

# Test 1: Check if .env file exists
env_path = Path(__file__).parent.parent / ".env"
print(f"Looking for .env file at: {env_path}")
print(f".env file exists: {env_path.exists()}")

if env_path.exists():
    print(f".env file size: {env_path.stat().st_size} bytes")
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"First 100 chars: {repr(content[:100])}")
    except Exception as e:
        print(f"Error reading .env file: {e}")

# Test 2: Try to load dotenv
try:
    from dotenv import load_dotenv
    result = load_dotenv(dotenv_path=env_path)
    print(f"load_dotenv result: {result}")
except Exception as e:
    print(f"Error loading dotenv: {e}")

# Test 3: Check environment variables
print(f"DATABASE_URL: {os.getenv('DATABASE_URL', 'NOT_FOUND')}")
print(f"SECRET_KEY: {os.getenv('SECRET_KEY', 'NOT_FOUND')}")

# Test 4: Try to import config
try:
    from app.core.config import settings
    print(f"✅ Config imported successfully")
    print(f"DATABASE_URL from settings: {settings.DATABASE_URL}")
    print(f"Environment: {settings.ENVIRONMENT}")
except Exception as e:
    print(f"❌ Error importing config: {e}")
    import traceback
    traceback.print_exc() 