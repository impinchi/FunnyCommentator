# FunnyCommentator - Complete Documentation

🦕 **ARK: Survival Evolved Server Management & AI Commentary System**

This is the comprehensive documentation for FunnyCommentator, covering all features, advanced configuration, and enterprise-grade capabilities.

## 📋 Table of Contents

- [Complete Feature List](#-complete-feature-list)
- [System Requirements](#-system-requirements)
- [Installation Guide](#-installation-guide)
- [Configuration Guide](#-configuration-guide)
- [Usage Examples](#-usage-examples)
- [Advanced Features](#️-advanced-features)
- [Architecture & Design](#-architecture--design)
- [Security Implementation](#-security-implementation)
- [API Documentation](#-api-documentation)
- [Troubleshooting](#-troubleshooting)
- [Development Guide](#-development-guide)

## ✨ Complete Feature List

### 🎮 ARK Server Management
- **Multi-server Support** - Manage unlimited ARK servers from one interface
- **Server Clusters** - Group related servers for coordinated operations
- **RCON Integration** - Secure remote console access for real-time server communication
- **Real-time Monitoring** - Server status, performance metrics, and health checks
- **Process Management** - Built-in start/stop/restart functionality with monitoring
- **Log Analysis** - Automated log fetching and analysis from ARK servers
- **Cross-platform Support** - Windows, macOS, and Linux compatibility

### 🤖 AI-Powered Commentary System
- **Intelligent Summaries** - AI-generated daily summaries of server events and player activities
- **Configurable Personality** - Choose from funny, sarcastic, professional, or custom AI tones
- **Context-Aware Analysis** - Server-specific context and historical awareness for better summaries
- **Multi-model Support** - Compatible with various Ollama AI models (deepseek-r1, llama3, etc.)
- **Memory Optimization** - Smart context window management for large-scale operations
- **Scheduled Generation** - Automated daily summaries with configurable timing
- **Event Detection** - Smart recognition of player joins/leaves, taming, deaths, and achievements

### 🌐 Web Interface & Configuration
- **ARK-themed UI** - Beautiful Bootstrap 5 interface with ARK: Survival Evolved theming
- **Real-time Process Control** - Start, stop, restart, and monitor applications from the web
- **Dynamic Configuration** - Live configuration updates without application restarts
- **Scheduler Management** - Configure and reload automated tasks in real-time
- **Credential Management** - Secure web-based credential storage and management
- **Server Configuration** - Easy setup and management of multiple ARK servers
- **Discord Integration Setup** - Simple Discord bot configuration and channel management
- **System Diagnostics** - Built-in system health checks and troubleshooting tools
- **IP Monitoring Interface** - Web-based IP monitoring with history and notifications

### 🔒 Enterprise-Grade Security
- **Multi-platform Keyring** - Native OS credential storage:
  - Windows: Windows Credential Manager
  - macOS: Keychain Access
  - Linux: Secret Service API (GNOME Keyring, KDE Wallet)
- **AES-256 Encryption** - Encrypted fallback storage with PBKDF2 key derivation
- **Zero Plain-text Storage** - No credentials stored in configuration files
- **Audit Logging** - Comprehensive logging for compliance and security monitoring
- **Key Rotation** - Built-in credential rotation and backup capabilities
- **Enterprise Deployment** - Support for containerized and CI/CD environments

### 💬 Discord Integration
- **Unified Discord Manager** - Single interface supporting both client and HTTP modes
- **Multi-channel Support** - Send summaries to different Discord channels
- **Rich Formatting** - Beautiful Discord embeds with server-specific information
- **Automated Notifications** - Daily summaries, server status updates, and IP change alerts
- **Bot Management** - Easy Discord bot setup and token management
- **Channel Configuration** - Separate channels for AI summaries, server status, and global announcements
- **HTTP API Mode** - Lightweight notifications without persistent connections

### ⏰ Automation & Scheduling
- **Dynamic Scheduler** - Configure automated tasks with live reload functionality
- **Daily Summaries** - Automated AI-generated daily reports
- **Consolidated IP Monitoring** - Automatic detection and notification of server IP changes
- **Health Monitoring** - Automated system health checks and notifications
- **Process Recovery** - Automatic detection and recovery of orphaned processes

### 🖥️ Process & System Management
- **Cross-platform Process Control** - Unified process management across operating systems
- **Graceful Shutdown** - Clean application shutdown with resource cleanup
- **Signal Handling** - Proper handling of system signals and interrupts
- **Resource Monitoring** - CPU, memory, and disk usage tracking
- **Log Management** - Automatic log rotation and cleanup

## 🖥️ System Requirements

### Hardware Requirements
- **CPU**: 2+ cores recommended (1 core minimum)
- **Memory**: 4GB RAM recommended (2GB minimum)
- **Storage**: 1GB free space + AI model storage
- **Network**: Broadband internet connection

### Software Requirements
- **Python**: 3.7+ (3.8+ recommended)
- **Operating System**: 
  - Windows 10+ or Windows Server 2016+
  - macOS 10.15+ (Catalina or later)
  - Linux (Ubuntu 18.04+, CentOS 7+, or equivalent)
- **Ollama**: Latest version with at least one AI model installed

### Network Requirements
- **Ports**: 
  - 5000 (default web interface)
  - RCON ports for your ARK servers
  - 11434 (Ollama API)
- **Internet Access**: Required for Discord integration and AI model downloads

## 🚀 Installation Guide

### 1. Install Prerequisites

**Install Python:**
- Windows: Download from [python.org](https://python.org)
- macOS: Use Homebrew: `brew install python3`
- Linux: Use package manager: `apt install python3 python3-pip`

**Install Ollama:**
1. Visit [https://ollama.ai/](https://ollama.ai/)
2. Download and install for your OS
3. Install an AI model:
   ```bash
   # Recommended model
   ollama pull deepseek-r1:70b
   
   # Alternative models
   ollama pull llama3
   ollama pull codellama
   ollama pull qwen2.5
   ```

### 2. Install FunnyCommentator

```bash
# Clone the repository
git clone <repository-url>
cd FunnyCommentator

# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python -c "import src.main; print('Installation successful!')"
```

### 3. Initial Setup

```bash
# Start web interface for configuration
python web/app.py

# Open browser to http://127.0.0.1:5000
# Configure your settings through the web interface
```

## ⚙️ Configuration Guide

### Essential Configuration

**1. Discord Bot Setup:**
1. Create a Discord application at [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a bot and copy the token
3. Invite bot to your server with appropriate permissions
4. Add token via web interface (stored securely in keyring)

**2. ARK Server Configuration:**
```json
{
    "servers": [
        {
            "name": "My PvE Server",
            "rcon_host": "127.0.0.1",
            "rcon_port": 27020,
            "rcon_password": "STORED_IN_KEYRING",
            "log_file_path": "/path/to/server/logs/ShooterGame.log",
            "is_pve": true,
            "map_name": "The Island",
            "tribe_name": "Default Tribe",
            "max_wild_dino_level": 150,
            "player_names": ["Player1", "Player2"]
        }
    ]
}
```

**3. AI Configuration:**
```json
{
    "ai": {
        "ollama_model": "deepseek-r1:70b",
        "ollama_url": "http://localhost:11434/api/generate",
        "ai_tone": "funny and sarcastic",
        "input_token_size": 16000,
        "min_output_tokens": 64,
        "max_output_tokens": 512,
        "safety_buffer": 48,
        "tokenizer_model": "gpt-3.5-turbo",
        "timeout_seconds": 10800,
        "startup_timeout_seconds": 11800,
        "ollama_start_cmd": "ollama serve"
    }
}
```

**AI Token Management Explanation:**
- `input_token_size`: Total context window size (input + output tokens)
- `min_output_tokens`: Minimum guaranteed response length (64 tokens)
- `max_output_tokens`: Maximum response length allowed (512 tokens) 
- `safety_buffer`: Reserved tokens to prevent context overflow (48 tokens)
- `tokenizer_model`: Model used for accurate token counting (gpt-3.5-turbo, gpt-4, etc.)

The system uses **dynamic token allocation** - it automatically calculates the optimal output token limit based on:
1. Actual prompt size (using tiktoken for accuracy)
2. Available context window space 
3. Safety buffer to prevent overflows
4. Configured min/max bounds

This ensures efficient memory usage while preventing out-of-memory errors.

**4. IP Monitoring Configuration:**
```json
{
    "ip_monitor": {
        "check_interval_seconds": 3600,
        "discord_notifications": true,
        "auto_monitoring": true
    }
}
```

### Advanced Configuration

**Server Clusters:**
```json
{
    "clusters": {
        "pvp_cluster": {
            "description": "PvP servers for competitive play",
            "servers": ["PvP Island", "PvP Ragnarok"]
        },
        "pve_cluster": {
            "description": "PvE servers for casual play",
            "servers": ["PvE The Center", "PvE Extinction"]
        }
    }
}
```

**Scheduler Configuration:**
```json
{
    "scheduler": {
        "logs_summary_hour": 3,
        "logs_summary_minute": 0
    }
}
```

## 📖 Usage Examples

### Managing Multiple ARK Servers

**1. Add Servers via Web Interface:**
- Navigate to "Servers" section
- Click "Add Server"
- Fill in RCON details and server information
- Test RCON connection
- Save configuration

**2. Create Server Clusters:**
- Go to "Clusters" section
- Create logical groupings (e.g., "PvP Cluster", "PvE Cluster")
- Assign servers to clusters
- Configure cluster-specific settings

**3. Set Up Automated Summaries:**
- Configure AI model and tone
- Set summary generation schedule
- Assign Discord channels for each cluster
- Test summary generation

### Customizing AI Commentary

**AI Tone Examples:**
- **Funny**: "Sarcastic and humorous observations about player fails"
- **Professional**: "Detailed technical analysis of server events"
- **Community**: "Friendly and encouraging commentary for casual players"
- **Custom**: Define your own personality and style

**Context Configuration:**
```json
{
    "servers": [
        {
            "name": "Dragon Tamers PvP",
            "tribe_name": "Dragon Lords",
            "player_names": ["ChiefDragon", "DragonRider"],
            "map_name": "Scorched Earth",
            "max_wild_dino_level": 150
        }
    ]
}
```

### Security Best Practices

**1. Credential Management:**
- Always use the web interface to store credentials
- Never put passwords in config.json files
- Use keyring storage for all sensitive data
- Enable audit logging

**2. Network Security:**
- Use strong RCON passwords
- Limit RCON access to trusted IPs
- Use Discord bot tokens with minimal permissions
- Monitor access logs regularly

**3. System Security:**
- Run with non-root/non-admin privileges when possible
- Keep Python and dependencies updated
- Use encrypted fallback storage in production
- Enable comprehensive logging

## 🏗️ Advanced Features

### IP Monitoring System

**Consolidated Architecture:**
- Single `IPMonitorManager` class handles all IP monitoring
- Supports both main application and web interface
- Automatic Discord notifications via enhanced `DiscordManager`
- Database logging of IP changes with history

**Configuration:**
```json
{
    "ip_monitor": {
        "check_interval_seconds": 3600,
        "discord_notifications": true,
        "auto_monitoring": true,
        "history_retention_days": 30
    }
}
```

**Web Interface Features:**
- Real-time IP monitoring status
- IP change history with timestamps
- Manual IP checks
- Notification testing

### Enhanced Discord Integration

**Dual Mode Support:**
- **Client Mode**: Persistent connection for main application
- **HTTP Mode**: Stateless API calls for web interface

**Usage Examples:**
```python
# Client mode (main application)
discord = DiscordManager(token, use_client=True)
await discord.send_message("Server starting up!", channel_id)

# HTTP mode (web interface)  
discord = DiscordManager(token, use_client=False)
await discord.send_message("IP changed!", channel_id, embed=embed_data)
```

**Rich Embed Support:**
```python
embed = {
    "title": "Server Status Update",
    "color": 0x00ff41,
    "fields": [
        {"name": "Status", "value": "Online", "inline": True},
        {"name": "Players", "value": "5/20", "inline": True}
    ],
    "footer": {"text": "ARK Server Monitor"}
}
```

### Process Management

**Cross-platform Support:**
- Windows: Process creation via subprocess with proper signal handling
- Linux/macOS: Fork/exec with signal management
- Graceful shutdown with resource cleanup

**Features:**
- Process monitoring and health checks
- Automatic restart on failure
- Resource usage tracking
- Log file management

### Database Integration

**Data Storage:**
- SQLite database for configuration and history
- IP change logging with timestamps
- AI summary history
- Audit trail for security compliance

**Schema:**
```sql
-- IP monitoring history
CREATE TABLE ip_changes (
    id INTEGER PRIMARY KEY,
    old_ip_address TEXT,
    ip_address TEXT NOT NULL,
    changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    change_type TEXT DEFAULT 'auto',
    notified BOOLEAN DEFAULT 0
);

-- AI summary history  
CREATE TABLE cluster_summaries (
    id INTEGER PRIMARY KEY,
    cluster_name TEXT NOT NULL,
    summary TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## 🔐 Security Implementation

### Multi-platform Credential Management

**Windows Implementation:**
```python
import keyring
keyring.set_password("FunnyCommentator", "discord_token", token)
stored_token = keyring.get_password("FunnyCommentator", "discord_token")
```

**Security Features:**
- Native OS integration
- AES-256 encrypted fallback
- PBKDF2 key derivation
- No plain-text storage
- Audit logging

### Enterprise Security Features

**Compliance:**
- SOC 2 Type II compatible logging
- GDPR compliance for player data
- Audit trail for all credential access
- Encrypted data at rest and in transit

**Deployment:**
- Container-friendly credential management
- CI/CD pipeline integration
- Automated backup and recovery
- Key rotation capabilities

## 🧪 Testing & Diagnostics

### Built-in Diagnostic Tools

```bash
# Configuration validation
python tests/diagnose_config.py

# Cross-platform compatibility test
python tests/test_cross_platform.py

# Discord connectivity test
python tests/test_discord.py

# RCON connection test
python tests/test_rcon.py

# IP monitoring test
python tests/test_ip_monitor.py

# Web interface test
python tests/test_web_config.py
```

### Manual Testing

**Discord Integration:**
```bash
# Test enhanced Discord manager
python test_discord_enhanced.py

# Test both client and HTTP modes
python -c "
from src.discord_manager import DiscordManager
import asyncio

async def test():
    # HTTP mode test
    dm = DiscordManager('your_token', use_client=False)
    await dm.send_message('Test message', channel_id)

asyncio.run(test())
"
```

**IP Monitoring:**
```bash
# Test IP monitoring manager
python -c "
from src.ip_monitor_manager import IPMonitorManager
from src.config import Config
import asyncio

async def test():
    config = Config()
    from src.database import DatabaseManager
    db = DatabaseManager(config.db_path, {})
    
    ip_manager = IPMonitorManager(config, db, None)
    result = await ip_manager.perform_ip_check_and_notify()
    print('IP check result:', result)

asyncio.run(test())
"
```

## 📞 Troubleshooting

### Common Issues

**1. Ollama Connection Issues:**
```bash
# Check Ollama status
ollama list
ollama serve  # Start Ollama if not running

# Test Ollama connectivity
curl http://localhost:11434/api/tags
```

**2. RCON Connection Problems:**
```bash
# Test RCON manually
python -c "
from src.rcon_client import RconClient
client = RconClient('127.0.0.1', 27020, 'your_password')
result = client.execute_command('ListPlayers')
print(result)
"
```

**3. Discord Bot Issues:**
```bash
# Test Discord connectivity
python tests/test_discord.py

# Check bot permissions in Discord server:
# - Send Messages
# - Embed Links  
# - Read Message History
```

**4. Web Interface Problems:**
```bash
# Check Flask logs
python web/app.py
# Look for error messages in console

# Test API endpoints
curl http://localhost:5000/api/ip/status
```

**5. IP Monitoring Issues:**
```bash
# Test IP monitoring
python -c "
from src.ip_monitor_manager import IPMonitorManager
from src.config import Config
import asyncio

async def test():
    config = Config()
    current_ip = await IPMonitorManager.check_current_ip()
    print(f'Current IP: {current_ip}')

asyncio.run(test())
"
```

### Log Analysis

**Log Locations:**
- **Application logs**: `logs/application.log`
- **Process logs**: `logs/process.log`
- **AI logs**: `aiLogsResponder.log`
- **Web logs**: Console output from Flask

**Important Log Patterns:**
```bash
# Discord connection issues
grep "Discord.*error" logs/*.log

# RCON failures
grep "RCON.*failed" logs/*.log

# IP monitoring
grep "IP.*changed" logs/*.log

# AI processing errors
grep "Ollama.*error" logs/*.log
```

## 💻 Development Guide

### Code Architecture

**Design Principles:**
- **Single Responsibility**: Each module has a focused purpose
- **Dependency Injection**: Components are loosely coupled
- **Configuration Driven**: Behavior controlled via config files
- **Cross-platform**: Works on Windows, macOS, and Linux

**Key Modules:**
```
src/
├── main.py                 # Application orchestrator
├── config.py              # Configuration management
├── discord_manager.py     # Unified Discord integration
├── ip_monitor_manager.py  # Consolidated IP monitoring
├── ollama_manager.py      # AI model management
├── rcon_client.py         # ARK server communication
├── credential_manager.py  # Secure credential storage
├── database.py            # Data persistence
└── process_manager.py     # System process control
```

### Recent Architectural Improvements

**1. IP Monitoring Consolidation:**
- Merged `ip_monitor.py` and `ip_monitor_manager.py`
- Single `IPMonitorManager` class for all IP monitoring
- Unified interface for main app and web interface

**2. Discord Integration Enhancement:**
- Enhanced `DiscordManager` with dual-mode support
- Removed redundant `discord_http.py` module
- Unified API for client and HTTP modes

**3. Configuration Improvements:**
- Centralized configuration management
- Web-based credential storage
- Real-time configuration updates

### Contributing Guidelines

**Code Standards:**
- **PEP 8**: Python style guide compliance
- **PEP 257**: Comprehensive docstrings
- **Type Hints**: Use typing module for better code clarity
- **Error Handling**: Comprehensive exception handling

**Testing Requirements:**
- Unit tests for critical components
- Integration tests for external services
- Cross-platform compatibility testing
- Security testing for credential management

**Documentation:**
- Update README.md for user-facing changes
- Add technical documentation for new features
- Include usage examples and configuration guides
- Maintain API documentation

## 📄 License & Credits

**MIT License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**Powered by:**
- [Ollama](https://ollama.ai/) - Local AI model execution
- [Discord.py](https://discordpy.readthedocs.io/) - Discord bot integration  
- [Flask](https://flask.palletsprojects.com/) - Web interface framework
- [APScheduler](https://apscheduler.readthedocs.io/) - Task scheduling
- [Bootstrap 5](https://getbootstrap.com/) - UI framework
- [aiohttp](https://docs.aiohttp.org/) - HTTP client for Discord API

**Architecture:**
- Cross-platform credential management
- Enterprise-grade security implementation
- Modular design with separation of concerns
- Modern async/await Python patterns

---

*"Survive. Evolve. Dominate." - Enhanced with cutting-edge AI commentary and enterprise-grade management tools*
