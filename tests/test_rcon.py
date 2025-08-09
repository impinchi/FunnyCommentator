"""Test RCON client module."""
import pytest
from unittest.mock import MagicMock, patch
from src.rcon_client import RconClient

@pytest.fixture
def rcon_client():
    """Create a RCON client for testing."""
    return RconClient("test_host", 25575, "test_password")

def test_sanitize_log_line():
    """Test log line sanitization."""
    test_cases = [
        # Normal text
        ("Hello, world!", "Hello, world!"),
        # Control characters
        ("Hello\x00World", "HelloWorld"),
        # Long line
        ("x" * 600, "x" * 500),
        # Whitespace
        ("  Hello  World  ", "Hello  World"),
    ]
    
    for input_line, expected in test_cases:
        assert RconClient.sanitize_log_line(input_line) == expected

@pytest.mark.asyncio
async def test_fetch_logs(rcon_client):
    """Test log fetching functionality."""
    mock_logs = "line1\nline2\nline3"
    
    with patch('rcon.source.Client') as mock_client:
        # Configure the mock
        mock_instance = MagicMock()
        mock_instance.run.return_value = mock_logs
        mock_client.return_value.__enter__.return_value = mock_instance
        
        # Call the method
        logs = rcon_client.fetch_logs()
        
        # Verify results
        assert len(logs) == 3
        assert all(isinstance(line, str) for line in logs)
        mock_instance.run.assert_called_once_with("GetGameLog")

@pytest.mark.asyncio
async def test_fetch_logs_error(rcon_client):
    """Test error handling in log fetching."""
    with patch('rcon.source.Client') as mock_client:
        # Configure the mock to raise an exception
        mock_client.return_value.__enter__.side_effect = Exception("Connection failed")
        
        # Call the method
        logs = rcon_client.fetch_logs()
        
        # Verify error handling
        assert logs == []
