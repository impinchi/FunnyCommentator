# Enterprise Credential Management

## Overview

FunnyCommentator now includes enterprise-level credential management with cross-platform support, secure fallback options, and comprehensive audit logging.

## Enterprise Features

### 🔒 **Multi-Platform Security**
- **Windows**: Windows Credential Manager (secure vault)
- **macOS**: Keychain integration
- **Linux**: Secret Service API (GNOME Keyring, KDE Wallet)
- **Fallback**: AES-256 encrypted file storage for headless/CI environments

### 📊 **Enterprise Compliance**
- **Audit Logging**: Complete access logs with timestamps and user information
- **Key Rotation**: Secure master key rotation for encrypted storage
- **Export/Import**: Encrypted credential backup and migration
- **System Validation**: Real-time backend health checks
- **Platform Detection**: Automatic optimal backend selection

### 🛡️ **Security Standards**
- **PBKDF2**: 100,000 iterations for key derivation
- **AES-256**: Fernet encryption for fallback storage
- **Secure Permissions**: Restricted file access (Unix: 0600)
- **Memory Safety**: Secure credential handling
- **No Plain Text**: Credentials never stored in plain text

## Quick Start

### Enterprise Setup
```bash
# Interactive enterprise setup with audit logging
python -m src.credential_manager enterprise

# Standard setup
python -m src.credential_manager setup

# Migrate existing configuration
python -m src.credential_manager migrate
```

### System Validation
```bash
# Check all backend availability
python -m src.credential_manager validate

# View system information
python -m src.credential_manager info

# List stored credentials
python -m src.credential_manager list
```

## Platform Support

### Windows
- **Primary**: Windows Credential Manager
- **Location**: Control Panel → User Accounts → Credential Manager
- **Security**: Windows-native secure vault
- **Access**: Current user only

### macOS
- **Primary**: Keychain Access
- **Location**: Applications → Utilities → Keychain Access
- **Security**: macOS-native keychain
- **Access**: User keychain with secure enclave

### Linux
- **Primary**: Secret Service API
- **Backends**: GNOME Keyring, KDE Wallet, others
- **Location**: DE-specific secure storage
- **Security**: Desktop environment integration

### Fallback (All Platforms)
- **Primary**: Encrypted file storage
- **Location**: `~/.funnycommentator/secure/credentials.enc`
- **Security**: PBKDF2 + AES-256 encryption
- **Use Cases**: Headless servers, CI/CD, Docker containers

## Enterprise Administration

### Command Line Interface

```bash
# Enterprise credential management
python -m src.credential_manager --help

Available commands:
  migrate     - Migrate from config.json
  setup       - Interactive setup
  enterprise  - Enterprise setup with audit logging
  list        - List stored credentials
  validate    - Validate system access
  info        - Show system information
```

### Programmatic Usage

```python
from src.credential_manager import CredentialManager

# Create enterprise manager
manager = CredentialManager(use_enterprise_mode=True)

# Store credential with fallback
manager.store_credential("api_key", "secret", master_password="fallback_pass")

# Retrieve credential
api_key = manager.get_credential("api_key", master_password="fallback_pass")

# System information
info = manager.get_system_info()
print(f"Platform: {info['platform']}")
print(f"Backend: {info['keyring_backend']}")

# Validate backends
validation = manager.validate_credential_access()
if validation['keyring_read_write']:
    print("Keyring backend operational")
```

### Enterprise Features

#### Key Rotation
```python
# Rotate master encryption key
manager.rotate_master_key("old_password", "new_password")
```

#### Credential Export/Import
```python
# Export for backup/migration
encrypted_backup = manager.export_credentials("export_password")

# Import from backup
manager.import_credentials(encrypted_backup, "export_password")
```

#### Audit Logging
```bash
# View audit logs
cat ~/.funnycommentator/audit/credential_access.log

# Example log entry:
# 2025-08-08 17:30:15,123 - INFO - STORE - Key: disc**** - Status: SUCCESS - User: admin - Platform: windows
```

## Configuration

### Environment Variables
```bash
# Force fallback mode (useful for CI/CD)
export FUNNYCOMMENTATOR_FORCE_FALLBACK=true

# Custom audit log location
export FUNNYCOMMENTATOR_AUDIT_DIR="/var/log/funnycommentator"

# Enterprise service name
export FUNNYCOMMENTATOR_ENTERPRISE_MODE=true
```

### Web Interface Integration

The web interface automatically detects and uses the new credential system:

1. **Credential Status**: Real-time backend health in dashboard
2. **Secure Forms**: Credentials stored via enterprise manager
3. **Platform Info**: System details displayed in settings
4. **Fallback Support**: Automatic fallback for headless deployments

## Security Best Practices

### Development
- Use environment-specific service names
- Enable audit logging for compliance
- Regular key rotation schedules
- Backup credential exports securely

### Production
- Deploy with enterprise mode enabled
- Monitor audit logs for compliance
- Use fallback storage for containers
- Implement credential rotation policies

### CI/CD Integration
```yaml
# Example GitHub Actions integration
- name: Setup Credentials
  env:
    MASTER_PASSWORD: ${{ secrets.MASTER_PASSWORD }}
  run: |
    echo "${{ secrets.DISCORD_TOKEN }}" | python -m src.credential_manager import
```

## Troubleshooting

### Backend Issues
```bash
# Test keyring access
python -c "import keyring; print(keyring.get_keyring())"

# Validate all backends
python -m src.credential_manager validate
```

### Common Problems

**"Keyring backend not available"**
- Linux: Install `python3-secretstorage` or `python3-keyring`
- macOS: Ensure Keychain Access permissions
- Windows: Check Windows Credential Manager access

**"Fallback encryption failed"**
- Verify master password
- Check file permissions: `ls -la ~/.funnycommentator/secure/`
- Ensure directory write access

**"Audit logging failed"**
- Check audit directory permissions
- Verify disk space availability
- Review log file ownership

### Performance Considerations

- **Keyring Access**: ~10-50ms per operation
- **Fallback Storage**: ~100-200ms with encryption
- **Memory Usage**: Minimal overhead (~1-2MB)
- **Audit Logging**: Asynchronous, no performance impact

## Migration Guide

### From Basic Keyring
```bash
# Existing setup continues to work
python -m src.credential_manager list

# Upgrade to enterprise features
python -m src.credential_manager enterprise
```

### From Plain Text Config
```bash
# Migrate existing config.json
python -m src.credential_manager migrate

# Verify migration
python -m src.credential_manager validate
```

### Cross-Platform Migration
```bash
# Export from source system
python -m src.credential_manager export > backup.enc

# Import on target system
python -m src.credential_manager import < backup.enc
```

## Support Matrix

| Platform | Keyring | Fallback | Audit | Enterprise |
|----------|---------|----------|-------|------------|
| Windows 10/11 | ✅ | ✅ | ✅ | ✅ |
| macOS 12+ | ✅ | ✅ | ✅ | ✅ |
| Ubuntu 20.04+ | ✅ | ✅ | ✅ | ✅ |
| RHEL 8+ | ✅ | ✅ | ✅ | ✅ |
| Alpine Linux | ⚠️ | ✅ | ✅ | ✅ |
| Docker | ⚠️ | ✅ | ✅ | ✅ |

Legend:
- ✅ Full support
- ⚠️ Fallback mode recommended
- ❌ Not supported

---

This enterprise credential management system provides the security, compliance, and cross-platform compatibility required for professional deployment environments while maintaining backward compatibility with existing configurations.
