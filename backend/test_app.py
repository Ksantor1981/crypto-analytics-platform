#!/usr/bin/env python3
"""
Test script to check if the app imports correctly
"""

try:
    from app.main import app
    print("✅ App imported successfully")
    
    # Test basic functionality
    print(f"✅ App title: {app.title}")
    print(f"✅ App version: {app.version}")
    
    # Try to get routes
    routes = [route.path for route in app.routes]
    print(f"✅ Available routes: {routes}")
    
except Exception as e:
    print(f"❌ Error importing app: {e}")
    import traceback
    traceback.print_exc() 