# FunnyCommentator Tests

This directory contains test scripts, diagnostic tools, and legacy code for the FunnyCommentator project.

## 📁 Directory Structure

```
tests/
├── README.md                   # This file
├── legacy/                     # Legacy scripts and deprecated code
│   └── web_interface.py       # Legacy web interface launcher
├── test_config.py             # Configuration system tests
├── test_cross_platform.py     # Cross-platform compatibility tests
├── test_database.py           # Database functionality tests
├── test_discord.py            # Discord integration tests
├── test_rcon.py               # RCON connection tests
├── test_web_config.py         # Web interface configuration tests
├── debug_config.py            # Configuration debugging utility
└── diagnose_config.py         # Configuration diagnostic tool
```

## 🧪 Test Scripts

### Core Tests
- **`test_config.py`** - Tests configuration loading and validation
- **`test_cross_platform.py`** - Validates cross-platform process management
- **`test_database.py`** - Tests database operations and connections
- **`test_discord.py`** - Tests Discord bot integration
- **`test_rcon.py`** - Tests RCON server connections
- **`test_web_config.py`** - Tests web interface configuration handling

### Diagnostic Tools
- **`debug_config.py`** - Interactive configuration debugging
- **`diagnose_config.py`** - Automated configuration diagnosis

### Legacy Code
- **`legacy/web_interface.py`** - Original web interface launcher (deprecated)

## 🚀 Running Tests

### Individual Tests
```bash
# Test cross-platform compatibility
python tests/test_cross_platform.py

# Test configuration system
python tests/test_config.py

# Test RCON connections
python tests/test_rcon.py

# Test Discord integration
python tests/test_discord.py

# Test database operations
python tests/test_database.py

# Test web configuration
python tests/test_web_config.py
```

### Diagnostic Tools
```bash
# Debug configuration issues
python tests/debug_config.py

# Run configuration diagnostics
python tests/diagnose_config.py
```

### Legacy Scripts
```bash
# Use legacy web interface launcher (if needed)
python tests/legacy/web_interface.py --port 8080
```

## 📋 Test Requirements

Most tests require the same dependencies as the main application:
```bash
pip install -r requirements.txt
```

Some tests may require additional setup:
- **RCON tests**: Require running ARK servers with RCON enabled
- **Discord tests**: Require valid Discord bot tokens
- **Database tests**: Require write permissions to create test databases

## 🛠️ Development Testing

When developing new features:

1. **Run relevant tests** to ensure compatibility
2. **Add new tests** for new functionality
3. **Update existing tests** when changing behavior
4. **Test cross-platform** compatibility using `test_cross_platform.py`

## 🐛 Debugging

If you encounter issues:

1. **Run diagnostic tools** first:
   ```bash
   python tests/diagnose_config.py
   ```

2. **Check specific component tests**:
   ```bash
   python tests/test_config.py
   python tests/test_rcon.py
   ```

3. **Enable debug mode** in the web interface:
   ```bash
   python web/app.py --debug
   ```

4. **Check logs** in the `logs/` directory

## 📝 Test Output

Tests provide detailed output including:
- ✅ **Success indicators** for passing tests
- ❌ **Error messages** for failing tests
- 📊 **System information** and compatibility details
- 🔍 **Diagnostic information** for troubleshooting

## 🔄 Continuous Integration

For automated testing environments:
- All tests are designed to run without user interaction
- Tests handle missing dependencies gracefully
- Cross-platform tests adapt to the current operating system
- Diagnostic tools provide machine-readable output when needed

---

*For more information, see the main documentation in the `docs/` directory.*
