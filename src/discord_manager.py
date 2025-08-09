"""Discord client module.

This module handles all Discord-related operations including message sending
and client setup. Following PEP 257 for docstring conventions.
"""
import logging
from typing import List
import discord
from discord.ext import tasks

class DiscordManager:
    """Discord client manager for handling Discord operations."""
    
    def __init__(self, token: str):
        """Initialize Discord manager with bot token.
        
        Args:
            token: Discord bot token
        """
        intents = discord.Intents.default()
        intents.messages = True
        self.client = discord.Client(intents=intents)
        self.token = token
    
    @staticmethod
    def split_text_on_word_boundaries(text: str, max_length: int = 2000) -> List[str]:
        """Split text into chunks that respect Discord's message length limit.
        
        Args:
            text: Text to split
            max_length: Maximum length of each chunk
        
        Returns:
            List of text chunks
        """
        chunks = []
        while len(text) > max_length:
            # Find the last space within the limit
            split_at = text.rfind(' ', 0, max_length)
            if split_at == -1:
                # No space found, force split at max_length
                split_at = max_length
            chunks.append(text[:split_at])
            # Remove only a single leading space if present
            if text[split_at:split_at+1] == ' ':
                text = text[split_at+1:]
            else:
                text = text[split_at:]
        if text:
            chunks.append(text)
        return chunks
    
    async def send_message(self, content: str, channel_id: int) -> None:
        """Send a message to a Discord channel, splitting if necessary.
        
        Args:
            content: The message content to send
            channel_id: The ID of the channel to send to
        """
        try:
            channel = await self.client.fetch_channel(channel_id)
            for chunk in self.split_text_on_word_boundaries(content):
                await channel.send(chunk)
            logging.info(f"Sent message to Discord channel {channel_id}.")
        except Exception as e:
            logging.error(f"Discord send error: {e}")
    
    def run(self):
        """Start the Discord client."""
        self.client.run(self.token)
