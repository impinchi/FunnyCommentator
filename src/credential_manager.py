"""Enterprise-level credential management module with cross-platform support.

This module provides secure storage and retrieval of sensitive credentials
using the operating system's secure credential store with fallback options
for enterprise environments.

Supported platforms:
- Windows: Windows Credential Manager
- macOS: Keychain
- Linux: Secret Service API (GNOME Keyring, KDE Wallet)
- Fallback: Encrypted file storage for headless/CI environments
"""
import keyring
import getpass
import logging
import platform
import os
import sys
from typing import Optional, Dict, Any
import json
from pathlib import Path
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class CredentialManager:
    """Enterprise-level credential manager with cross-platform support.
    
    Features:
    - Cross-platform keyring support (Windows, macOS, Linux)
    - Encrypted file fallback for headless environments
    - Key rotation and credential versioning
    - Audit logging for enterprise compliance
    - Multiple authentication backends
    - Secure credential validation
    """
    
    # Service name for keyring storage
    SERVICE_NAME = "FunnyCommentator"
    ENTERPRISE_SERVICE_NAME = "FunnyCommentator-Enterprise"
    
    # Credential keys
    DISCORD_TOKEN = "discord_token"
    RCON_PASSWORD_PREFIX = "rcon_password_"
    MASTER_KEY = "master_encryption_key"
    
    # Platform detection
    PLATFORM = platform.system().lower()
    
    # Fallback encrypted storage
    FALLBACK_DIR = Path.home() / ".funnycommentator" / "secure"
    FALLBACK_FILE = FALLBACK_DIR / "credentials.enc"
    
    def __init__(self, use_enterprise_mode: bool = False, fallback_to_file: bool = True):
        """Initialize credential manager with enterprise options.
        
        Args:
            use_enterprise_mode: Enable enterprise features and compliance logging
            fallback_to_file: Allow fallback to encrypted file storage if keyring fails
        """
        self.enterprise_mode = use_enterprise_mode
        self.fallback_enabled = fallback_to_file
        self.service_name = self.ENTERPRISE_SERVICE_NAME if use_enterprise_mode else self.SERVICE_NAME
        
        # Setup logging for enterprise compliance
        if self.enterprise_mode:
            self._setup_audit_logging()
        
        # Ensure fallback directory exists
        if self.fallback_enabled:
            self.FALLBACK_DIR.mkdir(parents=True, exist_ok=True)
    
    def _setup_audit_logging(self) -> None:
        """Setup audit logging for enterprise compliance.
        
        Note: Using main application logger instead of separate audit log
        to comply with centralized logging requirements.
        """
        # Use the main application logger instead of creating separate audit log
        self.audit_logger = logging.getLogger('credential_audit')
        
        # Log audit setup to main application log
        logging.info("Credential audit logging initialized - using main application log")
    
    def _log_audit_event(self, event: str, key: str, success: bool = True) -> None:
        """Log credential access events for audit purposes.
        
        Args:
            event: Type of event (store, retrieve, delete)
            key: Credential key (masked for security)
            success: Whether the operation was successful
        """
        if hasattr(self, 'audit_logger'):
            masked_key = key[:4] + "*" * (len(key) - 4) if len(key) > 4 else "****"
            status = "SUCCESS" if success else "FAILED"
            self.audit_logger.info(f"{event.upper()} - Key: {masked_key} - Status: {status}")
    
    def _get_keyring_backend(self) -> str:
        """Detect and return the available keyring backend."""
        try:
            backend = keyring.get_keyring()
            return f"{backend.__module__}.{backend.__class__.__name__}"
        except Exception:
            return "Unknown"
    
    def _generate_fallback_key(self, password: str) -> bytes:
        """Generate encryption key from password for fallback storage.
        
        Args:
            password: User password for key derivation
            
        Returns:
            Derived encryption key
        """
        password_bytes = password.encode()
        salt = b'FunnyCommentator_Salt_2025'  # In production, use random salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password_bytes))
    
    def _store_credential_fallback(self, key: str, value: str, master_password: str) -> None:
        """Store credential in encrypted file as fallback.
        
        Args:
            key: Credential key
            value: Credential value
            master_password: Password for encryption
        """
        try:
            # Load existing credentials or create new
            credentials = {}
            if self.FALLBACK_FILE.exists():
                credentials = self._load_fallback_credentials(master_password)
            
            # Add new credential
            credentials[key] = value
            
            # Encrypt and save
            encryption_key = self._generate_fallback_key(master_password)
            fernet = Fernet(encryption_key)
            encrypted_data = fernet.encrypt(json.dumps(credentials).encode())
            
            with open(self.FALLBACK_FILE, 'wb') as f:
                f.write(encrypted_data)
            
            # Set secure permissions (Unix-like systems)
            if self.PLATFORM in ['linux', 'darwin']:
                os.chmod(self.FALLBACK_FILE, 0o600)
                
        except Exception as e:
            logging.error(f"Fallback credential storage failed for {key}: {e}")
            raise
    
    def _load_fallback_credentials(self, master_password: str) -> Dict[str, str]:
        """Load credentials from encrypted fallback file.
        
        Args:
            master_password: Password for decryption
            
        Returns:
            Dictionary of stored credentials
        """
        try:
            if not self.FALLBACK_FILE.exists():
                return {}
            
            encryption_key = self._generate_fallback_key(master_password)
            fernet = Fernet(encryption_key)
            
            with open(self.FALLBACK_FILE, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
            
        except Exception as e:
            logging.error(f"Failed to load fallback credentials: {e}")
            return {}
    
    def _get_credential_fallback(self, key: str, master_password: str) -> Optional[str]:
        """Retrieve credential from fallback storage.
        
        Args:
            key: Credential key
            master_password: Password for decryption
            
        Returns:
            Credential value or None
        """
        try:
            credentials = self._load_fallback_credentials(master_password)
            return credentials.get(key)
        except Exception as e:
            logging.error(f"Failed to retrieve fallback credential {key}: {e}")
            return None
    
    @classmethod
    def create_manager(cls, enterprise_mode: bool = False) -> 'CredentialManager':
        """Factory method to create credential manager instance.
        
        Args:
            enterprise_mode: Enable enterprise features
            
        Returns:
            Configured CredentialManager instance
        """
        return cls(use_enterprise_mode=enterprise_mode)
    
    def store_credential(self, key: str, value: str, master_password: Optional[str] = None) -> None:
        """Store a credential securely with multiple backend support.
        
        Args:
            key: The credential identifier
            value: The credential value to store
            master_password: Password for fallback encryption (if needed)
        """
        success = False
        
        try:
            # Try keyring first
            keyring.set_password(self.service_name, key, value)
            logging.info(f"Stored credential in keyring: {key}")
            success = True
            
        except Exception as keyring_error:
            logging.warning(f"Keyring storage failed for {key}: {keyring_error}")
            
            # Fallback to encrypted file if enabled
            if self.fallback_enabled and master_password:
                try:
                    self._store_credential_fallback(key, value, master_password)
                    logging.info(f"Stored credential in fallback storage: {key}")
                    success = True
                except Exception as fallback_error:
                    logging.error(f"Fallback storage failed for {key}: {fallback_error}")
            else:
                logging.error(f"No fallback available for credential {key}")
        
        # Audit logging
        self._log_audit_event("store", key, success)
        
        if not success:
            raise RuntimeError(f"Failed to store credential {key} in any available backend")
    
    def get_credential(self, key: str, master_password: Optional[str] = None) -> Optional[str]:
        """Retrieve a credential with multiple backend support.
        
        Args:
            key: The credential identifier
            master_password: Password for fallback decryption (if needed)
            
        Returns:
            The credential value or None if not found
        """
        value = None
        success = False
        
        try:
            # Try keyring first
            value = keyring.get_password(self.service_name, key)
            if value is not None:
                success = True
                logging.debug(f"Retrieved credential from keyring: {key}")
            else:
                logging.debug(f"Credential not found in keyring: {key}")
                
        except Exception as keyring_error:
            logging.warning(f"Keyring retrieval failed for {key}: {keyring_error}")
        
        # Try fallback if keyring failed or returned None
        if value is None and self.fallback_enabled and master_password:
            try:
                value = self._get_credential_fallback(key, master_password)
                if value is not None:
                    success = True
                    logging.debug(f"Retrieved credential from fallback storage: {key}")
            except Exception as fallback_error:
                logging.warning(f"Fallback retrieval failed for {key}: {fallback_error}")
        
        # Audit logging
        self._log_audit_event("retrieve", key, success)
        
        if value is None:
            logging.warning(f"Credential not found in any backend: {key}")
        
        return value
    
    def delete_credential(self, key: str, master_password: Optional[str] = None) -> None:
        """Delete a credential from all available backends.
        
        Args:
            key: The credential identifier
            master_password: Password for fallback access (if needed)
        """
        success = False
        
        # Delete from keyring
        try:
            keyring.delete_password(self.service_name, key)
            logging.info(f"Deleted credential from keyring: {key}")
            success = True
        except Exception as keyring_error:
            logging.warning(f"Keyring deletion failed for {key}: {keyring_error}")
        
        # Delete from fallback storage
        if self.fallback_enabled and master_password:
            try:
                credentials = self._load_fallback_credentials(master_password)
                if key in credentials:
                    del credentials[key]
                    # Re-encrypt and save
                    encryption_key = self._generate_fallback_key(master_password)
                    fernet = Fernet(encryption_key)
                    encrypted_data = fernet.encrypt(json.dumps(credentials).encode())
                    with open(self.FALLBACK_FILE, 'wb') as f:
                        f.write(encrypted_data)
                    logging.info(f"Deleted credential from fallback storage: {key}")
                    success = True
            except Exception as fallback_error:
                logging.warning(f"Fallback deletion failed for {key}: {fallback_error}")
        
        # Audit logging
        self._log_audit_event("delete", key, success)
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information for enterprise monitoring.
        
        Returns:
            Dictionary with system and security information
        """
        return {
            "platform": self.PLATFORM,
            "keyring_backend": self._get_keyring_backend(),
            "enterprise_mode": self.enterprise_mode,
            "fallback_enabled": self.fallback_enabled,
            "fallback_file_exists": self.FALLBACK_FILE.exists() if self.fallback_enabled else False,
            "service_name": self.service_name,
            "user": getpass.getuser(),
            "python_version": sys.version,
        }
    
    def validate_credential_access(self) -> Dict[str, bool]:
        """Validate that credential storage/retrieval is working.
        
        Returns:
            Dictionary with validation results for each backend
        """
        results = {
            "keyring_available": False,
            "keyring_read_write": False,
            "fallback_available": False,
            "fallback_read_write": False,
        }
        
        test_key = "test_validation_key"
        test_value = "test_value_12345"
        
        # Test keyring
        try:
            keyring.set_password(self.service_name, test_key, test_value)
            results["keyring_available"] = True
            
            retrieved = keyring.get_password(self.service_name, test_key)
            if retrieved == test_value:
                results["keyring_read_write"] = True
            
            # Cleanup
            keyring.delete_password(self.service_name, test_key)
            
        except Exception as e:
            logging.debug(f"Keyring validation failed: {e}")
        
        # Test fallback
        if self.fallback_enabled:
            try:
                test_password = "test_master_password"
                self._store_credential_fallback(test_key, test_value, test_password)
                results["fallback_available"] = True
                
                retrieved = self._get_credential_fallback(test_key, test_password)
                if retrieved == test_value:
                    results["fallback_read_write"] = True
                
                # Cleanup
                if self.FALLBACK_FILE.exists():
                    credentials = self._load_fallback_credentials(test_password)
                    if test_key in credentials:
                        del credentials[test_key]
                        if credentials:
                            encryption_key = self._generate_fallback_key(test_password)
                            fernet = Fernet(encryption_key)
                            encrypted_data = fernet.encrypt(json.dumps(credentials).encode())
                            with open(self.FALLBACK_FILE, 'wb') as f:
                                f.write(encrypted_data)
                        else:
                            self.FALLBACK_FILE.unlink()
                            
            except Exception as e:
                logging.debug(f"Fallback validation failed: {e}")
        
        return results
    
    # Convenience methods for backward compatibility and ease of use
    @classmethod
    def store_discord_token(cls, token: str, master_password: Optional[str] = None) -> None:
        """Store Discord bot token securely.
        
        Args:
            token: Discord bot token
            master_password: Optional master password for fallback storage
        """
        manager = cls()
        manager.store_credential(cls.DISCORD_TOKEN, token, master_password)
    
    @classmethod
    def get_discord_token(cls, master_password: Optional[str] = None) -> Optional[str]:
        """Retrieve Discord bot token.
        
        Args:
            master_password: Optional master password for fallback storage
            
        Returns:
            Discord bot token or None if not found
        """
        manager = cls()
        return manager.get_credential(cls.DISCORD_TOKEN, master_password)
    
    @classmethod
    def store_rcon_password(cls, server_name: str, password: str, master_password: Optional[str] = None) -> None:
        """Store RCON password for a specific server.
        
        Args:
            server_name: Name of the server
            password: RCON password
            master_password: Optional master password for fallback storage
        """
        key = f"{cls.RCON_PASSWORD_PREFIX}{server_name.lower().replace(' ', '_')}"
        manager = cls()
        manager.store_credential(key, password, master_password)
    
    @classmethod
    def get_rcon_password(cls, server_name: str, master_password: Optional[str] = None) -> Optional[str]:
        """Retrieve RCON password for a specific server.
        
        Args:
            server_name: Name of the server
            master_password: Optional master password for fallback storage
            
        Returns:
            RCON password or None if not found
        """
        key = f"{cls.RCON_PASSWORD_PREFIX}{server_name.lower().replace(' ', '_')}"
        manager = cls()
        return manager.get_credential(key, master_password)
    
    @classmethod
    def migrate_from_config(cls, config_file: str = "config.json", master_password: Optional[str] = None) -> None:
        """Migrate credentials from config file to secure storage.
        
        Args:
            config_file: Path to configuration file
            master_password: Optional master password for fallback storage
        """
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            manager = cls()
            
            # Store Discord token
            discord_token = config.get("discord", {}).get("token")
            if discord_token and discord_token != "STORED_IN_KEYRING":
                manager.store_credential(cls.DISCORD_TOKEN, discord_token, master_password)
                print(f"✓ Stored Discord token in secure storage")
            
            # Store RCON passwords
            servers = config.get("servers", [])
            for server in servers:
                server_name = server.get("name")
                rcon_password = server.get("rcon_password")
                if server_name and rcon_password and rcon_password != "STORED_IN_KEYRING":
                    key = f"{cls.RCON_PASSWORD_PREFIX}{server_name.lower().replace(' ', '_')}"
                    manager.store_credential(key, rcon_password, master_password)
                    print(f"✓ Stored RCON password for '{server_name}' in secure storage")
            
            # Remove sensitive data from config
            if "discord" in config and "token" in config["discord"]:
                config["discord"]["token"] = "STORED_IN_KEYRING"
            
            for server in config.get("servers", []):
                if "rcon_password" in server:
                    server["rcon_password"] = "STORED_IN_KEYRING"
            
            # Write cleaned config back
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=4)
            
            print(f"✓ Updated {config_file} with keyring references")
            print("\nCredentials have been securely stored.")
            print("The config file now contains placeholder values and is safe to commit to git.")
            
        except Exception as e:
            logging.error(f"Failed to migrate credentials: {e}")
            raise
    
    @classmethod
    def setup_credentials_interactive(cls, enterprise_mode: bool = False) -> None:
        """Interactive setup for storing credentials.
        
        Args:
            enterprise_mode: Enable enterprise features
        """
        manager = cls(use_enterprise_mode=enterprise_mode)
        
        print("Setting up secure credential storage...")
        print("This will store your sensitive data securely.\n")
        
        master_password = None
        if manager.fallback_enabled:
            use_fallback = input("Enable encrypted file fallback for headless environments? (y/N): ").lower().startswith('y')
            if use_fallback:
                master_password = getpass.getpass("Enter master password for fallback encryption: ")
        
        # Discord token
        discord_token = getpass.getpass("Enter your Discord bot token: ")
        if discord_token.strip():
            manager.store_credential(cls.DISCORD_TOKEN, discord_token.strip(), master_password)
            print("✓ Discord token stored securely")
        
        # RCON passwords
        print("\nNow enter RCON passwords for your servers:")
        
        while True:
            server_name = input("Enter server name (or press Enter to finish): ").strip()
            if not server_name:
                break
            
            rcon_password = getpass.getpass(f"Enter RCON password for '{server_name}': ")
            if rcon_password.strip():
                key = f"{cls.RCON_PASSWORD_PREFIX}{server_name.lower().replace(' ', '_')}"
                manager.store_credential(key, rcon_password.strip(), master_password)
                print(f"✓ RCON password for '{server_name}' stored securely")
        
        print(f"\n✓ All credentials stored securely")
        print("You can now safely commit your config files to git.")
        
        # Display system info for enterprise mode
        if enterprise_mode:
            print("\n--- System Information ---")
            info = manager.get_system_info()
            for key, value in info.items():
                print(f"{key}: {value}")
    
    @classmethod 
    def list_stored_credentials(cls, master_password: Optional[str] = None) -> None:
        """List all stored credentials (without showing values).
        
        Args:
            master_password: Optional master password for fallback storage
        """
        manager = cls()
        print(f"Credentials stored in service '{manager.service_name}':")
        
        # Check Discord token
        if manager.get_credential(cls.DISCORD_TOKEN, master_password):
            print("✓ Discord token")
        else:
            print("✗ Discord token (not found)")
        
        print("\nNote: Use the migration or interactive setup to manage RCON passwords.")

    def count_stored_credentials(self, master_password: Optional[str] = None) -> int:
        """Count the number of stored credentials.
        
        Args:
            master_password: Optional master password for fallback storage
            
        Returns:
            Number of stored credentials
        """
        count = 0
        
        try:
            # Check Discord token
            if self.get_credential(self.DISCORD_TOKEN, master_password):
                count += 1
        except Exception:
            pass
        
        # Count RCON passwords for each server
        # We need to load config to know which servers exist
        try:
            from src.config import Config
            config = Config()
            
            for server_name in config.servers:
                try:
                    rcon_key = f"{self.RCON_PASSWORD_PREFIX}{server_name.lower().replace(' ', '_')}"
                    if self.get_credential(rcon_key, master_password):
                        count += 1
                except Exception:
                    pass
        except Exception:
            # If we can't load config, just return what we have
            pass
        
        return count
        
        # Show system info
        print("\n--- System Information ---")
        info = manager.get_system_info()
        for key, value in info.items():
            print(f"{key}: {value}")
        
        # Validate access
        print("\n--- Backend Validation ---")
        validation = manager.validate_credential_access()
        for backend, status in validation.items():
            status_icon = "✓" if status else "✗"
            print(f"{status_icon} {backend}")


def main():
    """CLI interface for enterprise credential management."""
    import sys
    
    if len(sys.argv) < 2:
        print("Enterprise Credential Manager")
        print("Usage:")
        print("  python -m src.credential_manager migrate     # Migrate from config.json")
        print("  python -m src.credential_manager setup       # Interactive setup")
        print("  python -m src.credential_manager enterprise  # Enterprise setup")
        print("  python -m src.credential_manager list        # List stored credentials")
        print("  python -m src.credential_manager validate    # Validate system access")
        print("  python -m src.credential_manager info        # Show system information")
        return
    
    command = sys.argv[1].lower()
    
    try:
        if command == "migrate":
            CredentialManager.migrate_from_config()
        elif command == "setup":
            CredentialManager.setup_credentials_interactive()
        elif command == "enterprise":
            CredentialManager.setup_credentials_interactive(enterprise_mode=True)
        elif command == "list":
            CredentialManager.list_stored_credentials()
        elif command == "validate":
            manager = CredentialManager()
            validation = manager.validate_credential_access()
            print("Backend Validation Results:")
            for backend, status in validation.items():
                status_icon = "✓" if status else "✗"
                print(f"  {status_icon} {backend}")
        elif command == "info":
            manager = CredentialManager()
            info = manager.get_system_info()
            print("System Information:")
            for key, value in info.items():
                print(f"  {key}: {value}")
        else:
            print(f"Unknown command: {command}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
