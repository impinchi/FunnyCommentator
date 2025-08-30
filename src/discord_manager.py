"""Discord client module.

This module handles all Discord-related operations including message sending
and client setup. Following PEP 257 for docstring conventions.
"""
import asyncio
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
        """Split text into chunks that respect Discord's message length limit and preserve formatting.
        
        Args:
            text: Text to split
            max_length: Maximum length of each chunk
        
        Returns:
            List of text chunks
        """
        if len(text) <= max_length:
            return [text]
            
        chunks = []
        remaining_text = text
        
        while len(remaining_text) > max_length:
            # Try to find a good split point
            split_at = max_length
            
            # Look for natural break points in order of preference
            break_points = [
                ('\n\n', -2),  # Paragraph breaks
                ('\n', -1),    # Line breaks
                ('. ', 0),     # Sentence endings
                ('! ', 0),     # Exclamation endings
                ('? ', 0),     # Question endings
                (', ', 0),     # Comma breaks
                (' ', 0),      # Word boundaries
            ]
            
            for delimiter, offset in break_points:
                pos = remaining_text.rfind(delimiter, 0, max_length)
                if pos != -1:
                    split_at = pos + len(delimiter) + offset
                    break
            
            # Extract the chunk
            chunk = remaining_text[:split_at].strip()
            if chunk:
                chunks.append(chunk)
                
            # Prepare remaining text
            remaining_text = remaining_text[split_at:].lstrip()
            
            # Safety check to prevent infinite loop
            if not remaining_text or len(remaining_text) == len(text):
                break
                
        # Add the final chunk if there's remaining text
        if remaining_text.strip():
            chunks.append(remaining_text.strip())
            
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
        
        # Log headers with masked token for security
        masked_headers = {
            "Authorization": f"Bot {self.token[:20]}...{self.token[-5:]}",
            "Content-Type": "application/json"
        }
        logging.debug(f"Discord API headers: {masked_headers}")
        
        # Split long messages into chunks
        chunks = self.split_text_on_word_boundaries(content, 2000)
        
        logging.info(f"Preparing to send {len(chunks)} Discord message chunk(s) via HTTP to channel {channel_id}")
        logging.debug(f"Total content length: {len(content)} chars, Split into chunks: {[len(chunk) for chunk in chunks]}")
        
        try:
            async with aiohttp.ClientSession() as session:
                success_count = 0
                
                for i, chunk in enumerate(chunks):
                    payload = {"content": chunk}
                    
                    # Only add embed to the first message
                    if i == 0 and embed:
                        payload["embeds"] = [embed]
                        logging.debug(f"Adding embed to first chunk: {embed.get('title', 'No title') if embed else 'None'}")
                    
                    logging.debug(f"Sending chunk {i+1}/{len(chunks)}: {len(chunk)} chars")
                    logging.debug(f"Chunk content preview: {chunk[:100]}{'...' if len(chunk) > 100 else ''}")
                    
                    async with session.post(url, json=payload, headers=headers) as response:
                        response_text = await response.text()
                        
                        if response.status == 200:
                            success_count += 1
                            logging.info(f"Successfully sent Discord chunk {i+1}/{len(chunks)} to channel {channel_id}")
                        else:
                            logging.error(f"Discord API error for chunk {i+1}: {response.status} - {response_text}")
                            return False
                    
                    # Rate limiting: small delay between chunks
                    if i < len(chunks) - 1:  # Don't delay after the last chunk
                        await asyncio.sleep(0.5)
                
                if success_count == len(chunks):
                    logging.info(f"Successfully sent all {len(chunks)} chunks to channel {channel_id}")
                    return True
                else:
                    logging.error(f"Only {success_count}/{len(chunks)} chunks sent successfully")
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
        logging.info(f"Discord send_message called - Channel: {channel_id}, Content length: {len(content)} chars")
        logging.debug(f"Content preview: {content[:200]}{'...' if len(content) > 200 else ''}")
        
        # If no client is available or we're in HTTP mode, use HTTP API
        if not self.use_client or not self.client:
            logging.debug("Using HTTP API mode for Discord message")
            # Convert Discord embed object to dict if needed
            embed_dict = None
            if embed:
                if isinstance(embed, discord.Embed):
                    logging.debug("Converting Discord Embed object to dict for HTTP API")
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
