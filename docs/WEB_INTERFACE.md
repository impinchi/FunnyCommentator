# FunnyCommentator Web Interface

A modern, responsive web-based configuration interface for the FunnyCommentator ARK server bot.

## Features

### 🎛️ **Complete Configuration Management**
- **Server Management**: Add, edit, and delete ARK server configurations
- **AI Settings**: Configure Ollama model settings and parameters
- **Credential Security**: Secure management of Discord tokens and RCON passwords
- **Scheduler Configuration**: Set up automated summary generation times
- **Real-time Status**: Monitor system status and configuration

### 🔒 **Security First**
- **Secure Credential Storage**: Uses system keyring (Windows Credential Manager, etc.)
- **No Plain Text Secrets**: All sensitive data encrypted and stored securely
- **Git-Safe Configuration**: Config files contain no sensitive information
- **Input Validation**: Comprehensive form validation and sanitization

### 📱 **Modern User Experience**
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Bootstrap 5 UI**: Clean, professional interface with accessibility support
- **Real-time Updates**: Live status monitoring and updates
- **Form Auto-save**: Automatically saves form progress
- **Toast Notifications**: User-friendly feedback and error messages

## Quick Start

### 1. Install Dependencies
```bash
pip install Flask Werkzeug keyring
```

### 2. Start Web Interface
```bash
# Default settings (http://localhost:5000) - RECOMMENDED
python web/app.py

# For development with debug mode
python web/app.py --debug

# Legacy launcher (still available)
python tests/legacy/web_interface.py --port 8080
```

### 3. Access Configuration
Open your browser to `http://localhost:5000` and start configuring your system!

## Project Structure

```
web/
├── app.py                 # Main Flask application
├── static/               # Static assets
│   ├── css/
│   │   └── style.css     # Custom styles
│   └── js/
│       └── app.js        # JavaScript functionality
└── templates/            # Jinja2 templates
    ├── base.html         # Base template with navigation
    ├── dashboard.html    # Main dashboard
    ├── servers.html      # Server list/overview
    ├── add_server.html   # Add new server form
    ├── edit_server.html  # Edit server form
    ├── credentials.html  # Credential management
    ├── ai_config.html    # AI configuration
    ├── scheduler.html    # Scheduler settings
    └── error.html        # Error pages
```

## Configuration Pages

### 🏠 **Dashboard**
- System overview and status
- Quick access to common tasks
- Real-time metrics and health indicators
- Recent activity summary

### 🖥️ **Server Management**
- Add/edit/delete ARK server configurations
- Support for all ARK maps (The Island, Ragnarok, Genesis, etc.)
- PvE/PvP configuration
- Player and tribe management
- RCON connection settings

### 🤖 **AI Configuration**
- Ollama server settings
- Model selection and parameters
- Timeout and performance tuning
- Connection testing
- Token limit configuration

### 🔐 **Credential Management**
- Secure Discord bot token storage
- RCON password management per server
- Real-time credential status
- Password visibility toggles
- Security best practices guidance

### ⏰ **Scheduler**
- Daily summary schedule configuration
- Visual time picker
- Next execution preview
- Test execution functionality
- Performance recommendations

## Security Features

### 🛡️ **Credential Protection**
- **System Keyring Integration**: Uses OS-native credential storage
- **Encrypted Storage**: All credentials encrypted at rest
- **No File Storage**: Passwords never stored in plain text files
- **User-Scoped Access**: Only accessible by the running user account

### 🔒 **Web Security**
- **Input Validation**: Server-side validation of all inputs
- **CSRF Protection**: Built-in Flask security features
- **Secure Headers**: Security headers for web protection
- **Local Access Default**: Binds to localhost by default

## API Endpoints

### Status API
```
GET /api/status
```
Returns current system status including:
- Server count and configuration
- Credential status
- AI model information
- Last update timestamp

## Customization

### 🎨 **Styling**
The interface uses Bootstrap 5 with custom CSS in `static/css/style.css`. Key customization points:

- **CSS Variables**: Easily change colors and spacing
- **Bootstrap Themes**: Supports Bootstrap theme customization
- **Responsive Breakpoints**: Mobile-first responsive design
- **Dark Mode Ready**: Structure supports future dark mode implementation

### 🔧 **Functionality**
JavaScript functionality in `static/js/app.js` provides:

- **Form Validation**: Real-time validation and feedback
- **Auto-save**: Automatic form progress saving
- **Status Updates**: Live status monitoring
- **Toast Notifications**: User feedback system
- **Utility Functions**: Common operations and helpers

## Development

### 🛠️ **Local Development**
```bash
# Enable debug mode
python web_interface.py --debug

# This enables:
# - Automatic reloading on code changes
# - Detailed error pages
# - Debug toolbar (if installed)
```

### 🧪 **Testing**
```bash
# Test configuration loading
python -c "from web.app import ConfigWebApp; app = ConfigWebApp()"

# Test credential access
python -c "from src.credential_manager import CredentialManager; print('OK' if CredentialManager.get_discord_token() else 'No token')"
```

### 📝 **Adding New Pages**
1. Create template in `web/templates/`
2. Add route handler in `web/app.py`
3. Update navigation in `templates/base.html`
4. Add any required CSS/JS

## Production Deployment

### 🚀 **WSGI Deployment**
For production use, deploy with a proper WSGI server:

```bash
# Using Gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 "web.app:create_app()"

# Using Waitress (Windows-friendly)
pip install waitress
waitress-serve --host=0.0.0.0 --port=5000 web.app:create_app
```

### 🔒 **Security Considerations**
- Use HTTPS in production
- Set strong secret key: `export FLASK_SECRET_KEY="your-secure-random-key"`
- Restrict access with firewall rules
- Regular security updates
- Monitor access logs

## Troubleshooting

### Common Issues

**"Configuration could not be loaded"**
- Check that `config.json` exists and is valid
- Ensure credentials are set up: `python -m src.credential_manager setup`

**"Credential not found in keyring"**
- Run credential setup: `python setup_credentials.py`
- Check keyring access permissions

**Web interface won't start**
- Verify Flask is installed: `pip install Flask`
- Check port availability: `netstat -an | findstr :5000`
- Review error messages in terminal

**Styling issues**
- Check Bootstrap CDN connectivity
- Verify static file serving
- Clear browser cache

### 🐛 **Debug Mode**
Enable debug mode for detailed error information:
```bash
python web_interface.py --debug
```

**⚠️ Warning**: Never use debug mode in production!

## Browser Support

- **Chrome/Chromium**: 90+
- **Firefox**: 88+
- **Safari**: 14+
- **Edge**: 90+

## Contributing

### 📋 **Development Guidelines**
1. Follow PEP 8 coding standards
2. Add docstrings to all functions
3. Use type hints where applicable
4. Test on multiple browsers
5. Ensure mobile responsiveness
6. Follow security best practices

### 🎯 **Future Enhancements**
- Dark mode support
- Multi-language support
- Advanced analytics dashboard
- Real-time log streaming
- Backup/restore functionality
- Plugin system for extensions

---

## License & Support

This web interface is part of the FunnyCommentator project and follows the same licensing terms.

For support, issues, or feature requests, please refer to the main project documentation.
