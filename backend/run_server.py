#!/usr/bin/env python3
"""
Server startup script with proper environment validation
"""
import os
import sys
import uvicorn

def main():
    """Start the server with environment validation."""
    # Check if we're in the correct directory
    if not os.path.exists("app"):
        print("❌ Error: Must run from backend directory")
        print("Current directory:", os.getcwd())
        print("Expected: .../crypto-analytics-platform/backend")
        sys.exit(1)
    
    # Validate required environment variables
    required_vars = ["SECRET_KEY", "DATABASE_URL"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Error: Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nPlease set these environment variables before starting the server.")
        print("You can copy env.example to .env and fill in the values.")
        sys.exit(1)
    
    print("🚀 Starting Backend API server...")
    print(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"Debug mode: {os.getenv('DEBUG', 'true')}")
    
    # Start the server
    try:
        uvicorn.run(
            "app.main:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 