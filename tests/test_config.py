"""Test configuration module."""
import os
import pytest
from src.config import Config

@pytest.fixture
def mock_env(monkeypatch):
    """Provide mock environment variables."""
    env_vars = {
        "LOG_LEVEL": "DEBUG",
        "RCON_HOST": "test_host",
        "RCON_PORT": "25575",
        "RCON_PASSWORD": "test_password",
        "DISCORD_TOKEN": "test_token",
        "DISCORD_CHANNEL_ID": "123456789",
        "DISCORD_CHANNEL_ID_SERVER_STATUS": "987654321",
        "DISCORD_CHANNEL_ID_AI": "123789456",
        "OLLAMA_URL": "http://localhost:11434",
        "OLLAMA_MODEL": "test_model",
        "OLLAMA_START_CMD": "test_cmd",
        "AI_TIMEOUT_SECONDS": "30",
        "IP_RETRY_SECONDS": "300",
        "DB_PATH": "test.sqlite",
        "INPUT_TOKEN_SIZE": "16000",
        "PREVIOUS_IP": "127.0.0.1"
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

def test_config_singleton():
    """Test that Config is a singleton."""
    config1 = Config()
    config2 = Config()
    assert config1 is config2

def test_config_values(mock_env):
    """Test that Config loads values correctly."""
    config = Config()
    assert config.log_level == "DEBUG"
    assert config.rcon_host == "test_host"
    assert config.rcon_port == 25575
    assert config.rcon_password == "test_password"
    assert config.discord_token == "test_token"
    assert config.channel_id_global == 123456789
    assert config.channel_id_server_status == 987654321
    assert config.channel_id_ai == 123789456
    assert config.ollama_url == "http://localhost:11434"
    assert config.ollama_model == "test_model"
    assert config.ollama_start_cmd == "test_cmd"
    assert config.ai_timeout_seconds == 30
    assert config.ip_retry_seconds == 300
    assert config.db_path == "test.sqlite"
    assert config.input_token_size == 16000
    assert config.previous_ip == "127.0.0.1"
