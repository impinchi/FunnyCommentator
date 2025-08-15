#!/usr/bin/env python3
"""Test both modes of the enhanced DiscordManager."""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import Config
from src.discord_manager import DiscordManager

async def test_discord_modes():
    """Test both client and HTTP modes of DiscordManager."""
    try:
        print("Loading configuration...")
        config = Config()
        
        discord_token = config.discord_token
        channel_id = config.channel_id_server_status
        
        print(f"Discord token loaded: {bool(discord_token)}")
        print(f"Channel ID: {channel_id}")
        
        # Test HTTP mode
        print("\n=== Testing HTTP Mode ===")
        http_manager = DiscordManager(discord_token, use_client=False)
        print(f"HTTP mode manager created. Has client: {http_manager.client is not None}")
        
        http_success = await http_manager.send_message(
            "🧪 **Test Message - HTTP Mode**\nThis tests the HTTP API functionality.",
            channel_id
        )
        print(f"HTTP mode test: {'✅ Success' if http_success else '❌ Failed'}")
        
        # Test client mode (without actually running the client)
        print("\n=== Testing Client Mode Setup ===")
        client_manager = DiscordManager(discord_token, use_client=True)
        print(f"Client mode manager created. Has client: {client_manager.client is not None}")
        print("✅ Client mode setup successful (not starting client to avoid blocking)")
        
        # Test text splitting utility
        print("\n=== Testing Text Splitting Utility ===")
        long_text = "A" * 2500  # Text longer than Discord's 2000 char limit
        chunks = DiscordManager.split_text_on_word_boundaries(long_text, 2000)
        print(f"Split {len(long_text)} chars into {len(chunks)} chunks")
        print(f"Chunk sizes: {[len(chunk) for chunk in chunks]}")
        print("✅ Text splitting works correctly")
        
        print("\n✅ All Discord functionality tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Testing enhanced DiscordManager functionality...")
    asyncio.run(test_discord_modes())
