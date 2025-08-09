# FunnyCommentator Documentation

Welcome to the FunnyCommentator documentation! This directory contains comprehensive guides and technical documentation for the FunnyCommentator ARK: Survival Evolved server management and AI commentary system.

## 📚 Documentation Index

### Essential Documentation
- **[Main README](../README.md)** - Complete feature list, installation, and quick start guide
- **[WEB_INTERFACE.md](WEB_INTERFACE.md)** - Comprehensive web interface documentation

### Security & Enterprise Features
- **[CREDENTIAL_SECURITY.md](CREDENTIAL_SECURITY.md)** - Multi-platform credential security implementation
- **[ENTERPRISE_CREDENTIALS.md](ENTERPRISE_CREDENTIALS.md)** - Enterprise-grade credential management system

## 🚀 Quick Start

### Prerequisites
Before starting, ensure you have:
1. **Python 3.7+** installed
2. **Ollama** installed and configured with at least one AI model
   - Visit [https://ollama.ai/](https://ollama.ai/) for installation instructions
   - Install a model: `ollama pull deepseek-r1:70b`

### Starting the System

**1. Web Interface:**
```bash
cd FunnyCommentator
python web/app.py
```
Then open http://127.0.0.1:5000 in your browser.

**2. Main Application:**
```bash
python run.py
```

## 🏗️ Project Structure

```
FunnyCommentator/
├── docs/                    # Documentation (you are here)
├── src/                     # Core application source code
├── web/                     # Web interface components
├── tests/                   # Test scripts and diagnostic tools
├── logs/                    # Application logs
├── config.json             # Main configuration file
├── run.py                  # Main application entry point
└── requirements.txt        # Python dependencies
```

## 🔧 Configuration

The system uses `config.json` for main configuration. The web interface provides a user-friendly way to configure:

- **Server Settings**: ARK server connections and RCON credentials
- **Discord Integration**: Bot tokens and channel configurations  
- **AI Settings**: Ollama model selection and response tone
- **Scheduler**: Automated summary generation timing
- **Security**: Credential storage and encryption settings

All sensitive credentials are stored securely in your operating system's keyring, never in plain text.

## 🛡️ Security Features

FunnyCommentator implements enterprise-grade security:

- **Multi-platform Keyring**: Native OS credential storage (Windows Credential Manager, macOS Keychain, Linux Secret Service)
- **AES-256 Encryption**: Encrypted fallback storage with PBKDF2 key derivation
- **Audit Logging**: Comprehensive logging for compliance and monitoring
- **Zero Plain-text Storage**: No credentials stored in configuration files
- **Process Management**: Secure process isolation and monitoring

## 🎮 ARK Server Management

- **Multi-server Support**: Manage multiple ARK servers from one interface
- **Cluster Management**: Group servers into clusters for coordinated summaries
- **Real-time Monitoring**: Process status, performance metrics, and health checks
- **RCON Integration**: Secure remote console access for log fetching
- **Dynamic Configuration**: Update settings without restarting the application

## 🤖 AI Commentary System

- **Configurable Personality**: Customize AI response tone (funny, sarcastic, professional, etc.)
- **Context-aware Summaries**: Server-specific context and historical awareness
- **Scheduled Generation**: Automated daily summaries sent to Discord
- **Multi-model Support**: Compatible with various Ollama AI models
- **Memory Optimization**: Smart context window management for large-scale operations

## � Web Interface Features

- **ARK-themed Design**: Beautiful Bootstrap 5 interface with ARK: Survival Evolved styling
- **Real-time Process Control**: Start, stop, restart applications from the web
- **Live Configuration**: Update settings without application restarts
- **Scheduler Management**: Configure and reload automated tasks in real-time
- **System Diagnostics**: Built-in health checks and troubleshooting tools
- **Credential Management**: Secure web-based credential storage

## �📞 Support & Troubleshooting

For technical support or questions:

1. **Check Documentation**: Review the files in this directory for detailed guides
2. **Run Diagnostics**: Use test files in `../tests/` for troubleshooting
   ```bash
   python tests/diagnose_config.py
   python tests/test_rcon.py
   python tests/test_discord.py
   ```
3. **Review Logs**: Check `../logs/process.log` for detailed application logs
4. **Verify Prerequisites**: Ensure Ollama is installed and working
   ```bash
   ollama list  # Should show installed models
   ```

## 🔄 Updates and Maintenance

The system includes built-in process management for easy maintenance:
- **Start/Stop/Restart**: Full functionality through the web interface
- **Cross-platform Compatibility**: Windows, macOS, and Linux support
- **Automatic Recovery**: Orphaned process detection and recovery
- **Real-time Monitoring**: Performance and health metrics
- **Dynamic Reloading**: Configuration updates without restarts

## ⚡ Advanced Features

- **Dynamic Scheduler Reloading**: Update schedules without restarting
- **Enterprise Security Standards**: Multi-platform credential management
- **Process Isolation**: Secure application and resource management
- **Audit Logging**: Comprehensive tracking for enterprise compliance
- **Graceful Shutdown**: Clean resource cleanup and state management

---

*Last updated: August 9, 2025*
