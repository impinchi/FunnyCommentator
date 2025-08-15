#!/usr/bin/env python3
"""Test Discord HTTP functionality."""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import Config
from src.discord_manager import DiscordManager

async def test_discord():
    """Test Discord HTTP API."""
    try:
        print("Loading configuration...")
        config = Config()
        
        discord_token = config.discord_token
        channel_id = config.channel_id_server_status
        
        print(f"Discord token loaded: {bool(discord_token)}")
        print(f"Channel ID: {channel_id}")
        
        # Test embed
        embed = {
            "title": "🧪 Test IP Monitor Notification",
            "color": 0x00ff41,
            "fields": [
                {
                    "name": "Previous IP",
                    "value": "`10.0.0.100`",
                    "inline": True
                },
                {
                    "name": "New IP",
                    "value": "`102.182.213.185`",
                    "inline": True
                }
            ],
            "footer": {
                "text": "ARK FunnyCommentator IP Monitor Test"
            }
        }
        
        content = "🔄 **TEST IP Change Notification**\nThis is a test of the IP monitoring Discord integration."
        
        print("Sending Discord test message...")
        discord_manager = DiscordManager(discord_token, use_client=False)
        success = await discord_manager.send_message(content, channel_id, embed)
        
        if success:
            print("✅ Discord message sent successfully!")
            print(f"Check your Discord channel #{channel_id} for the message.")
        else:
            print("❌ Failed to send Discord message.")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Testing Discord HTTP API...")
    asyncio.run(test_discord())
