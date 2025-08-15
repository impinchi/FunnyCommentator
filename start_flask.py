#!/usr/bin/env python3
"""Simple test to start Flask app without debug mode."""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web.app import ConfigWebApp

if __name__ == "__main__":
    try:
        print("Creating Flask app...")
        app = ConfigWebApp()
        print("Starting Flask app on port 5000...")
        app.run(host='127.0.0.1', port=5000, debug=False)
    except Exception as e:
        print(f"Error starting Flask app: {e}")
        import traceback
        traceback.print_exc()
