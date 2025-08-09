#!/usr/bin/env python3
"""Debug configuration loading."""

import logging
import sys
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from src.config import Config
    print("Creating Config instance...")
    config = Config()
    print(f"Config servers: {len(config.servers)}")
    print(f"Server names: {list(config.servers.keys())}")
    
    # Test credential manager directly
    from src.credential_manager import CredentialManager
    print("\nTesting credential manager...")
    
    # Create manager instance to test validation
    manager = CredentialManager.create_manager()
    validation_result = manager.validate_credential_access()
    print(f"Credential validation: {validation_result}")
    
    # Try to get RCON passwords
    for server_name in ['Imps Lost Island', 'Imps Island']:
        print(f"Getting RCON password for {server_name}...")
        try:
            password = CredentialManager.get_rcon_password(server_name)
            print(f"  Password found: {'Yes' if password else 'No'}")
        except Exception as e:
            print(f"  Error: {e}")
            
except Exception as e:
    logging.error(f"Error during debug: {e}")
    import traceback
    traceback.print_exc()
