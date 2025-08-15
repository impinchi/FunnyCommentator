"""IP Monitor Manager module.

This module handles IP monitoring operations including checks, configuration,
Discord notifications, and history tracking.
Following PEP 257 for docstring conventions.
"""
import os
import asyncio
import logging
import requests
from typing import Optional, Dict, List
from datetime import datetime
import json


class IPMonitorManager:
    """Manager for IP monitoring operations and configuration."""
    
    def __init__(self, config_manager, database_manager, discord_manager):
        """Initialize IP Monitor Manager.
        
        Args:
            config_manager: Configuration manager instance (can be Config object or dict)
            database_manager: Database manager instance
            discord_manager: Discord manager instance
        """
        self.config_manager = config_manager
        self.database = database_manager
        self.discord = discord_manager
        self.logger = logging.getLogger(__name__)
    
    def get_config(self) -> Dict:
        """Get configuration as dictionary.
        
        Returns:
            Configuration dictionary
        """
        if hasattr(self.config_manager, 'discord_token'):
            # Web app Config object with direct attributes - build dict representation
            config_dict = {
                "discord": {
                    "token": getattr(self.config_manager, 'discord_token', ''),
                    "channel_id_server_status": getattr(self.config_manager, 'channel_id_server_status', 0)
                },
                "database": {
                    "path": getattr(self.config_manager, 'db_path', 'arkbot_memory.db')
                },
                "ip_monitor": {
                    "check_interval_seconds": getattr(self.config_manager, 'ip_retry_seconds', 1800),
                    "last_known_ip": getattr(self.config_manager, 'previous_ip', None),
                    "discord_notifications": True,  # Default value
                    "history_retention_days": 30    # Default value
                }
            }
            return config_dict
        elif hasattr(self.config_manager, 'config'):
            # Main app Config object with a config attribute
            return self.config_manager.config
        elif hasattr(self.config_manager, '_get_config_path'):
            # If it's a web app config manager, load JSON directly
            import json
            config_path = self.config_manager._get_config_path()
            with open(config_path, 'r') as f:
                return json.load(f)
        elif isinstance(self.config_manager, dict):
            # If it's already a dictionary
            return self.config_manager
        else:
            # Fallback: try to load from config.json directly
            try:
                config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.json')
                with open(config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load config: {e}")
                return {}
    
    def save_config(self, config_data: Dict) -> None:
        """Save configuration to file.
        
        Args:
            config_data: Configuration dictionary to save
        """
        try:
            if hasattr(self.config_manager, '_get_config_path'):
                # If it's a web app config manager
                config_path = self.config_manager._get_config_path()
            else:
                # Default path
                config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.json')
            
            with open(config_path, 'w') as f:
                json.dump(config_data, f, indent=4)
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
            raise
    
    async def check_current_ip(self) -> Optional[str]:
        """Get current external IP address.
        
        Returns:
            Current IP address if successful, None otherwise
        """
        try:
            # Try multiple IP services for reliability
            services = [
                "https://api.ipify.org?format=json",
                "https://httpbin.org/ip",
                "https://jsonip.com"
            ]
            
            for service in services:
                try:
                    response = requests.get(service, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        # Handle different response formats
                        if 'ip' in data:
                            return data['ip']
                        elif 'origin' in data:
                            return data['origin']
                        elif 'ip' in str(data):
                            return str(data).split('"')[3]  # Simple parsing for jsonip
                except Exception as e:
                    self.logger.warning(f"Failed to get IP from {service}: {e}")
                    continue
            
            self.logger.error("All IP services failed")
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking current IP: {e}")
            return None
    
    def get_last_known_ip(self) -> Optional[str]:
        """Get last known IP from configuration.
        
        Returns:
            Last known IP address from config
        """
        try:
            config = self.get_config()
            return config.get('ip_monitor', {}).get('last_known_ip')
        except Exception as e:
            self.logger.error(f"Error getting last known IP: {e}")
            return None
    
    def update_last_known_ip(self, new_ip: str, change_type: str = 'manual') -> bool:
        """Update last known IP in configuration and log change.
        
        Args:
            new_ip: New IP address to store
            change_type: Type of change ('auto', 'manual', 'startup')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            old_ip = self.get_last_known_ip()
            
            # Update configuration
            config = self.get_config()
            if 'ip_monitor' not in config:
                config['ip_monitor'] = {}
            
            config['ip_monitor']['last_known_ip'] = new_ip
            self.save_config(config)
            
            # Log the change in database
            if old_ip and old_ip != new_ip:
                self.database.log_ip_change(old_ip, new_ip, change_type)
                self.logger.info(f"IP changed from {old_ip} to {new_ip} ({change_type})")
                return True
            elif not old_ip:
                # First time setting IP
                self.database.log_ip_change('', new_ip, 'startup')
                self.logger.info(f"Initial IP set to {new_ip}")
                return True
            
            return False  # No change
            
        except Exception as e:
            self.logger.error(f"Error updating last known IP: {e}")
            return False
    
    async def notify_discord_ip_change(self, old_ip: str, new_ip: str) -> bool:
        """Send Discord notification about IP change.
        
        Args:
            old_ip: Previous IP address
            new_ip: New IP address
            
        Returns:
            True if notification sent successfully
        """
        try:
            # Check if Discord notifications are enabled
            monitor_config = self.get_monitor_config()
            if not monitor_config.get('discord_notifications', True):
                self.logger.info("Discord notifications disabled, skipping")
                return True
            
            config = self.get_config()
            channel_id = config.get('discord', {}).get('channel_id_server_status')
            discord_token = config.get('discord', {}).get('token')
            
            if not channel_id or not discord_token:
                self.logger.warning("No Discord channel or token configured for server status")
                return False
            
            # Create Discord embed message
            embed = {
                "title": "🌐 External IP Address Changed",
                "color": 0x00ff41,  # ARK green
                "fields": [
                    {
                        "name": "Previous IP",
                        "value": f"`{old_ip or 'Unknown'}`",
                        "inline": True
                    },
                    {
                        "name": "New IP", 
                        "value": f"`{new_ip}`",
                        "inline": True
                    },
                    {
                        "name": "Detected At",
                        "value": f"<t:{int(datetime.now().timestamp())}:F>",
                        "inline": False
                    }
                ],
                "footer": {
                    "text": "ARK FunnyCommentator IP Monitor"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            message = f"🔄 **IP Address Update**\nExternal IP has changed from `{old_ip}` to `{new_ip}`"
            
            # Use enhanced DiscordManager HTTP mode instead of Discord client
            from .discord_manager import DiscordManager
            discord_manager = DiscordManager(discord_token, use_client=False)
            success = await discord_manager.send_message(
                content=message,
                channel_id=channel_id,
                embed=embed
            )
            
            if success:
                self.logger.info(f"Discord notification sent for IP change: {old_ip} → {new_ip}")
            else:
                self.logger.error("Failed to send Discord notification for IP change")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending Discord IP change notification: {e}")
            return False
    
    def get_monitor_config(self) -> Dict:
        """Get current IP monitor configuration.
        
        Returns:
            Dictionary containing IP monitor configuration
        """
        try:
            config = self.get_config()
            ip_config = config.get('ip_monitor', {})
            
            return {
                'last_known_ip': ip_config.get('last_known_ip'),
                'check_interval_seconds': ip_config.get('check_interval_seconds', 3600),
                'discord_notifications': ip_config.get('discord_notifications', True),
                'auto_monitoring': ip_config.get('auto_monitoring', True)
            }
        except Exception as e:
            self.logger.error(f"Error getting monitor config: {e}")
            return {}
    
    def update_monitor_config(self, new_config: Dict) -> bool:
        """Update IP monitor configuration.
        
        Args:
            new_config: Dictionary with new configuration values
            
        Returns:
            True if successful, False otherwise
        """
        try:
            config = self.get_config()
            
            if 'ip_monitor' not in config:
                config['ip_monitor'] = {}
            
            # Update allowed configuration fields
            allowed_fields = [
                'check_interval_seconds', 
                'discord_notifications', 
                'auto_monitoring'
            ]
            
            for field in allowed_fields:
                if field in new_config:
                    config['ip_monitor'][field] = new_config[field]
            
            self.save_config(config)
            self.logger.info(f"IP monitor configuration updated: {new_config}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating monitor config: {e}")
            return False
    
    def get_ip_history(self, limit: int = 50) -> List[Dict]:
        """Get IP change history from database.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of IP history records
        """
        try:
            return self.database.get_ip_history(limit)
        except Exception as e:
            self.logger.error(f"Error getting IP history: {e}")
            return []
    
    async def perform_ip_check_and_notify(self) -> Dict:
        """Perform full IP check, update config, and notify if changed.
        
        Returns:
            Dictionary with check results
        """
        try:
            current_ip = await self.check_current_ip()
            if not current_ip:
                return {
                    'success': False,
                    'error': 'Failed to determine current IP address',
                    'current_ip': None,
                    'changed': False
                }
            
            last_known = self.get_last_known_ip()
            changed = False
            
            if current_ip != last_known:
                # IP has changed
                changed = self.update_last_known_ip(current_ip, 'auto')
                
                if changed:
                    # Send Discord notification if enabled
                    config = self.get_monitor_config()
                    if config.get('discord_notifications', True):
                        await self.notify_discord_ip_change(last_known, current_ip)
            
            return {
                'success': True,
                'current_ip': current_ip,
                'last_known_ip': last_known,
                'changed': changed,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error performing IP check: {e}")
            return {
                'success': False,
                'error': str(e),
                'current_ip': None,
                'changed': False
            }
