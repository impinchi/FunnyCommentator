#!/usr/bin/env python3
"""Test web configuration loading."""

import sys
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Change to the correct working directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))
print(f"Working directory: {os.getcwd()}")

try:
    # Import the web app
    from web.app import ConfigWebApp
    
    print("Creating web app...")
    app = ConfigWebApp()
    
    print("Testing config loading...")
    config = app._load_config_safe()
    
    if config:
        print(f"Config loaded successfully! Servers: {len(config.servers)}")
        print(f"Server names: {list(config.servers.keys())}")
    else:
        print("Config loading failed!")
        
except Exception as e:
    logging.error(f"Error during test: {e}")
    import traceback
    traceback.print_exc()
