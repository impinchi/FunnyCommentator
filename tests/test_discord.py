"""Test Discord manager module."""
import pytest
from unittest.mock import MagicMock, patch
from src.discord_manager import DiscordManager

@pytest.fixture
def discord_manager():
    """Create a Discord manager for testing."""
    return DiscordManager("test_token")

def test_split_text_empty():
    """Test splitting empty text."""
    result = DiscordManager.split_text_on_word_boundaries("")
    assert result == []

def test_split_text_small():
    """Test splitting text smaller than limit."""
    text = "Hello, world!"
    result = DiscordManager.split_text_on_word_boundaries(text)
    assert result == [text]

def test_split_text_on_word_boundaries():
    """Test splitting text on word boundaries."""
    text = "a " * 1001  # Will exceed 2000 characters
    result = DiscordManager.split_text_on_word_boundaries(text)
    assert len(result) > 1
    assert all(len(chunk) <= 2000 for chunk in result)
    # Check that we split on spaces
    assert all(not chunk.endswith(" ") for chunk in result[:-1])

@pytest.mark.asyncio
async def test_send_message(discord_manager):
    """Test sending messages to Discord."""
    channel_id = 123456789
    message = "Test message"
    
    # Mock the channel and client
    mock_channel = MagicMock()
    discord_manager.client.fetch_channel = MagicMock(return_value=mock_channel)
    
    # Send message
    await discord_manager.send_message(message, channel_id)
    
    # Verify calls
    discord_manager.client.fetch_channel.assert_called_once_with(channel_id)
    mock_channel.send.assert_called_once_with(message)

@pytest.mark.asyncio
async def test_send_long_message(discord_manager):
    """Test sending a message that exceeds Discord's length limit."""
    channel_id = 123456789
    message = "a " * 1001  # Will exceed 2000 characters
    
    # Mock the channel and client
    mock_channel = MagicMock()
    discord_manager.client.fetch_channel = MagicMock(return_value=mock_channel)
    
    # Send message
    await discord_manager.send_message(message, channel_id)
    
    # Verify multiple sends occurred
    assert mock_channel.send.call_count > 1
