# FunnyCommentator Documentation

Welcome to the FunnyCommentator documentation! This directory contains comprehensive guides and technical documentation for the FunnyCommentator ARK: Survival Evolved server management and AI commentary system.

## 📚 Documentation Index

### 📖 Complete Documentation
- **[COMPLETE_DOCUMENTATION.md](COMPLETE_DOCUMENTATION.md)** - Comprehensive feature documentation, configuration guides, and technical details

## 🚀 Quick Start

### Prerequisites
Before starting, ensure you have:
1. **Python 3.7+** installed
2. **[Ollama](https://ollama.ai/)** installed and configured with at least one AI model
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
├── docs/                    # 📚 Documentation (you are here)
│   ├── COMPLETE_DOCUMENTATION.md  # Complete feature documentation
│   └── README.md                  # Documentation index and quick start
├── src/                     # 🔧 Core application source code
│   ├── main.py                    # Application orchestrator
│   ├── discord_manager.py         # Unified Discord integration
│   ├── ip_monitor_manager.py      # Consolidated IP monitoring
│   └── (other core modules)
├── web/                     # 🌐 Web interface components
├── tests/                   # 🧪 Test scripts and diagnostic tools
├── logs/                    # 📝 Application logs
├── config.json             # ⚙️ Main configuration file
├── run.py                  # 🚀 Main application entry point
└── requirements.txt        # 📦 Python dependencies
```

## ✨ Recent Updates & Improvements

### 🔄 Architecture Consolidation
- **IP Monitoring**: Consolidated from two modules to single `IPMonitorManager`
- **Discord Integration**: Enhanced `DiscordManager` with dual-mode support (client/HTTP)
- **Configuration**: Unified configuration management across web and main applications

### 🚀 New Features
- **IP Monitoring Web Interface**: Real-time monitoring with history tracking
- **Enhanced Discord Notifications**: Rich embeds for IP changes and server status
- **Improved Security**: Enhanced credential management with better error handling

### 🛠️ Technical Improvements
- **Reduced Code Duplication**: Consolidated duplicate functionality
- **Better Error Handling**: Comprehensive exception handling throughout
- **Cross-platform Compatibility**: Improved support for Windows, macOS, and Linux

## 📋 Documentation Structure

### For Users
1. **[Main README](../README.md)** - Start here for basic setup and usage
2. **[COMPLETE_DOCUMENTATION.md](COMPLETE_DOCUMENTATION.md)** - Comprehensive feature guide

### For Administrators
1. **[COMPLETE_DOCUMENTATION.md](COMPLETE_DOCUMENTATION.md)** - Advanced configuration and deployment

### For Developers
1. **[COMPLETE_DOCUMENTATION.md](COMPLETE_DOCUMENTATION.md)** - Development guide and architecture
2. **Source Code Documentation** - Inline documentation in `src/` directory
3. **Test Documentation** - Diagnostic tools in `tests/` directory

## 🆘 Getting Help

### Troubleshooting Steps
1. **Check Prerequisites**: Ensure Ollama is installed and working
2. **Run Diagnostics**: Use tools in `tests/` directory
3. **Review Logs**: Check `logs/` directory for error messages
4. **Consult Documentation**: See complete documentation for detailed guides

### Common Issues
- **Ollama Connection**: Verify Ollama is running (`ollama serve`)
- **Discord Bot**: Check token and permissions
- **RCON Issues**: Verify server settings and passwords
- **Web Interface**: Check Flask logs for errors

### Support Resources
- **Documentation**: Comprehensive guides in this directory
- **Diagnostic Tools**: Automated testing scripts in `tests/`
- **Configuration Help**: Web interface with built-in validation
- **Log Analysis**: Detailed logging for troubleshooting

---

*For the complete documentation experience, see [COMPLETE_DOCUMENTATION.md](COMPLETE_DOCUMENTATION.md)*
