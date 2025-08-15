#!/usr/bin/env python3
"""Test script for IP Monitor functionality."""

import sys
import os
import asyncio
import logging

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import Config
from src.database import DatabaseManager
from src.ip_monitor_manager import IPMonitorManager

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_ip_monitor():
    """Test the IP Monitor functionality."""
    try:
        # Load configuration
        print("Loading configuration...")
        config = Config()
        print(f"Config loaded. Discord token exists: {bool(config.discord_token)}")
        print(f"Database path: {config.db_path}")
        print(f"IP retry seconds: {config.ip_retry_seconds}")
        print(f"Previous IP: {config.previous_ip}")
        
        # Initialize database
        print("\nInitializing database...")
        db_manager = DatabaseManager(config.db_path, {})
        
        # Initialize IP Monitor
        print("\nInitializing IP Monitor...")
        ip_monitor = IPMonitorManager(config, db_manager, None)
        
        # Test configuration access
        print("\nTesting configuration access...")
        config_dict = ip_monitor.get_config()
        print(f"Config dict keys: {list(config_dict.keys())}")
        print(f"IP monitor config: {config_dict.get('ip_monitor', {})}")
        
        # Test IP checking
        print("\nTesting current IP check...")
        current_ip = await ip_monitor.check_current_ip()
        print(f"Current IP: {current_ip}")
        
        # Test last known IP
        print("\nTesting last known IP...")
        last_ip = ip_monitor.get_last_known_ip()
        print(f"Last known IP: {last_ip}")
        
        # Test IP history
        print("\nTesting IP history...")
        history = ip_monitor.get_ip_history(5)
        print(f"IP history (last 5): {history}")
        
        # Test monitor config
        print("\nTesting monitor config...")
        monitor_config = ip_monitor.get_monitor_config()
        print(f"Monitor config: {monitor_config}")
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Starting IP Monitor tests...")
    asyncio.run(test_ip_monitor())
