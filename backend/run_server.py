#!/usr/bin/env python3
"""
Simple server runner that sets environment variables manually
"""
import os
import uvicorn

# Set environment variables manually
os.environ["DATABASE_URL"] = "postgresql://crypto_user:crypto_password@localhost:5432/crypto_analytics"
os.environ["SECRET_KEY"] = "supersecretkey"
os.environ["ENVIRONMENT"] = "development"
os.environ["DEBUG"] = "True"

if __name__ == "__main__":
    # Import after setting environment variables
    from app.main import app
    
    print("✅ Starting FastAPI server...")
    print(f"✅ Database URL: {os.environ.get('DATABASE_URL')}")
    
    # Run the server
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    ) 