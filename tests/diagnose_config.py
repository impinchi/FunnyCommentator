import sys
import traceback
from src.config import Config
from src.credential_manager import CredentialManager

print("=== Configuration Diagnostic ===")

try:
    print("1. Testing credential manager...")
    discord_token = CredentialManager.get_discord_token()
    print(f"   Discord token: {'Found' if discord_token else 'Not found'}")
    
    rcon1 = CredentialManager.get_rcon_password('Imps Lost Island')
    print(f"   Lost Island RCON: {'Found' if rcon1 else 'Not found'}")
    
    rcon2 = CredentialManager.get_rcon_password('Imps Island') 
    print(f"   Island RCON: {'Found' if rcon2 else 'Not found'}")
    
except Exception as e:
    print(f"   Error with credential manager: {e}")
    traceback.print_exc()

try:
    print("\n2. Testing configuration loading...")
    Config.clear_instance()
    config = Config()
    print(f"   Config loaded successfully")
    print(f"   Servers found: {len(config.servers)}")
    for name in config.servers:
        print(f"     - {name}")
        
except Exception as e:
    print(f"   Error loading configuration: {e}")
    traceback.print_exc()

print("\n=== End Diagnostic ===")
