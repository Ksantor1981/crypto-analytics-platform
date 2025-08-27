#!/usr/bin/env python3
"""
Тест импорта Telethon
"""
import sys
print(f"Python version: {sys.version}")

try:
    import telethon
    print(f"✅ Telethon version: {telethon.__version__}")
    
    from telethon import TelegramClient
    print("✅ TelegramClient imported successfully")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Trying to install telethon...")
    
    try:
        import subprocess
        result = subprocess.run([sys.executable, "-m", "pip", "install", "telethon"], 
                              capture_output=True, text=True)
        print(f"Install result: {result.stdout}")
        if result.stderr:
            print(f"Install errors: {result.stderr}")
    except Exception as install_error:
        print(f"Install failed: {install_error}")
