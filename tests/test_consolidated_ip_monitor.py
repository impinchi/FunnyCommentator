#!/usr/bin/env python3
"""Test the consolidated IP monitoring in main.py."""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main import Application

async def test_ip_monitoring():
    """Test IP monitoring integration in main app."""
    try:
        print("Creating Application instance...")
        app = Application()
        
        print("Testing IP monitor configuration...")
        monitor_config = app.ip_monitor.get_monitor_config()
        print(f"✅ Monitor config loaded: {monitor_config}")
        
        print("Testing IP check functionality...")
        result = await app.ip_monitor.perform_ip_check_and_notify()
        print(f"✅ IP check result: {result}")
        
        print("✅ Consolidated IP monitoring is working correctly!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Testing consolidated IP monitoring...")
    asyncio.run(test_ip_monitoring())
