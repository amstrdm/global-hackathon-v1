#!/usr/bin/env python3
"""
EAAS Frontend Startup Script
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    # Change to frontend directory
    frontend_dir = Path(__file__).parent / "frontend" / "eaas-frontend"
    os.chdir(frontend_dir)
    
    print("🚀 Starting EAAS Frontend...")
    print("📍 Frontend directory:", frontend_dir.absolute())
    print("🌐 Frontend will be available at: http://localhost:5173")
    print("=" * 50)
    
    try:
        # Run the Vite dev server
        subprocess.run(["npm", "run", "dev"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Frontend stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting frontend: {e}")
        print("💡 Make sure you've run 'npm install' in the frontend directory")
        sys.exit(1)

if __name__ == "__main__":
    main()
