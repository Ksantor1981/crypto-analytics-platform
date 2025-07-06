#!/usr/bin/env python3
"""
Celery Worker Starter Script
Starts Celery worker for background tasks
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_redis_connection():
    """Check if Redis is available"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        return True
    except:
        return False

def start_celery_worker():
    """Start Celery worker"""
    print("🚀 Starting Celery Worker...")
    
    # Change to workers directory
    workers_dir = Path("workers")
    if not workers_dir.exists():
        print("❌ Workers directory not found!")
        return False
    
    os.chdir(workers_dir)
    
    # Check Redis connection
    if not check_redis_connection():
        print("⚠️  Redis not available. Install and start Redis server first.")
        print("   For Windows: Download Redis from https://redis.io/download")
        print("   Or use Docker: docker run -d -p 6379:6379 redis:alpine")
        return False
    
    try:
        # Start Celery worker
        cmd = [
            sys.executable, "-m", "celery", 
            "worker", 
            "-A", "tasks.app",
            "--loglevel=info",
            "--concurrency=2"
        ]
        
        print(f"Executing: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start Celery worker: {e}")
        return False
    except KeyboardInterrupt:
        print("\n🛑 Celery worker stopped by user")
        return True
    
    return True

def start_celery_beat():
    """Start Celery beat scheduler"""
    print("🚀 Starting Celery Beat Scheduler...")
    
    workers_dir = Path("workers")
    if not workers_dir.exists():
        print("❌ Workers directory not found!")
        return False
    
    os.chdir(workers_dir)
    
    try:
        cmd = [
            sys.executable, "-m", "celery", 
            "beat", 
            "-A", "tasks.app",
            "--loglevel=info"
        ]
        
        print(f"Executing: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start Celery beat: {e}")
        return False
    except KeyboardInterrupt:
        print("\n🛑 Celery beat stopped by user")
        return True
    
    return True

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python start_celery_worker.py [worker|beat|both]")
        print("  worker - Start Celery worker")
        print("  beat   - Start Celery beat scheduler") 
        print("  both   - Start both worker and beat (not recommended for production)")
        return
    
    mode = sys.argv[1].lower()
    
    if mode == "worker":
        start_celery_worker()
    elif mode == "beat":
        start_celery_beat()
    elif mode == "both":
        print("⚠️  Starting both worker and beat in development mode")
        print("   In production, run these as separate processes")
        # For development, we'll just start worker
        start_celery_worker()
    else:
        print(f"❌ Unknown mode: {mode}")
        print("Available modes: worker, beat, both")

if __name__ == "__main__":
    main() 