"""Test script to verify credential counting functionality."""
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.credential_manager import CredentialManager

def test_credential_count():
    """Test the credential counting functionality."""
    print("Testing credential count functionality...")
    print("-" * 50)
    
    try:
        manager = CredentialManager.create_manager()
        
        # Test the new count method
        count = manager.count_stored_credentials()
        print(f"✅ Stored credentials count: {count}")
        
        # Test validation
        validation = manager.validate_credential_access()
        print(f"✅ Keyring available: {validation.get('keyring_available', False)}")
        print(f"✅ Keyring read/write: {validation.get('keyring_read_write', False)}")
        print(f"✅ Fallback available: {validation.get('fallback_available', False)}")
        print(f"✅ Fallback read/write: {validation.get('fallback_read_write', False)}")
        
        # Test system info
        system_info = manager.get_system_info()
        print(f"✅ Platform: {system_info.get('platform', 'Unknown')}")
        print(f"✅ Keyring backend: {system_info.get('keyring_backend', 'Unknown')}")
        
        print("\n" + "=" * 50)
        print("✅ Credential counting test completed successfully!")
        
        if count > 0:
            print(f"🎉 Found {count} stored credential(s) - dashboard should display this correctly!")
        else:
            print("ℹ️  No credentials stored yet - this is normal for a fresh setup.")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_credential_count()
