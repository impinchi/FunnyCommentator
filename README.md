# FunnyCommentator

🦕 **ARK: Survival Evolved Server Management & AI Commentary System**

A comprehensive administrative platform for ARK: Survival Evolved servers featuring AI-powered commentary, web-based configuration, enterprise-grade security, and cross-platform process management.

## ✨ Complete Feature List

### 🎮 **ARK Server Management**
- **Multi-server Support** - Manage unlimited ARK servers from one interface
- **Server Clusters** - Group related servers for coordinated operations
- **RCON Integration** - Secure remote console access for real-time server communication
- **Real-time Monitoring** - Server status, performance metrics, and health checks
- **Process Management** - Built-in start/stop/restart functionality with monitoring
- **Log Analysis** - Automated log fetching and analysis from ARK servers
- **Cross-platform Support** - Windows, macOS, and Linux compatibility

### 🤖 **AI-Powered Commentary System**
- **Intelligent Summaries** - AI-generated daily summaries of server events and player activities
- **Configurable Personality** - Choose from funny, sarcastic, professional, or custom AI tones
- **Context-Aware Analysis** - Server-specific context and historical awareness for better summaries
- **Multi-model Support** - Compatible with various Ollama AI models (deepseek-r1, llama3, etc.)
- **Memory Optimization** - Smart context window management for large-scale operations
- **Scheduled Generation** - Automated daily summaries with configurable timing
- **Event Detection** - Smart recognition of player joins/leaves, taming, deaths, and achievements

### 🌐 **Web Interface & Configuration**
- **ARK-themed UI** - Beautiful Bootstrap 5 interface with ARK: Survival Evolved theming
- **Real-time Process Control** - Start, stop, restart, and monitor applications from the web
- **Dynamic Configuration** - Live configuration updates without application restarts
- **Scheduler Management** - Configure and reload automated tasks in real-time
- **Credential Management** - Secure web-based credential storage and management
- **Server Configuration** - Easy setup and management of multiple ARK servers
- **Discord Integration Setup** - Simple Discord bot configuration and channel management
- **System Diagnostics** - Built-in system health checks and troubleshooting tools

### 🔒 **Enterprise-Grade Security**
- **Multi-platform Keyring** - Native OS credential storage:
  - Windows: Windows Credential Manager
  - macOS: Keychain Access
  - Linux: Secret Service API (GNOME Keyring, KDE Wallet)
- **AES-256 Encryption** - Encrypted fallback storage with PBKDF2 key derivation
- **Zero Plain-text Storage** - No credentials stored in configuration files
- **Audit Logging** - Comprehensive logging for compliance and security monitoring
- **Key Rotation** - Built-in credential rotation and backup capabilities
- **Enterprise Deployment** - Support for containerized and CI/CD environments

### 💬 **Discord Integration**
- **Multi-channel Support** - Send summaries to different Discord channels
- **Rich Formatting** - Beautiful Discord embeds with server-specific information
- **Automated Notifications** - Daily summaries, server status updates, and alerts
- **Bot Management** - Easy Discord bot setup and token management
- **Channel Configuration** - Separate channels for AI summaries, server status, and global announcements

### ⏰ **Automation & Scheduling**
- **Dynamic Scheduler** - Configure automated tasks with live reload functionality
- **Daily Summaries** - Automated AI-generated daily reports
- **IP Monitoring** - Automatic detection and notification of server IP changes
- **Health Monitoring** - Automated system health checks and notifications
- **Process Recovery** - Automatic detection and recovery of orphaned processes

### 🖥️ **Process & System Management**
- **Cross-platform Process Control** - Unified process management across operating systems
- **Graceful Shutdown** - Clean application shutdown with resource cleanup
- **Signal Handling** - Proper handling of system signals and interrupts
- **Resource Monitoring** - CPU, memory, and disk usage tracking
- **Log Management** - Automatic log rotation and cleanup

## 🚀 Prerequisites & Installation

### **Required: Ollama AI Platform**

FunnyCommentator requires [Ollama](https://ollama.ai/) to be installed and configured on your system.

**Install Ollama:**
1. Visit [https://ollama.ai/](https://ollama.ai/)
2. Download and install Ollama for your operating system
3. Install a compatible AI model (recommended: `deepseek-r1:70b` or `llama3`)

```bash
# Example: Install recommended model
ollama pull deepseek-r1:70b

# Alternative models
ollama pull llama3
ollama pull codellama
```

**Note:** Ollama installation, model selection, and AI model management are outside the scope of this documentation. Please refer to the official Ollama documentation for detailed setup instructions.

### **System Requirements**
- **Python 3.7+** (3.8+ recommended)
- **Operating System**: Windows 10+, macOS 10.15+, or Linux
- **Memory**: 2GB RAM minimum (4GB+ recommended for AI models)
- **Storage**: 500MB for application + space for AI models
- **Network**: Internet access for AI models and Discord integration
- **Ollama**: Must be installed and configured with at least one AI model

### **Installation Steps**

1. **Clone or download FunnyCommentator**
2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Verify Ollama is working:**
   ```bash
   ollama list  # Should show installed models
   ```

## 🚀 Quick Start Guide

### **1. Start Web Interface**
```bash
python web/app.py
```

### **2. Initial Configuration**
Open http://127.0.0.1:5000 in your browser and configure:

**Essential Settings:**
- **Discord Bot Token** - Create a Discord application and bot
- **Discord Channel IDs** - Channels for AI summaries and notifications
- **ARK Server Details** - RCON host, port, and password for each server
- **AI Model Selection** - Choose your installed Ollama model
- **Scheduler Timing** - When to generate daily summaries

**Optional Settings:**
- **Server Clusters** - Group related servers
- **AI Personality** - Customize the AI commentary tone
- **Security Settings** - Advanced credential and encryption options

### **3. Start Main Application**
Use the web interface process control panel or run manually:
```bash
python run.py
```

### **4. Monitor & Manage**
- Check the web interface dashboard for system status
- View logs in the `logs/` directory
- Monitor Discord channels for AI summaries

## 📖 Usage Examples

### **Managing Multiple ARK Servers**
1. Add each server in the web interface with RCON details
2. Group related servers into clusters (e.g., "PvP Cluster", "PvE Cluster")
3. Configure different Discord channels for different server groups
4. Set up automated daily summaries for each cluster

### **Customizing AI Commentary**
1. Choose an AI model that fits your server's personality
2. Configure the AI tone (funny, sarcastic, professional, custom)
3. Set up server-specific context (map name, tribe names, player names)
4. Schedule daily summaries at optimal times for your community

### **Security Best Practices**
1. Use the web interface to store all credentials securely
2. Never put passwords directly in config files
3. Regularly rotate Discord bot tokens and RCON passwords
4. Monitor audit logs for unauthorized access attempts

## 📁 Project Structure

```
FunnyCommentator/
├── src/                     # � Core application source code
│   ├── main.py             #     Main application orchestrator
│   ├── config.py           #     Configuration management
│   ├── discord_manager.py  #     Discord integration
│   ├── ollama_manager.py   #     AI model management
│   ├── rcon_client.py      #     ARK RCON communication
│   ├── credential_manager.py #   Secure credential storage
│   ├── database.py         #     Data persistence
│   └── process_manager.py  #     System process control
├── web/                     # 🌐 Web interface
│   ├── app.py              #     Flask web application
│   ├── templates/          #     HTML templates
│   └── static/             #     CSS, JS, and assets
├── docs/                    # 📚 Documentation
├── tests/                   # 🧪 Test scripts and diagnostics
├── logs/                    # 📝 Application logs
├── config.json             # ⚙️ Main configuration file
├── run.py                  # 🚀 Application entry point
└── requirements.txt        # 📦 Python dependencies
```

## �️ Advanced Configuration

### **AI Model Selection**
- **deepseek-r1:70b** - Recommended for detailed, contextual summaries
- **llama3** - Good balance of performance and quality
- **codellama** - Better for technical server analysis

### **Scheduler Configuration**
- Configure multiple schedules for different server groups
- Set up maintenance windows with automated notifications
- Create custom automation scripts for server management

### **Security Hardening**
- Enable audit logging for compliance requirements
- Configure encrypted fallback storage for headless environments
- Set up key rotation schedules for enterprise deployments

## 🧪 Testing & Diagnostics

Run diagnostic tools to verify your setup:

```bash
# Test configuration
python tests/diagnose_config.py

# Test cross-platform compatibility  
python tests/test_cross_platform.py

# Test Discord connectivity
python tests/test_discord.py

# Test RCON connections
python tests/test_rcon.py
```

## 📞 Troubleshooting & Support

### **Common Issues**
1. **Ollama not found** - Ensure Ollama is installed and in PATH
2. **RCON connection failed** - Verify server RCON settings and passwords
3. **Discord bot not responding** - Check bot token and permissions
4. **Scheduler not running** - Verify system time and timezone settings

### **Getting Help**
1. Check documentation in `docs/` directory
2. Run diagnostic tools in `tests/` directory  
3. Review application logs in `logs/` directory
4. Verify Ollama installation and model availability

### **Log Locations**
- **Application logs**: `logs/process.log`
- **Web interface logs**: Console output when running `web/app.py`
- **System logs**: OS-specific event logs for process management

## 🔧 Development & Contributing

### **Code Standards**
- **PEP 8**: Python code style guide
- **PEP 257**: Docstring conventions
- **Modular Design**: Separation of concerns and SOLID principles
- **Cross-platform**: Test on Windows, macOS, and Linux
- **Security First**: No plain-text credentials, secure by default

### **Architecture Principles**
- **Fat Models, Thin Views**: Business logic in models, presentation in views
- **Enterprise Security**: Multi-platform credential management
- **Platform Independence**: Works across Windows, Linux, and macOS
- **Responsive Design**: Web interface works on desktop and mobile

## 📄 License

**MIT License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**What this means:**
- ✅ **Commercial use** - Use in commercial projects
- ✅ **Modification** - Modify and adapt the code
- ✅ **Distribution** - Share and distribute freely
- ✅ **Private use** - Use for personal projects
- ✅ **No warranty** - Software provided "as is"
- ⚠️ **Credit required** - Must include original copyright notice

## 🙏 Credits & Acknowledgments

**Powered by:**
- [Ollama](https://ollama.ai/) - Local AI model execution
- [Discord.py](https://discordpy.readthedocs.io/) - Discord bot integration  
- [Flask](https://flask.palletsprojects.com/) - Web interface framework
- [APScheduler](https://apscheduler.readthedocs.io/) - Task scheduling
- [Bootstrap 5](https://getbootstrap.com/) - UI framework

**Special Thanks:**
- ARK: Survival Evolved community for inspiration
- Open source contributors and maintainers

---

*"Survive. Evolve. Dominate." - Enhanced with cutting-edge AI commentary*
