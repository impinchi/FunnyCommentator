#!/usr/bin/env python3
"""Test script for Web App IP Monitor functionality."""

import sys
import os
import asyncio
import logging
import json

# Add the project root to Python path  
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web.app import ConfigWebApp

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_web_app_ip_monitor():
    """Test the Web App IP Monitor functionality."""
    try:
        print("Creating ConfigWebApp instance...")
        webapp = ConfigWebApp()
        
        print("\nLoading configuration...")
        config = webapp._load_config_safe()
        print(f"Config loaded: {config is not None}")
        
        if config:
            print(f"Config type: {type(config)}")
            print(f"Has discord_token: {hasattr(config, 'discord_token')}")
            print(f"Has db_path: {hasattr(config, 'db_path')}")
            print(f"Has ip_retry_seconds: {hasattr(config, 'ip_retry_seconds')}")
            
        print("\nTesting _get_ip_monitor_status...")
        status = webapp._get_ip_monitor_status()
        print(f"Status result: {json.dumps(status, indent=2, default=str)}")
        
        print("\n✅ Web app test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Web app test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Starting Web App IP Monitor tests...")
    test_web_app_ip_monitor()
