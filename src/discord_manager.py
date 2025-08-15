"""Discord client module.

This module handles all Discord-related operations including message sending
and client setup. Following PEP 257 for docstring conventions.
"""
import logging
from typing import List, Dict, Optional
import discord
from discord.ext import tasks
import aiohttp

class DiscordManager:
    """Discord client manager for handling Discord operations."""
    
    def __init__(self, token: str, use_client: bool = True):
        """Initialize Discord manager with bot token.
        
        Args:
            token: Discord bot token
            use_client: If True, creates persistent client; if False, uses HTTP API only
        """
        self.token = token
        self.use_client = use_client
        
        if use_client:
            intents = discord.Intents.default()
            intents.messages = True
            self.client = discord.Client(intents=intents)
        else:
            self.client = None
    
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
    
    async def send_message_http(self, content: str, channel_id: int, embed: Optional[Dict] = None) -> bool:
        """Send a Discord message using HTTP API (no persistent connection).
        
        Args:
            content: Message content
            channel_id: Target channel ID
            embed: Optional embed data as dictionary
            
        Returns:
            True if successful, False otherwise
        """
        url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
        headers = {
            "Authorization": f"Bot {self.token}",
            "Content-Type": "application/json"
        }
        
        payload = {"content": content}
        if embed:
            payload["embeds"] = [embed]
        
        logging.info(f"Sending Discord message via HTTP to channel {channel_id}")
        logging.debug(f"Payload: {payload}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    response_text = await response.text()
                    logging.debug(f"Discord API response {response.status}: {response_text}")
                    
                    if response.status == 200:
                        logging.info(f"Successfully sent Discord message to channel {channel_id}")
                        return True
                    else:
                        logging.error(f"Discord API error {response.status}: {response_text}")
                        return False
        except Exception as e:
            logging.error(f"Error sending Discord message via HTTP: {e}")
            return False
    
    async def send_message(self, content: str, channel_id: int, embed=None) -> bool:
        """Send a message to a Discord channel, using client or HTTP based on configuration.
        
        Args:
            content: The message content to send
            channel_id: The ID of the channel to send to
            embed: Optional Discord embed object or dict
            
        Returns:
            True if successful, False otherwise
        """
        # If no client is available or we're in HTTP mode, use HTTP API
        if not self.use_client or not self.client:
            # Convert Discord embed object to dict if needed
            embed_dict = None
            if embed:
                if isinstance(embed, discord.Embed):
                    # Convert Discord Embed to dict format for HTTP API
                    embed_dict = {
                        "title": embed.title or "",
                        "color": embed.color.value if embed.color else 0x00ff41,
                        "fields": [
                            {
                                "name": field.name,
                                "value": field.value,
                                "inline": field.inline
                            } for field in embed.fields
                        ],
                        "footer": {"text": embed.footer.text} if embed.footer else None,
                        "timestamp": embed.timestamp.isoformat() if embed.timestamp else None
                    }
                elif isinstance(embed, dict):
                    embed_dict = embed
            
            return await self.send_message_http(content, channel_id, embed_dict)
        
        # Use client-based approach (original implementation)
        try:
            channel = await self.client.fetch_channel(channel_id)
            
            if embed:
                # Convert dict embed to Discord Embed object if needed
                if isinstance(embed, dict):
                    discord_embed = discord.Embed(
                        title=embed.get('title', ''),
                        color=embed.get('color', 0x00ff41),
                        timestamp=discord.utils.utcnow() if embed.get('timestamp') else None
                    )
                    
                    # Add fields
                    for field in embed.get('fields', []):
                        discord_embed.add_field(
                            name=field.get('name', ''),
                            value=field.get('value', ''),
                            inline=field.get('inline', True)
                        )
                    
                    # Add footer
                    if 'footer' in embed:
                        discord_embed.set_footer(text=embed['footer'].get('text', ''))
                    
                    embed = discord_embed
                
                await channel.send(content=content, embed=embed)
            else:
                # Send as regular message, splitting if necessary
                for chunk in self.split_text_on_word_boundaries(content):
                    await channel.send(chunk)
                    
            logging.info(f"Sent message to Discord channel {channel_id} via client.")
            return True
            
        except Exception as e:
            logging.error(f"Discord send error (client mode): {e}")
            return False
    
    def run(self):
        """Start the Discord client (only available in client mode)."""
        if not self.use_client or not self.client:
            raise RuntimeError("Cannot run Discord client in HTTP-only mode. Use send_message() for HTTP API calls.")
        self.client.run(self.token)
