#!/usr/bin/env python3
"""
Startup script for Simple CI Redis Service
Runs continuously, updating CI and forecasts every 2 minutes
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import yolo_onnx
sys.path.insert(0, str(Path(__file__).parent))

# Import and run main
from simple_ci_redis import main

if __name__ == "__main__":
    print("Starting Simple CI Redis Service...")
    print("Press Ctrl+C to stop")
    try:
        main()
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        sys.exit(1)
