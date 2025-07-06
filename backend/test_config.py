#!/usr/bin/env python3
"""
Test configuration loading
"""
import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set the environment variable for testing
os.environ['ENVIRONMENT'] = 'development'

def test_config():
    """Test if configuration loads correctly."""
    try:
        from app.core.config import get_settings
        settings = get_settings()
        
        print("✅ Configuration loaded successfully!")
        print(f"Environment: {settings.ENVIRONMENT}")
        print(f"Database URL: {settings.DATABASE_URL}")
        print(f"Redis URL: {settings.REDIS_URL}")
        print(f"Backend CORS Origins: {settings.BACKEND_CORS_ORIGINS}")
        print(f"Secret Key: {'*' * 20}")
        
        # Test database connection
        from app.core.database import get_db
        db = next(get_db())
        print("✅ Database connection successful!")
        db.close()
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_config()
    sys.exit(0 if success else 1) 