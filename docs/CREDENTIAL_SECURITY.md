# Credential Security Guide

This project uses secure credential storage to protect sensitive information like Discord tokens and RCON passwords.

## Why Secure Credential Storage?

- **Security**: Credentials are stored in your OS's secure credential store (Windows Credential Manager, macOS Keychain, Linux Secret Service)
- **Git Safety**: Config files contain only placeholder values, safe to commit to public repositories
- **Convenience**: No need to manage separate `.env` files or worry about accidentally committing secrets

## Initial Setup

### Option 1: Automatic Migration (Recommended)
If you already have credentials in `config.json`:

```bash
python setup_credentials.py
```

This will:
1. Install the `keyring` library
2. Move your credentials from `config.json` to secure storage
3. Replace sensitive values in `config.json` with safe placeholders

### Option 2: Manual Setup
If starting fresh or on a new machine:

```bash
# Install dependencies
pip install keyring

# Interactive credential setup
python -m src.credential_manager setup
```

## How It Works

### Before (Unsafe for Git)
```json
{
    "discord": {
        "token": "MyPrivateToken"
    },
    "servers": [
        {
            "name": "My Server",
            "rcon_password": "mysecretpassword"
        }
    ]
}
```

### After (Safe for Git)
```json
{
    "discord": {
        "token": "STORED_IN_KEYRING"
    },
    "servers": [
        {
            "name": "My Server", 
            "rcon_password": "STORED_IN_KEYRING"
        }
    ]
}
```

## Managing Credentials

### View Stored Credentials
```bash
python -m src.credential_manager list
```

### Add New Credentials
```bash
python -m src.credential_manager setup
```

### Setting Up on a New Machine
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run credential setup: `python -m src.credential_manager setup`
4. Enter your credentials when prompted

## Supported Platforms

- **Windows**: Windows Credential Manager
- **macOS**: Keychain
- **Linux**: Secret Service (requires `python3-secretstorage` or similar)

## Troubleshooting

### "Credential not found in keyring"
This means you need to set up credentials:
```bash
python -m src.credential_manager setup
```

### Linux: "No suitable backend found"
Install the Secret Service backend:
```bash
# Ubuntu/Debian
sudo apt-get install python3-secretstorage

# Or use alternative backends
pip install keyrings.alt
```

### Windows: "Access Denied"
Run the command prompt as Administrator the first time you set up credentials.

## Security Notes

- Credentials are encrypted and stored using your OS's native credential store
- Access requires your user account privileges
- No passwords are stored in plain text files
- Config files are safe to commit to public repositories
- Each server's RCON password is stored separately for better security

## Emergency Access

If you lose access to your keyring, you can:
1. Temporarily put credentials back in `config.json`
2. Run the migration script again to restore secure storage
3. Remove the plain text credentials from `config.json`
