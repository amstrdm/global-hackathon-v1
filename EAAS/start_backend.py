#!/usr/bin/env python3
"""
EAAS Backend Startup Script
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    # Change to backend directory
    backend_dir = Path(__file__).parent / "backend"
    os.chdir(backend_dir)
    
    print("🚀 Starting EAAS Backend...")
    print("📍 Backend directory:", backend_dir.absolute())
    print("🌐 Server will be available at: http://localhost:8000")
    print("📚 API docs available at: http://localhost:8000/docs")
    print("=" * 50)
    
    try:
        # Run the FastAPI server
        subprocess.run([sys.executable, "main.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Backend stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting backend: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
