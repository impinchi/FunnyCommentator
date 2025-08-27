# FunnyCommentator

🦕 **ARK: Survival Evolved Server Management & AI Commentary System**

A comprehensive administrative platform for ARK: Survival Evolved servers featuring AI-powered commentary, web-based configuration, and automated server management.

## ✨ Key Features

- **🎮 Multi-Server Management** - Manage unlimited ARK servers with RCON integration
- **🤖 AI-Powered Commentary** - Daily AI-generated summaries of server events and player activities
- **🌐 Web Interface** - Beautiful ARK-themed web interface for configuration and control
- **🔒 Enterprise Security** - Multi-platform secure credential management
- **💬 Discord Integration** - Automated notifications and rich formatting
- **📊 IP Monitoring** - Automatic detection and notification of server IP changes
- **⏰ Smart Scheduling** - Automated tasks with configurable timing

## 🚀 Quick Start

### Prerequisites
- **Python 3.7+**
- **[Ollama](https://ollama.ai/)** with an AI model installed
- **Discord Bot Token** (optional, for notifications)

### Installation
```bash
# 1. Clone or download FunnyCommentator
git clone https://github.com/impinchi/FunnyCommentator
cd FunnyCommentator

# 2. Install dependencies
pip install -r requirements.txt

# 3. Verify Ollama is working
ollama list  # Should show installed models
```

### Usage
```bash
# Start the web interface
python web/app.py

# Configure via web browser at http://127.0.0.1:5000
# Then start the main application via the browser or:
python run.py
```

## 📖 Documentation

For comprehensive documentation, configuration guides, and advanced features, see the **[docs/](docs/)** directory:

- **[Complete Documentation](docs/README.md)** - Full feature documentation and guides


## 🔧 Basic Configuration

### Essential Settings (via web interface)
1. **Discord Bot Token** - For automated notifications
2. **ARK Server Details** - RCON host, port, and password
3. **AI Model Selection** - Choose your Ollama model and configure token management
4. **Channel Configuration** - Discord channels for notifications

### Example Configuration
```json
{
    "discord": {
        "channel_id_server_status": "your_channel_id",
        "token": "STORED_IN_KEYRING"
    },
    "servers": [
        {
            "name": "My ARK Server",
            "rcon_host": "127.0.0.1",
            "rcon_port": 27020,
            "rcon_password": "STORED_IN_KEYRING"
        }
    ],
    "ai": {
        "ollama_model": "deepseek-r1:70b",
        "input_token_size": 16000,
        "min_output_tokens": 64,
        "max_output_tokens": 5120,
        "safety_buffer": 48,
        "tokenizer_model": "gpt-3.5-turbo"
    }
}
```

## 🆘 Support

- **Documentation**: See [docs/](docs/) for comprehensive guides
- **Diagnostics**: Run `python tests/diagnose_config.py` for troubleshooting
- **Logs**: Check `logs/` directory for application logs

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

*"Survive. Evolve. Dominate." - Enhanced with AI commentary*
